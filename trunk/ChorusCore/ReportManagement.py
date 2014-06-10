'''
Created on Mar 1, 2014

@author: mxu,Anduril
@target: to generate a pretty HTML Report and an email template for CI
'''
import os,sys
import ChorusGlobals
from ChorusConstants import CommonConstants
import Utils
from jinja2 import Environment, PackageLoader
import urllib2, json
import datetime
from collections import OrderedDict
from PerformanceManagement import Performance_Result
class ReportManagement:
    TEMPLATENAME = "Static"
    def __init__(self):
        self.result = ChorusGlobals.get_testresult()
        self.logger = ChorusGlobals.get_logger()
        self.baseline_path = ChorusGlobals.get_baselinepath()
        self.output_path = ChorusGlobals.get_outputdir()
    
    def copy_template(self):
        current_dir_abs = os.path.abspath(os.path.dirname(__file__))
        status_dir_abs = os.path.join(current_dir_abs, self.TEMPLATENAME)
        output_dir_abs = os.path.join(self.output_path, self.TEMPLATENAME)
        Utils.copy_folder(status_dir_abs, output_dir_abs)
    
    def analyze_result(self):
        self.result.suite_number = self.result.passed_suites + self.result.failed_suites + self.result.crash_suites
        self.result.suites = OrderedDict(sorted(self.result.suites.items(),key=lambda t:t[0]))
        for suite_name, suite_result in self.result.suites.items():
            suite_result.cases = OrderedDict(sorted(suite_result.cases.items(),key=lambda t:t[0]))
            self.result.suites[suite_name].case_number = suite_result.passed_cases + suite_result.failed_cases + suite_result.crash_cases
            self.result.case_number += suite_result.case_number
            if suite_result.unknownflag:
                self.result.unknownflag = suite_result.unknownflag
            for case_name, case_result in suite_result.cases.items():
                case_result.assertions = OrderedDict(sorted(case_result.assertions.items(),key=lambda t:t[0]))
                suite_result.cases[case_name].assertion_number = case_result.passed_assertions + case_result.failed_assertions
                suite_result.assertion_number += case_result.assertion_number
                redundant_assertions = []
                for assertion_name, assertion_result in case_result.assertions.items():
                    if assertion_result.baseline_status and assertion_result.baseline and assertion_result.current==None:
                        redundant_assertions.append(assertion_name)
                for assertion_name in redundant_assertions:
                    del case_result.assertions[assertion_name]
            self.result.assertion_number += suite_result.assertion_number
        
    def init_ci_result(self):
        self.ciresult = CIReport()
        if os.environ.has_key("NODE_NAME"):
            self.ciresult.machine_name = os.environ["NODE_NAME"]
        if os.environ.has_key("BUILD_URL"):
            self.logger.info("Job is triggered by CI, will call api for the job info")
            self.ciresult.joblink = os.environ["BUILD_URL"]
            resp = self.ciresult.call_url()
            if isinstance(resp, dict):
                for action in resp["actions"]:
                    if action.has_key('causes'):
                        for cause in action['causes']:
                            self.ciresult.startuser = cause['shortDescription'] #ToDo, support multiple causes in future
                        if self.ciresult.startuser.startswith("Started by user"):
                            self.ciresult.startuser = self.ciresult.startuser.split("Started by user ")[1]
                        else:
                            self.ciresult.startuser = self.ciresult.startuser.split("Started by ")[1]
                    if action.has_key("parameters"):
                        self.ciresult.parameters = action["parameters"]
                    self.ciresult.starttime = datetime.datetime.fromtimestamp(float(resp['timestamp'])/1000).strftime('%Y-%m-%d %H:%M:%S')
                    self.ciresult.job = resp["fullDisplayName"]
                    self.ciresult.htmllink = self.ciresult.joblink+"HTML_Report"
                    self.ciresult.consolelink = self.ciresult.htmllink+"console"
                    self.ciresult.duration = Utils.round_sig(float(resp["duration"])/1000000)
        if os.environ.has_key(CommonConstants.KNOWN_ISSUE_KEY):
            self.ciresult.knownissueflag = True
        for suite_name in self.result.suites:
            self.ciresult.suites[suite_name] = CISuiteResult()
            if self.ciresult.htmllink:
                self.ciresult.suites[suite_name].link = self.ciresult.htmllink+"/"+suite_name+".html"
        self.logger.info("Get CI link ready in the Result.html")                 
    
    def generate_result_email(self):
        self.init_ci_result()
        env = Environment(loader=PackageLoader('ChorusCore', 'templates'))
        resulttemplate = env.get_template('result.html')
        content = resulttemplate.render({"result":self.result,"ci":self.ciresult})
        filename = os.path.join(self.output_path, 'Result.html')
        Utils.write_to_file(filename, content, "w+")
        self.logger.info("Result.html generated")
    
    def generate_performance_result(self):
        env = Environment(loader=PackageLoader('ChorusCore', 'templates'))
        performancetemplate = env.get_template("performance.html")
        content = performancetemplate.render({"earesult":Performance_Result})
        filename = os.path.join(self.output_path, 'Performance.html')
        Utils.write_to_file(filename, content, "w+")
        self.logger.info("Performance.html generated")
        
    def generate_console_report(self):
        if self.result.statusflag:
            self.logger.info("Total Test Result: %s" % self.result.status)
        else:
            self.logger.error("Total Test Result: %s" % self.result.status)
        print "----------------------------"
        for suite_name, suite_result in self.result.suites.items():
            print "%s ----- %s" % (suite_name, suite_result.status)
            if not suite_result.statusflag:
                for case_name, case_result in suite_result.cases.items():
                    if not case_result.statusflag:
                        print "---Case: %s ----- %s" % (case_name, case_result.status)
                        if case_result.fail_message:
                            print "------Case Crash Message: %s" % str(case_result.fail_message)
                            for assertion_name, assertion_result in case_result.assertions.items():
                                if not assertion_result.statusflag:
                                    print "------Assertion: %s ----- %s" % (assertion_name, assertion_result.status)   
        if not self.result.statusflag:
            sys.exit(1)
        
    def generate_html(self):
        self.analyze_result()
        self.copy_template()
        env = Environment(loader=PackageLoader('ChorusCore', 'templates'))
        for suite_name, suiteresult in self.result.suites.iteritems():
            suitetemplate = env.get_template("suite.html")
            content = suitetemplate.render({"result":suiteresult.__dict__})
            filename = os.path.join(self.output_path, '%s.html' % suite_name )
            Utils.write_to_file(filename, content, "w+")
            self.logger.info("Suite %s.html generated" % suite_name)
        summarytemplate = env.get_template('summary.html')
        xmltemplate = env.get_template('summary.xml')
        content = summarytemplate.render({"result":self.result,"ea":Performance_Result})
        filename = os.path.join(self.output_path, 'Summary.html')
        Utils.write_to_file(filename, content, "w+")
        self.logger.info("Summary.html generated")
        #TODO Modify xml
        content = xmltemplate.render({"result":self.result,"ea":Performance_Result})
        filename = os.path.join(self.output_path, 'Summary.xml')
        Utils.write_to_file(filename, content, "w+")
        self.logger.info("Summary.xml generated")
        if os.environ.has_key("BUILD_URL"):
            self.generate_result_email()
        if Performance_Result.data:    
            self.generate_performance_result()
        
class CIReport:
    def __init__(self):
        self.job = "Test Result"
        self.startuser = "Start by N/A"
        self.joblink = ""
        self.starttime = 0
        self.duration = 0
        self.htmllink = ""
        self.consolelink = ""
        self.knownissueflag = False
        self.machine_name = ""
        self.suites={}
        self.logger = ChorusGlobals.get_logger()
        self.parameters = {}
        
    def call_url(self):
        url = "%sapi/json" % self.joblink
        try:
            request = urllib2.Request(url,None)
            response = urllib2.urlopen(request)
            resp_str = response.read()
            try:
                return json.loads(resp_str)
            except:
                self.logger.error("Response data must be json format!")
                return None    
        except urllib2.HTTPError, e:
            self.logger.error("Request returned error code: %s" % str(e.code))
            return None
        except urllib2.URLError, e:
            print "Bad request, code %s" % "500"
            return None
        except Exception, e:
            print "Unexpected error: %s" % e
            return None
        

class CISuiteResult:
    def __init__(self):
        self.link = ""