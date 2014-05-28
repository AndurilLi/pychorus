'''
Created on Jan 25, 2014

@author: Anduril, mxu
@target: read config file and generate related test suite pipeline, and let unittest run each of them
'''
import Utils
import unittest
import inspect
import ChorusGlobals
import os
import importlib
import time
from ChorusConstants import ResultStatus, CommonConstants
import traceback

class TestSuiteManagement:
    '''
    Entry in charge of test suite management: get test suite, run test suite  
    '''
#     testsuites={}
    TESTSUITE_FOLDER = CommonConstants.TESTSUITE_FOLDER
    BASELINE_PATH = CommonConstants.BASELINE_PATH
    runner = []
    def __init__(self):
        
        self.logger = ChorusGlobals.get_logger()
        self.config = ChorusGlobals.get_configinfo()
        ChorusGlobals.init_testresult()
        self.result = ChorusGlobals.get_testresult()
        self.suite_dict = self.get_test_mapping()
        self.filter_test_mapping()
        self.set_scope()
        self.get_testsuites()
        self.set_baselinepath()
        self.get_knownissues()
        ChorusGlobals.set_suitedict(self.suite_dict)
    
    def get_knownissues(self):
        if os.environ.has_key(CommonConstants.KNOWN_ISSUE_KEY):
            known_issue_list = Utils.get_dict_from_json(os.environ[CommonConstants.KNOWN_ISSUE_KEY])
            ChorusGlobals.set_knownissuelist(known_issue_list)
            self.logger.info("Known issue list found in environment variables")
        else:
            ChorusGlobals.set_knownissuelist(None)
            self.logger.debug("No known issue list found in environment variables")
    
    def set_baselinepath(self):
        self.baselinepath = self.BASELINE_PATH
        if self.config.has_key("baseline"):
            paths = self.config["baseline"].split(".")
            for path in paths:
                self.baselinepath.append(path)
        ChorusGlobals.set_baselinepath(self.baselinepath)
    
    def parse_crashed_suite(self, suitename, unittest_result):
        try:
            error_message = unittest_result.errors[0][1]
            error_type, error_content, error_line_info = Utils.parse_error(error_message)
            self.result.suites[suitename].status = ResultStatus.CRASHED
            for case_name in self.result.suites[suitename].cases:
                self.result.suites[suitename].cases[case_name].status = ResultStatus.NOT_STARTED
                self.result.suites[suitename].cases[case_name].statusflag = False
            self.result.suites[suitename].statusflag = False
            self.result.suites[suitename].unknownflag = True
            self.result.statusflag = False
            self.result.unknownflag = True
            self.result.status = ResultStatus.CRASHED
            self.result.suites[suitename].fail_message={"type":error_type,
                                                        "content":error_content,
                                                        "line_info":error_line_info}
            self.logger.error("CrashError: "+" - ".join([error_type, error_content, error_line_info]))
            unittest_result.errors = []
        except Exception, e:
            traceback.print_exc()
            self.logger.critical("parsing crash error failed by errors '%s'" % str(e))
    
    def execute_suites(self):
        start_time = time.time()
        for suite in self.suites_in_scope._tests:
            unittest_result = unittest.TextTestRunner(verbosity=2).run(suite)
            self.runner.append(unittest_result)
            if unittest_result.errors:
                self.parse_crashed_suite(suite.name, unittest_result)
        end_time = time.time()
        self.result.time_taken = Utils.round_sig(end_time - start_time)
        for suite_result in self.result.suites:
            if self.result.suites[suite_result].status in [ResultStatus.PASSED, ResultStatus.KNOWN_ISSUES]:
                self.result.passed_suites += 1
            elif self.result.suites[suite_result].status == ResultStatus.FAILED:
                if self.result.status != ResultStatus.CRASHED:
                    self.result.status = ResultStatus.FAILED
                    self.result.statusflag = False
                self.result.failed_suites += 1
            else:
                self.result.status = ResultStatus.CRASHED
                self.result.statusflag = False
                self.result.crash_suites += 1
        
    def get_testsuites(self, sortflag=True):
        self.dependency_mapping = {"suites":{},"cases":{}}
        self.suites_in_scope = unittest.TestSuite()
        for suite_name in self.suite_dict.keys():
            self.check_suite_dependency(suite_name)
        if self.dependency_mapping["suites"]:
            self.logger.debug("include following suites for dependency: %s" % ",".join(self.dependency_mapping["suites"].keys()))
        if self.dependency_mapping["cases"]:
            self.logger.debug("include following cases for dependency: %s" % ",".join(self.dependency_mapping["cases"].keys()))
        suite_list = sorted(self.suite_dict.keys()) if sortflag else self.suite_dict.keys()
        for suite_name in suite_list:
            case_list = sorted(self.suite_dict[suite_name])
            try:
                suite_module = importlib.import_module("%s.%s" % (self.TESTSUITE_FOLDER, suite_name))
            except Exception,e:
                traceback.print_exc()
                self.logger.critical("Cannot import suite %s in folder %s with error %s" % (suite_name,self.TESTSUITE_FOLDER,str(e)))
                raise Exception("Cannot import suite %s in folder %s with error %s" % (suite_name,self.TESTSUITE_FOLDER,str(e)))
            suite_classes = inspect.getmembers(suite_module)
            for class_name, class_obj in suite_classes:
                if class_name == suite_name:
                    suite = unittest.TestSuite(map(class_obj,case_list))
                    suite.name = suite_name
                    self.suites_in_scope.addTest(suite)
        for insuite in self.suite_dict:
            if len(self.suite_dict[insuite])>0:
                self.logger.info("include testsuite %s cases: %s" % (insuite, ",".join(self.suite_dict[insuite])))
    
    def check_suite_dependency(self, suite_name):
        try:
            suite_module = importlib.import_module("%s.%s" % (self.TESTSUITE_FOLDER, suite_name))
        except Exception,e:
            traceback.print_exc()
            self.logger.critical("Cannot import suite %s in folder %s with error %s" % (suite_name,self.TESTSUITE_FOLDER,str(e)))
            raise Exception("Cannot import suite %s in folder %s with error %s" % (suite_name,self.TESTSUITE_FOLDER,str(e)))
        suite_classes = inspect.getmembers(suite_module)
        for class_name, class_obj in suite_classes:
            if class_name == suite_name:
                if not suite_name in self.suite_dict:
                    self.suite_dict[suite_name] = self.raw_suite_dict[suite_name]
                case_list = self.suite_dict[suite_name]
                suite = unittest.TestSuite(map(class_obj,case_list))
                suite.name = suite_name
                self.check_suite_scope(suite, suite_name, class_obj)
                for case in suite._tests:
                    if hasattr(case, "depends"):
                        raw_case_list = self.raw_suite_dict[suite_name]
                        suite = unittest.TestSuite(map(class_obj,raw_case_list))
                        self.check_case_dependency(case, suite, suite_name)
                if self.suite_dict[suite_name]:
                    suite = unittest.TestSuite(map(class_obj,self.suite_dict[suite_name]))
                else:
                    suite = None
                    del self.suite_dict[suite_name]
                if hasattr(class_obj, "global_depends") and suite._tests:
                    for suite_name_depends in class_obj.global_depends:
                        if suite_name_depends not in self.suite_dict and suite_name_depends in self.raw_suite_dict:
                            self.check_suite_dependency(suite_name_depends)
                            self.dependency_mapping["suites"][suite_name_depends] = True
    
    def check_case_dependency(self, case, suite, suite_name):
        for case_name in case.depends:
            if case_name not in self.suite_dict[suite_name]:
                self.suite_dict[suite_name].append(case_name)
                self.dependency_mapping["cases"][case_name] = True
                for case in suite._tests:
                    if case._testMethodName == case_name and hasattr(case, "depends"):
                        self.check_case_dependency(case, suite, suite_name)
        self.suite_dict[suite_name] = list(set(self.suite_dict[suite_name]))
                            
    def check_suite_scope(self, suite, suite_name, class_obj):
        cases_not_in_scope = []
        casenames_not_in_scope = []
        for case in suite._tests:
            case_name = case._testMethodName
            if hasattr(class_obj, "global_scopes"):
                case_scopes = class_obj.global_scopes
            else:
                case_scopes = case.scopes
            case_scopes = [item.lower() for item in case_scopes]
            is_in_scope = False
            if "all" in self.scopes:
                is_in_scope = True
            else:
                for scope in self.scopes:
                    if scope in case_scopes:
                        is_in_scope = True
            if not is_in_scope:
                cases_not_in_scope.append(case)
                if case_name in self.suite_dict[suite_name]:
                    self.suite_dict[suite_name].remove(case_name)
                    casenames_not_in_scope.append(case_name)
        if cases_not_in_scope:
            self.logger.debug("Removing cases not in scope: %s" % ",".join(casenames_not_in_scope))
        else:
            self.logger.info("All cases are included in %s current scope" % suite_name)
    
    def set_scope(self):
        if self.config.has_key("scope") and self.config["scope"]:
            self.result.scope_info = self.config["scope"]
            self.scopes=[]
            for item in self.config["scope"].split(','):
                self.scopes.append(item.strip().lower())
        else:
            self.scopes = ["all"]
            self.result.scope_info = "all"
        self.logger.info("Scope is set to: %s" % ','.join(self.scopes))
    
    def filter_test_mapping(self):
        self.filter_include_testsuites()
        self.filter_exclude_testsuites()
        self.filter_include_testcases()
        self.filter_exclude_testcases()
    
    def get_test_mapping(self):
        suites_path = Utils.get_filestr([self.TESTSUITE_FOLDER], "")
        suites_filelist = os.listdir(suites_path)
        suites_dict={}
        for suite_file in suites_filelist:
            if suite_file.endswith(".py"):
                suite_name = suite_file[0:suite_file.rfind('.')]
                try:
                    case_dict = Utils.class_browser("%s.%s" % (self.TESTSUITE_FOLDER,suite_name))
                except Exception,e:
                    traceback.print_exc()
                    self.logger.critical("Cannot import suite %s in folder %s with error %s" % (suite_name,self.TESTSUITE_FOLDER,str(e)))
                    raise Exception("Cannot import suite %s in folder %s with error %s" % (suite_name,self.TESTSUITE_FOLDER,str(e)))
                if case_dict:
                    case_list = []
                    for case in case_dict[suite_name].methods:
                        if case[0:4] == 'test':
                            case_list.append(case)
                    suites_dict[suite_name]=case_list
        self.raw_suite_dict = Utils.create_entity(suites_dict)
        if not suites_dict:
            self.logger.warning("No test suites found in TestSuite folder")
        return suites_dict

    def filter_include_testsuites(self):
        include_testsuites = []
        if self.config.has_key("include_testsuite"):
            temp = self.config["include_testsuite"].split(",")
            for insuite in temp:
                include_testsuites.append(insuite.strip())
        if len(include_testsuites)>0:
            origin_suite_dict=Utils.create_entity(self.suite_dict)
            self.suite_dict.clear()
            nomatchsuite = []
            for insuite in include_testsuites:
                if origin_suite_dict.has_key(insuite):
                    self.suite_dict[insuite]=origin_suite_dict[insuite]            
                else:
                    nomatchsuite.append(insuite)
            self.logger.debug("Include test suites: %s" % ",".join(self.suite_dict.keys()))
            if len(nomatchsuite)!=0:
                self.logger.warning("Following include suites: %s are not matched with any suite" % ",".join(nomatchsuite))
        else:
            self.logger.debug("All test suites to be included in configuration")
    
    def filter_exclude_testsuites(self):
        exclude_testsuites = []
        if self.config.has_key("exclude_testsuite"):
            temp = self.config["exclude_testsuite"].split(",")
            for exsuite in temp:
                exclude_testsuites.append(exsuite.strip())
        if len(exclude_testsuites)>0:
            nomatchsuite = []
            matchsuite = []
            for exsuite in exclude_testsuites:
                if exsuite in self.suite_dict.keys():
                    del self.suite_dict[exsuite]
                    matchsuite.append(exsuite)
                else:
                    nomatchsuite.append(exsuite)
            if len(matchsuite)>0:
                self.logger.debug("Skip test suites: %s" % ",".join(matchsuite))
            if len(nomatchsuite)!=0:
                self.logger.warning("Exlude suite: %s not find " % ",".join(nomatchsuite))
    
    def filter_include_testcases(self):
        include_testcases = []
        matchcase = []
        if self.config.has_key("include_testcase"):
            temp = self.config["include_testcase"].split(",")
            for incase in temp:
                include_testcases.append(incase.strip())
        if len(include_testcases)>0:
            origin_suite_dict=Utils.create_entity(self.suite_dict)
            for insuite in self.suite_dict:
                self.suite_dict[insuite]=[]
            nomatchcase = Utils.create_entity(include_testcases)
            for insuite in origin_suite_dict:
                for incase in origin_suite_dict[insuite]:
                    if incase in include_testcases:
                        self.suite_dict[insuite].append(incase)
                        matchcase.append(incase)
                        if incase in nomatchcase:
                            nomatchcase.remove(incase)
            if len(nomatchcase)!=0:
                self.logger.warning("Following include cases: %s are not matched with any case" % ",".join(nomatchcase))
            if len(matchcase)!=0:
                self.logger.debug("Chorus will only run test cases from INCLUDE_TESTCASES: %s" % ",".join(matchcase))
    
    def filter_exclude_testcases(self):
        exclude_testcases = []
        matchcase = []
        if self.config.has_key("exclude_testcase"):
            temp = self.config["exclude_testcase"].split(",")
            for excase in temp:
                exclude_testcases.append(excase.strip())
        if len(exclude_testcases)>0:
            nomatchcase = Utils.create_entity(exclude_testcases)
            for excase in exclude_testcases:
                for insuite in self.suite_dict:
                    if excase in self.suite_dict[insuite]:
                        self.suite_dict[insuite].remove(excase)
                        matchcase.append(excase)
                        if excase in nomatchcase:
                            nomatchcase.remove(excase)
            if len(matchcase)>0:
                self.logger.debug("Skip test cases: %s" % ",".join(matchcase))
            if len(nomatchcase)!=0:
                self.logger.warning("Following exclude cases: %s are not matched with any case" % ",".join(nomatchcase))
