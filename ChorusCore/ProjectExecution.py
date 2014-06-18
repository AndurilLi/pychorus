'''
Created on Jan 20, 2014

@author: Anduril
@target: provide a basic framework of chorus, you may inherit and change it by yourself
'''

from TestSuiteManagement import TestSuiteManagement
from VerificationManagement import VerificationManagement
from ReportManagement import ReportManagement

class RunTest:
    result = []
    def __init__(self):
#        self.currunname=Utils.get_timestamp()
        self.init_testsuite()
        self.run_testsuite()
        self.generate_report()
        
    def init_testsuite(self):
        self.tsm = TestSuiteManagement()
        self.vm = VerificationManagement()
        self.vm.check_allbaselines()
        
    def run_testsuite(self):
        self.tsm.execute_suites()
    
    def generate_report(self):
        self.rm = ReportManagement()
        self.rm.generate_html()
        self.rm.generate_console_report()
        