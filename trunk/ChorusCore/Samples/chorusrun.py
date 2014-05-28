#!/Users/mxu/Documents/py_env/bin/python
'''
Created on Dec 28, 2013

@author: Anduril
'''
import sys
# from ChorusCore.ProjectConfiguration import ProjectConfiguration
# from ChorusCore.ProjectExecution import RunTest
# from ChorusCore.LogServer import Level
# class MyProject(ProjectConfiguration):
#     def __init__(self, argv):
#         self.init_options()
#         '''Add your own options here by self.parser.add_option(...)'''
#         self.options, argv = self.parser.parse_args(argv)
#         '''Add your functions called by the added options here'''
#         self.set_working_directory()
#         self.set_output_folder()
#         self.set_logserver(level=Level.debug)
#         self.logserver.add_filehandler(level=Level.error,
#                                        filepath=self.outputdir,filename="error.log")
#         self.logserver.add_filehandler(level=Level.info,
#                                        filepath=self.outputdir,filename="info.log")
#         self.set_configfile()
#     
# #    def __init__(self, argv):
# #        self.setup(argv)
#         
#     def start_test(self): 
#         RunTest()

from ChorusCore import RunTest
RunTest.main(sys.argv)