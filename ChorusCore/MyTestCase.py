'''
Created on Feb 23, 2014

@author: Anduril
@target: to give a better shell of unittest in order to provide pretty HTML report
'''
import unittest,time
import Utils
import ChorusGlobals
from ChorusConstants import LEVELS, LOGIC, IMAGELOGIC, TYPES, ResultStatus, AssertionResult

class MyTestCase(unittest.TestCase):
    '''
    Inherit from python's unittest.TestCase
    override the setUp, setUpClass, tearDown, tearDownClass methold    
    '''
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)     
        if hasattr(getattr(self, methodName), '_scopes'):          
            self.scopes = getattr(self, methodName)._scopes
        else:
            self.scopes = ["all"]
        if hasattr(getattr(self, methodName), '_depends'):          
            self.depends = getattr(self, methodName)._depends
        else:
            self.depends = []
        self.executed_cases = []
    
    def init_assertions(self, name):
        assertions = self.result.cases[self._testMethodName].assertions
        if not assertions.has_key(name):
            assertions[name] = AssertionResult(name)
        return assertions[name]
    
    def assertBool(self, name, content, levels = LEVELS.Normal):
        if content is True:
            content = 'True'
        elif content is False:
            content = 'False'
        elif content != 'True' and content != 'False':
            content = 'False'
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Bool, logic = LOGIC.Equal)
    
    def assertData(self, name, content, levels = LEVELS.Normal):
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Data, logic = LOGIC.Equal)
    
    def assertDataOnFly(self, name, data1, data2, levels = LEVELS.Normal, cptype = TYPES.Data):
        assertion_result = self.init_assertions(name)
        assertion_result.onfly_flag = True
        assertion_result.baseline = data1
        assertion_result.baseline_status = True
        self.vm.checkpoint(self, name, data2, level = levels, cptype = cptype, logic = LOGIC.Equal)
    
    def assertHTTPResponse(self, name, response, levels = LEVELS.Normal, logic = LOGIC.Equal):
        assertion_result = self.init_assertions(name)
        assertion_result.detail = {
                                    "url":response.response.url,
                                    "api":response.jsdata
                                   }
        self.vm.checkpoint(self, name, response.result, level = levels, cptype = TYPES.HTTPResponse, logic = logic)

    def assertImageData(self, name, imagedata, levels = LEVELS.Normal, image_logic = IMAGELOGIC.Full, imagetype = "jpg"):
        self.vm.save_image(self, name, imagedata, imagetype)
        content = {
                    "image_name":self._testMethodName+"_"+name,
                    "image_type":imagetype
                   }
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Image, logic = image_logic)
    
    def assertScreenShot(self, name, driver, levels = LEVELS.Normal, image_logic = IMAGELOGIC.Full, imagetype = "png", elements = None, coordinates = None):
        #add by Peng, suggested by Yue, Approved by Lucinda
        #If the system is linux, and use javamonkey driver, will auto skip the assertion
        try:
            if driver.__class__.__name__ == "JavaMonkey":
                import sys
                if sys.platform.startswith("linux"):
                    self.logger.info("Assertion %s has been skipped due to JavaMonkey&Linux reason" % name)
                    return
        except:
            pass
        self.vm.save_screenshot(self, name, driver, elements, coordinates, imagetype)
        content = {
                    "image_name":self._testMethodName+"_"+name,
                    "image_type":imagetype
                   }
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Image, logic = image_logic)
    
    def assertElementShot(self, name, driver, target = None, exclusion = None, iframe_loc = None, levels = LEVELS.Normal, image_logic = IMAGELOGIC.Full, imagetype = "png"):
        self.vm.save_elementshot(self, name, driver, target, exclusion, iframe_loc, imagetype)
        content = {
                    "image_name":self._testMethodName+"_"+name,
                    "image_type":imagetype
                   }
        self.vm.checkpoint(self, name, content, level = levels, cptype = TYPES.Image, logic = image_logic)
    
    def assertText(self, name, content, levels = LEVELS.Normal, logic = LOGIC.Equal):
        self.vm.checkpoint(self, name, str(content), level = levels, cptype = TYPES.Text, logic = logic)
    
    def setUp(self):
        '''
        setUp is executed every time before run a test case
        you can do some initial work here
        '''
        self.startTime = time.time()
        #has dependency test case
        if len(self.depends) > 0:
            suites = ChorusGlobals.get_testresult().suites.values()
            mapping = {}
            for s in suites:
                cases = s.cases
                for key, value in cases.iteritems():
                    mapping[key] = value.statusflag
            for d in self.depends:
                if mapping.has_key(d) and not mapping[d]:
                    self.addCleanup(self.tearDown)
                    raise Exception("Has failed dependency test case %s" %(str(d)))
        unittest.TestCase.setUp(self)
    
    @classmethod
    def get_suite_dependency(cls):
        if hasattr(cls, "global_depends"):
            return getattr(cls, "global_depends")
        else:
            return []
        
    @classmethod
    def setUpClass(cls):        
        '''
        setUpClass is executed every time before run a test suite
        '''
        suite_dependency = cls.get_suite_dependency()
        if len(suite_dependency) > 0:
            suites = ChorusGlobals.get_testresult().suites
            mapping = {}
            for key, value in suites.iteritems():
                mapping[key] = value.statusflag
            for d in suite_dependency:
                if mapping.has_key(d) and not mapping[d]:
                    raise Exception("Has failed dependency test suite %s" %(str(d)))   
        cls.suite_starttime = time.time() 
        cls.logserver = ChorusGlobals.get_logserver()
        cls.logserver.flush_console()
        super(MyTestCase,cls).setUpClass()
        cls.logger = ChorusGlobals.get_logger()
        cls.suite_name = Utils.get_current_classname(cls)
        ChorusGlobals.set_current_suitename(cls.suite_name)
        from VerificationManagement import VerificationManagement
        cls.vm = VerificationManagement()
        cls.result = cls.vm.check_suitebaseline(cls.suite_name)
        cls.result.description = Utils.parse_description(cls.__doc__)
        cls.timestamp = Utils.get_timestamp()
        cls.config = ChorusGlobals.get_configinfo()
        cls.parameters = ChorusGlobals.get_parameters()

    def tearDown(self):
        '''
        tear down is executed after each case has finished, 
        you can do some clean work here, including
        1.check if crash happens, 
        2.analyze failed/passed actions, 
        3.store the case level test result 
        '''
        self.logserver.flush_console()
        if self._resultForDoCleanups.failures:
            self.parse_unittest_assertionerror()
        if self._resultForDoCleanups.errors:
            self.parse_crasherror()
        self.endTime = time.time()
        if self.result.cases.has_key(self._testMethodName):
            self.result.cases[self._testMethodName].time_taken = Utils.round_sig(self.endTime-self.startTime)
            if self.result.cases[self._testMethodName].status == ResultStatus.FAILED:
                self.result.failed_cases += 1
            elif self.result.cases[self._testMethodName].status in [ResultStatus.PASSED, ResultStatus.KNOWN_ISSUES]:
                self.result.passed_cases += 1
            self.result.cases[self._testMethodName].description = Utils.parse_description(self._testMethodDoc)
        unittest.TestCase.tearDown(self)
        
    @classmethod
    def tearDownClass(cls): 
        '''
        tearDownClass is executed after each suite has finished, 
        you can do some clean work here, including
        1.generate baseline, 
        '''
        super(MyTestCase,cls).tearDownClass()
        cls.vm.generate_baseline(cls.result)
        cls.logserver.flush_console()
        cls.suite_endtime = time.time()
        cls.result.time_taken = Utils.round_sig(cls.suite_endtime - cls.suite_starttime)
    
    def parse_unittest_assertionerror(self):
        try:
            error_message = self._resultForDoCleanups.failures[0][1]
            error_type, error_content, error_line_info = Utils.parse_error(error_message)
            self.result.cases[self._testMethodName].status = ResultStatus.FAILED
            self.result.cases[self._testMethodName].statusflag = False
            self.result.statusflag = False
            self.result.unknownflag = True
            if self.result.status != ResultStatus.CRASHED:
                self.result.status = ResultStatus.FAILED
            self.result.cases[self._testMethodName].fail_message={"type":error_type,
                                                                  "content":error_content,
                                                                  "line_info":error_line_info}
            self.result.cases[self._testMethodName].failed_assertions += 1
            self.logger.error("AssertionError: "+" - ".join([error_type, error_content, error_line_info]))
            self._resultForDoCleanups.failures = []
        except Exception, e:
            self.logger.critical("parsing assertion error failed by errors '%s'" % str(e))
            
    def parse_crasherror(self):
        try:
            error_message = self._resultForDoCleanups.errors[0][1]
            error_type, error_content, error_line_info = Utils.parse_error(error_message)
            if str(error_content).startswith("Has failed dependency test case"):
                self.result.cases[self._testMethodName].status = ResultStatus.NOT_STARTED
                self.result.cases[self._testMethodName].statusflag = False
                self.logger.critical("CaseDependencyError: "+" - ".join([error_type, error_content, error_line_info]))
            else:
                self.result.cases[self._testMethodName].status = ResultStatus.CRASHED
                self.result.cases[self._testMethodName].statusflag = False
                self.result.status = ResultStatus.CRASHED
                self.result.statusflag = False
                self.result.unknownflag = True
                self.result.crash_cases += 1
                self.logger.critical("CrashError: "+" - ".join([error_type, error_content, error_line_info]))
            self.result.cases[self._testMethodName].fail_message={"type":error_type,
                                                                  "content":error_content,
                                                                  "line_info":error_line_info}
            self._resultForDoCleanups.errors = []
        except Exception, e:
            self.logger.critical("parsing crash error failed by errors '%s'" % str(e))