#!/Users/mxu/Documents/py_env/bin/python
'''
Created on Dec 28, 2013

@author: Anduril
'''
import sys,os
import optparse
from ProjectConfiguration import ProjectConfiguration,ConfigFile
from ProjectExecution import RunTest
# from LogServer import Level
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
#    def __init__(self, argv):
#        self.setup(argv)
#         
#     def start_test(self): 
#         RunTest()

def main(argv = sys.argv):
#     init=MyProject(list(argv))
#     init.start_test()
    proj = ProjectConfiguration()
    proj.setup(argv)
    RunTest()

def modify_config(argv = sys.argv):
    parser = optparse.OptionParser()
    parser.add_option("-c","--config",dest="configfile",
                      default="default.cfg",
                      help="config file name, e.g: test.cfg")
    parser.add_option("-p","--path",dest="configpath",
                      default="",
                      help="config file path, default: Config, e.g. test")
    parser.add_option("-s", dest="section",
                      help="section name, e.g: DEFAULTENV")
    parser.add_option("-k", dest="keyname",
                      help="key name, e.g: Scope")
    parser.add_option("-v", dest="value",
                      help="key value, e.g: All")
    parser.add_option("-d","--directory", dest="directory",
                      default=None,
                      help="Current working directory full path, which contains the Config/Testsuite/Baseline folder, if you are in the default directory, you can omit this option")
    parser.add_option("--xml", dest="xml", 
                     default=None,
                     help="give a configuration XML file which define the test execution order. And other cofiguration in scipts/config file will be ignored")
    options, argv = parser.parse_args(list(argv))
    if options.directory:
        if os.path.isdir(options.directory):
            os.chdir(options.directory)
    current_dir_abs = os.getcwd()
    sys.path.append(current_dir_abs)
    if not hasattr(options,"section") or not hasattr(options,"keyname") or not hasattr(options,"value"):
        print "please enter section name, key name and key value by the correct format"
        sys.exit()
    else:
        configfile = ConfigFile(options.configfile, options.configpath)
        configdata = configfile.cfg
        if configdata.has_section(options.section):
            configdata.set(options.section, options.keyname, options.value)
        else:
            configdata.add_section(options.section)
            print "add new section %s" % options.section
            configdata.set(options.section, options.keyname, options.value)
        configfile.write_config()
        print "set section %s key %s with value %s successful" % (options.section, options.keyname, options.value)