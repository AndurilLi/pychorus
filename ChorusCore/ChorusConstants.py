'''
Created on Mar 2, 2014

@author: Anduril
@target: Provide basic constants and basic class
'''

class CommonConstants:
    KNOWN_ISSUE_KEY = "KNOWN_ISSUES"
    TESTSUITE_FOLDER = "TestSuite"
    BASELINE_PATH = ["Baseline"]
    APITEMPLATE_FOLDER = "APITemplates"
    CONFIG_KEY = "DEFAULTENV"
    ENV_KEY = "env"

class ResultStatus:
    PASSED = "Passed"
    FAILED = "Failed"
    KNOWN_ISSUES = "Passed with known issues"
    CRASHED = "Crashed"
    NOT_STARTED = "Not_Started"
    
class LOGIC:
    Equal = 'Equal'
    Unequal = 'UnEqual'
    In = 'In'
    NotIn = 'NotIn'

class IMAGELOGIC:
    Zero = 0
    Fourty = 40
    Fifty = 50
    Seventy = 70
    Eighty = 80
    Ninety = 90
    Full = 100
    
class TYPES:
    Image = 'Image'
    Data= 'Data'
    HTTPResponse = 'HTTPResponse'
    Bool = 'Bool'
    Text = 'Text'

class LEVELS:
    Critical = 'Critical'
    Normal = 'Normal'
    
class ProjectResult:
    def __init__(self):
        self.suites = {}
        self.baseline_status = True
        self.suite_number = 0
        self.case_number = 0
        self.assertion_number = 0
        self.passed_suites = 0
        self.failed_suites = 0
        self.crash_suites = 0
        self.status = ResultStatus.PASSED
        self.statusflag = True
        self.scope_info = None
        self.time_taken = 0
        self.unknownflag = False
        self.knownflag = False

class SuiteResult:
    def __init__(self,name):
        self.name = name
        self.cases = {}
        self.baseline_status = True
        self.case_number = 0
        self.assertion_number = 0
        self.passed_cases = 0
        self.failed_cases = 0
        self.crash_cases = 0
        self.time_taken = 0
        self.status = ResultStatus.PASSED
        self.statusflag = True
        self.unknownflag = False
        self.description = ""
        self.fail_message = {}
        self.baseline_dict = {}
        
class CaseResult:
    def __init__(self,name):
        self.name = name
        self.assertions = {}
        self.assertion_number = 0
        self.fail_message = {}
        self.baseline_status = True
        self.passed_assertions = 0
        self.failed_assertions = 0
        self.time_taken = 0
        self.status = ResultStatus.PASSED
        self.statusflag = True
        self.description = ""
    
class AssertionResult:
    def __init__(self,name):
        self.name = name
        self.baseline_status = False
        self.baseline = None
        self.comments = None
        self.current = None
        self.detail = {}
        self.status = ResultStatus.PASSED
        self.statusflag = True
        self.similarity = 100
        self.onfly_flag = False
        self.path = ""
        
    def getsettings(self, content, level, cptype, logic, jscontent):
        self.logic = logic
        self.cptype = cptype
        self.level = level
        self.current = content
        self.detail["realvalue"]=jscontent

