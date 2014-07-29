'''
Created on Nov 18, 2013

@author: Anduril
'''
from ChorusCore.MyTestCase import MyTestCase
from ChorusCore import TestScope, Utils

class TestSuite2_Pass(MyTestCase):
    '''TestSuite name must equal to the filename'''
    @classmethod
    def setUpClass(cls):
        '''Add prepare scripts before all cases'''
        super(TestSuite2_Pass,cls).setUpClass()
        
    def setUp(self):  
        '''scripts before each cases'''
        MyTestCase.setUp(self)   
        
    def tearDown(self):
        '''scripts after each cases'''
        MyTestCase.tearDown(self)

    @classmethod
    def tearDownClass(cls):
        '''Add en scripts after all cases'''
        super(TestSuite2_Pass,cls).tearDownClass()
        
    def testC01_depend(self):
        self.assertDataOnFly("A01_Compare_Equal","abcd", "abcd")
        self.assertEqual(True, False)
    
    @TestScope.setscope(TestScope.Scope.Sanity)
    @TestScope.setdependency("testC01_depend")   
    def testC02_depend(self):
        self.assertDataOnFly("A01_Compare_Equal","abcd", "abcd")