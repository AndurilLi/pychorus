'''
Created on Feb 23, 2014

@author: redesigned by Anduril 
@target: Generate result by read unittest result, and assert baselines
'''
import os, json
import ChorusGlobals
import Utils
from MyTestCase import LEVELS, TYPES, LOGIC
from PIL import Image
from ImageCom import FuzzyImageCompare, metrictype
from ChorusConstants import ResultStatus, SuiteResult, CaseResult, AssertionResult
import traceback
class VerificationManagement:
    
    def __init__(self):
        self.suite_dict = ChorusGlobals.get_suitedict()
        self.logger = ChorusGlobals.get_logger()
        self.configinfo = ChorusGlobals.get_configinfo()
        self.baseline_path = ChorusGlobals.get_baselinepath()
        self.outputdir = ChorusGlobals.get_outputdir()
        self.result = ChorusGlobals.get_testresult()
        self.known_issue_list = ChorusGlobals.get_knownissuelist()
        
    def check_allbaselines(self):
        self.baseline_dict = {}
        for suite_name, case_list in self.suite_dict.iteritems():
            suite_result = SuiteResult(suite_name)
            path = Utils.create_entity(self.baseline_path)
            path.append(suite_name)
            filename = '%s.base' % suite_name
            file_fullname = Utils.get_filestr(path,filename)
            baseline_cases = {}
            if not os.path.isfile(file_fullname):
                self.logger.debug("Baseline for test suite '%s' doesn't exist!" % suite_name)
            else:
                try:
                    baseline_cases = Utils.get_json_from_file(path, filename)
                except Exception,e:
                    traceback.print_exc()
                    self.logger.critical("Open file %s error or Json type not correct %s" % (filename,str(e)))
                    raise Exception("Open file %s error or Json type not correct %s" % (filename,str(e)))
            for case_name in case_list:
                case_result = CaseResult(case_name)
                if case_name not in baseline_cases:
                    self.logger.debug("Baseline for test case '%s' doesn't exist!" % case_name)
                else:
                    for assertion_name in baseline_cases[case_name]:
                        assertion_result = AssertionResult(assertion_name)
                        assertion_result.baseline = baseline_cases[case_name][assertion_name]
                        assertion_result.baseline_status = True
                        case_result.assertions[assertion_name] = assertion_result
                suite_result.cases[case_name] = case_result
            suite_result.baseline_dict = baseline_cases
            self.result.suites[suite_name] = suite_result
        
        self.logger.info("Verifing all baselines finished")
            
    def check_suitebaseline(self,suite_name):
        base_path = Utils.create_entity(self.baseline_path)
        base_path.append(suite_name)
        self.suite_baseline_path = base_path
        output_path = list(os.path.split(Utils.create_entity(self.outputdir)))
        if output_path[0]=="":
            output_path.remove("")
        output_path.append(suite_name)
        self.suite_output_path = output_path
        self.suite_name = suite_name
        return self.result.suites[suite_name]
    
    def generate_baseline(self,result):
        baseline_dict = Utils.create_entity(result.baseline_dict)
        current_dict = Utils.create_entity(result.baseline_dict)
        for case_name, case_result in result.cases.items():
            if not baseline_dict.has_key(case_name):
                baseline_dict[case_name]={}
            current_dict[case_name] = {}
            for assertion_name, assertion_result in case_result.assertions.items():
                if not assertion_result.onfly_flag:
                    current_dict[case_name][assertion_name] = assertion_result.current
                    if not assertion_result.baseline_status:
                        baseline_dict[case_name][assertion_name] = assertion_result.current
                        if assertion_result.cptype == "Image":
                            content = assertion_result.current
                            src_image_filename = Utils.get_filestr(self.suite_output_path, content["image_name"]+"."+content["image_type"])
                            dst_image_filename = Utils.get_filestr(self.suite_baseline_path, content["image_name"]+"."+content["image_type"])
                            try:
                                Utils.copy_to_file(src_image_filename, dst_image_filename)
                            except Exception, e:
                                self.logger.warning("Copy image file %s to %s failed with error %s" % (src_image_filename, dst_image_filename, str(e)))
                                del baseline_dict[case_name][assertion_name]
        base_filename = '%s.base' % result.name
        Utils.dump_dict_to_file(current_dict, self.suite_output_path, base_filename)
        if not result.baseline_status:
            Utils.dump_dict_to_file(baseline_dict, self.suite_baseline_path, base_filename)
    
    def checkpoint_onfly(self, tsobj, assertion_name, content, level, cptype, logic):
        suite_name = tsobj.suite_name
        case_name = tsobj._testMethodName
        case_result = self.result.suites[suite_name].cases[case_name]
        if not case_result.assertions.has_key(assertion_name):
            case_result.assertions[assertion_name] = AssertionResult(assertion_name)
        assertion_result = case_result.assertions[assertion_name]
        assertion_result.getsettings(content, level, cptype, logic, json.dumps(content))
    
    def checkpoint(self, tsobj, assertion_name, content, level, cptype, logic):
        suite_name = tsobj.suite_name
        case_name = tsobj._testMethodName
        case_result = self.result.suites[suite_name].cases[case_name]
        if not case_result.assertions.has_key(assertion_name):
            case_result.assertions[assertion_name] = AssertionResult(assertion_name)
        assertion_result = case_result.assertions[assertion_name]
        assertion_result.path = case_name + "/" + assertion_name
        assertion_result.getsettings(content, level, cptype, logic, json.dumps(content))
        if assertion_result.baseline_status:
            self.compare_checkpoint(tsobj, assertion_result)
        else:
            self.generate_checkpoint(tsobj, assertion_result)
            case_result.baseline_status = False
            self.result.suites[suite_name].baseline_status = False
            self.result.baseline_status = False
        if assertion_result.status == ResultStatus.FAILED:
            try:
                assertion_result.comments = self.known_issue_list[suite_name][case_name][assertion_name]
                assertion_result.status = ResultStatus.KNOWN_ISSUES
                self.result.knownflag = True
                case_result.passed_assertions += 1
                if case_result.status == ResultStatus.PASSED:
                    case_result.status = ResultStatus.KNOWN_ISSUES
                    if self.result.suites[suite_name].status == ResultStatus.PASSED:
                        self.result.suites[suite_name].status = ResultStatus.KNOWN_ISSUES
                        if self.result.status == ResultStatus.PASSED:
                            self.result.status = ResultStatus.KNOWN_ISSUES
                self.logger.warning("Assertion '%s' passed with known issues" % assertion_name)
            except Exception:
                assertion_result.statusflag = False
                case_result.statusflag = False
                case_result.status = ResultStatus.FAILED
                case_result.failed_assertions += 1
                if self.result.suites[suite_name].status!= ResultStatus.CRASHED:
                    self.result.suites[suite_name].status = ResultStatus.FAILED
                    self.result.suites[suite_name].statusflag = False
                    self.result.status = ResultStatus.FAILED
                    self.result.statusflag = False
                if level == LEVELS.Critical:
                    self.logger.error("Assertion '%s' failed. Fail the test case!" % assertion_name)
                    tsobj.fail("Assertion '%s' failed. Fail the test case!" % assertion_name)
                else:
                    self.logger.warning("Assertion '%s' failed." % assertion_name)
        else:
            case_result.passed_assertions += 1
            if assertion_result.baseline_status:
                self.logger.info("Assertion '%s' passed" % assertion_name)
            else:
                self.logger.info("Assertion '%s' baseline generated" % assertion_name)
    
    def generate_checkpoint(self, tsobj, assertion_result):
        if assertion_result.cptype == TYPES.Image:
            content = assertion_result.current
            image_filename = content["image_name"]+"."+content["image_type"]
            thumb_filename = content["image_name"]+"_thumbnail"+"."+content["image_type"]
            image_filepath = Utils.get_filestr(self.suite_output_path, image_filename)
            thumb_filepath = Utils.get_filestr(self.suite_output_path, thumb_filename)
            im_base=Image.open(image_filepath).convert('RGBA')
            assertion_result.similarity = 100
            self.make_thumbfile(im_base, thumb_filepath)
            assertion_result.detail = {
                                        "basethumb": os.path.join(self.suite_name, thumb_filename),
                                        "basevalue": os.path.join(self.suite_name, image_filename),
                                        "realthumb": os.path.join(self.suite_name, thumb_filename),
                                        "realvalue": os.path.join(self.suite_name, image_filename)
                                       }
        else:
            assertion_result.detail["basevalue"] = assertion_result.detail["realvalue"]
    
    def compare_checkpoint(self, tsobj, assertion_result): 
        if assertion_result.cptype == TYPES.Image:
            base_imagefile1 = assertion_result.current["image_name"]+"."+assertion_result.current["image_type"]
            base_imagefile2 = assertion_result.current["image_name"]+"_base"+"."+assertion_result.current["image_type"]
            src_imagefile = Utils.get_filestr(self.suite_baseline_path, base_imagefile1)
            dst_imagefile = Utils.get_filestr(self.suite_output_path, base_imagefile2)
            Utils.copy_to_file(src_imagefile, dst_imagefile)
            self.image_compare(assertion_result)
        elif assertion_result.logic != LOGIC.Equal:
            self.special_compare(assertion_result)
        else:
            self.data_compare(assertion_result)
    
    def image_compare(self,assertion_result):
        content = assertion_result.current
        base_filename = Utils.get_filestr(self.suite_output_path,content["image_name"]+"_base"+"."+content["image_type"])
        base_thumbfilename = Utils.get_filestr(self.suite_output_path,content["image_name"]+"_base"+"_thumbnail"+"."+content["image_type"])
        real_filename = Utils.get_filestr(self.suite_output_path,content["image_name"]+"."+content["image_type"])
        real_thumbfilename = Utils.get_filestr(self.suite_output_path,content["image_name"]+"_thumbnail"+"."+content["image_type"])
        im_base=Image.open(base_filename).convert('RGBA')
        im_real=Image.open(real_filename).convert('RGBA')
        imgcmp = FuzzyImageCompare(im_base,im_real)
        assertion_result.similarity = imgcmp.similarity()
        self.make_thumbfile(im_base, base_thumbfilename)
        self.make_thumbfile(im_real, real_thumbfilename)
        assertion_result.detail = {
                                    "basethumb": os.path.join(self.suite_name, content["image_name"]+"_base"+"_thumbnail"+"."+content["image_type"]),
                                    "basevalue": os.path.join(self.suite_name, content["image_name"]+"_base"+"."+content["image_type"]),
                                    "realthumb": os.path.join(self.suite_name, content["image_name"]+"_thumbnail"+"."+content["image_type"]),
                                    "realvalue": os.path.join(self.suite_name, content["image_name"]+"."+content["image_type"])
                                   }
        if assertion_result.similarity < assertion_result.logic:
            assertion_result.status = ResultStatus.FAILED
            diff_file = content["image_name"]+"_diff"+"."+content["image_type"]
            imgcmp.GetDiff(Utils.get_filestr(self.suite_output_path),diff_file,metrictype.PSNR)
            diff_filename = Utils.get_filestr(self.suite_output_path,diff_file)
            im_diff = Image.open(diff_filename)
            diff_thumbfilename = Utils.get_filestr(self.suite_output_path,content["image_name"]+"_diff"+"_thumbnail"+"."+content["image_type"])
            self.make_thumbfile(im_diff, diff_thumbfilename)
            assertion_result.detail["diffthumb"] = os.path.join(self.suite_name, content["image_name"]+"_diff"+"_thumbnail"+"."+content["image_type"])
            assertion_result.detail["diffvalue"] = os.path.join(self.suite_name, content["image_name"]+"_diff"+"."+content["image_type"])
    
    def special_compare(self, assertion_result):
        if assertion_result.logic == 'UnEqual' and assertion_result.baseline == assertion_result.current:
            assertion_result.status = ResultStatus.FAILED
        elif assertion_result.logic == 'In' and assertion_result.baseline.find(assertion_result.current)==-1:
            assertion_result.status = ResultStatus.FAILED
        elif assertion_result.logic == 'NotIn' and assertion_result.baseline.find(assertion_result.current)>=0:
            assertion_result.status = ResultStatus.FAILED
    
    def data_compare(self,assertion_result):
        assertion_result.detail["basevalue"] = json.dumps(assertion_result.baseline)
        if not Utils.simple_compare(assertion_result.baseline,assertion_result.current):
            assertion_result.status = ResultStatus.FAILED
        
    def save_image(self, tsobj, name, imagedata, imagetype):
        try:
            filename = Utils.get_filestr(self.suite_output_path,tsobj._testMethodName + "_"+ name+"."+imagetype)
            Utils.write_to_file(filename, imagedata)
        except Exception, e:
            traceback.print_exc()
            self.logger.error("Cannot save image with error %s" % str(e))
            raise Exception("Cannot save image with error %s" % str(e))
    
    def save_screenshot(self, tsobj, name, driver, elements, coordinates, imagetype = ".png"):
        try:
            filename = Utils.get_filestr(self.suite_output_path,tsobj._testMethodName + "_"+ name+"."+imagetype)
            '''make sure the driver has related functions'''
            if elements or coordinates:
                driver.get_screenshot_without_items(filename, elements, coordinates)
            else:
                driver.get_screenshot_as_file(filename)
        except Exception, e:
            traceback.print_exc()
            self.logger.error("Cannot save image with error %s" % str(e))
            raise Exception("Cannot save image with error %s" % str(e))
    
    def save_elementshot(self, tsobj, name, driver, target, exclusion, iframe_loc, imagetype = ".png"):
        try:
            filename = Utils.get_filestr(self.suite_output_path,tsobj._testMethodName + "_"+ name+"."+imagetype)
            '''make sure the driver has related functions'''
            if target or exclusion:
                driver.get_elementshot_without_items(filename, target, exclusion, iframe_loc)
            else:
                driver.get_screenshot_as_file(filename)
        except Exception, e:
            traceback.print_exc()
            self.logger.error("Cannot save image with error %s" % str(e))
            raise Exception("Cannot save image with error %s" % str(e))
    
    def make_thumbfile(self, im, thumb_file):
        thumb_im = Utils.create_entity(im)
        size = 128, 128
        thumb_im.thumbnail(size, Image.ANTIALIAS)
        thumb_im.save(thumb_file)