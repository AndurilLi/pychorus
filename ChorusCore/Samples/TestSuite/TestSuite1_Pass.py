'''
Created on Nov 18, 2013

@author: Anduril
'''
from ChorusCore.MyTestCase import MyTestCase
from ChorusCore import TestScope, Utils
from ChorusCore import PerformanceManagement
#@TestScope.setscope(TestScope.Scope.Sanity,TestScope.Scope.Regression)
@TestScope.setdependency("TestSuite2_Pass")
class TestSuite1_Pass(MyTestCase):
    '''TestSuite name must equal to the filename'''
    @classmethod
    def setUpClass(cls):
        '''Add prepare scripts before all cases'''
        super(TestSuite1_Pass,cls).setUpClass()
        cls.picture1 = open(Utils.get_filestr(["TestData"], "test_photo.png"),"rb")
        cls.picdata1 = cls.picture1.read()
        cls.picture2 = open(Utils.get_filestr(["TestData"], "test_photo1.png"),"rb")
        cls.picdata2 = cls.picture2.read()

    def setUp(self):  
        '''scripts before each cases'''
        MyTestCase.setUp(self)   
        
    def tearDown(self):
        '''scripts after each cases'''
        MyTestCase.tearDown(self)

    @classmethod
    def tearDownClass(cls):
        '''Add en scripts after all cases'''
        super(TestSuite1_Pass,cls).tearDownClass()
    
    @PerformanceManagement.EAFlag()
    @TestScope.setscope(TestScope.Scope.Sanity,TestScope.Scope.Regression)
    @TestScope.setdependency("testC05_depend")
    def testC01_pass(self):
        '''[Notice] Each test case must start with a "test" label
           [author] Anduril
           [Target] Show this function
           [Pre-requisite] ~
           [Expect Result] All Pass for case 1
           [Step 1] assert a bool equal to True, compare with baseline
           [Step 2] assert a dict data, compare with baseline
           [Step 3] assert a image data, compare with baseline
           [Step 4] use unittest assertion to assert a true, with a message claimed
           [Step 5] use unittest assertion to compare two data
           [Step 6] call an API and assert it, then compare with baseline
        '''
        self.assertBool("A01_Compare_Bool", True)
        self.assertData("A02_Compare_Data_With_Baseline", {"data":"I like chorus"})
        self.assertImageData("A03_Compare_Photo_With_Baseline", self.picdata1, image_logic=100, imagetype="png")
        self.assertTrue(True, "Break_Message_for_unitteset_assertTrue")
        self.assertEqual("A01_data","A01_data","Break_Message_for_unittest_assertEqual")
        from ChorusCore.APIManagement import Request
        api = Request(url = "data/cityinfo/101010100.html", method = "get", base_url = "http://www.weather.com.cn", timeout = 3).send()
        self.assertHTTPResponse("A04_HttpCompare_With_Baseline", api)
        
    @TestScope.setscope(TestScope.Scope.Regression)
    def testC02_fail(self):
        self.assertImageData("A01_Compare_Photo_With_Baseline", self.picdata2, image_logic=100, imagetype="png")
        self.assertData("A01_Compare_Data_With_Baseline", {"data":"I don't like chorus"})
        self.assertBool("A01_Compare_Bool", False)
        #self.assertTrue(False, "Break_Message_for_unitteset_assertTrue")
        self.assertEqual("A01_data","A02_data","Break_Message_for_unittest_assertEqual")
        
    def testC03_crash(self):
        self.assertBool("A01_Compare_Bool", True)
        abc
    
    @TestScope.setscope(TestScope.Scope.Regression)
    def testC04_crash(self):
        self.assertBool("A01_Compare_Bool", True)
        abc
    
    def testC05_depend(self):
        self.wait_timeout()
        self.assertDataOnFly("A01_Compare_Equal","abcd", "abcd")
    
    @staticmethod
    @PerformanceManagement.EAFlag(name="Test timeout fail", detail={"hi":"here is performance result"}, timeout=2)
    def wait_timeout(timeout = 3):
        import time
        time.sleep(4)