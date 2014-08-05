'''
Created on Jan 19, 2014

@author: Anduril
@target: provide a basic class for user to parse config file
'''
import os, sys, optparse
import Utils
import ChorusGlobals
from LogServer import LogServer,Level, LogType, Formatter
from ChorusConstants import CommonConstants
import traceback
class ProjectConfiguration:
    '''Load options, own all project step functions'''
    def init_options(self):
        self.parser = optparse.OptionParser()
        self.parser.add_option("-c","--config",dest="configfile",
                               default="default.cfg",
                               help="config file name, e.g: test.cfg")
        self.parser.add_option("-p","--path",dest="configpath",
                               default="",
                               help="config file path, default: Config/, e.g. test")
        self.parser.add_option("-o","--output",dest="outputpath",
                               default="",
                               help="output file path, default: Output/, e.g: Output")
        self.parser.add_option("--color",dest="color",
                               default=False, action="store_true",
                               help="provide a colorful console with different log level")
        self.parser.add_option("-e","--env",dest="env",
                               default=None, 
                               help="choose environment to run the test in config file")
        self.parser.add_option("-d","--directory", dest="directory",
                               default=None,
                               help="Current working directory full path, which contains the Config/Testsuite/Baseline folder, if you are in the default directory, you can omit this option")
        self.parser.add_option("--xml", dest="xml", 
                               default=None,
                               help="give a configuration XML file which define the test execution order. And other cofiguration in scipts/config file will be ignored")
        
    def setup(self, argv=[]):
        if not hasattr(self,"parser"):
            self.init_options()
        self.options, argv = self.parser.parse_args(list(argv))
        self.set_working_directory()
        self.set_output_folder()
        self.set_logserver()
        self.set_configfile()
        self.set_xml_file()
    
    def set_working_directory(self):
        if self.options.directory:
            if os.path.isdir(self.options.directory):
                os.chdir(self.options.directory)
        current_dir_abs = os.getcwd()
        sys.path.append(current_dir_abs)
    
    def set_output_folder(self):
        '''Set output folder
           Input: options.outputpath
           Output: self.outputdir, ChorusGlobals.outputdir'''
        self.outputdir = os.path.abspath(Utils.create_folder(self.options.outputpath, "Output", True))
        ChorusGlobals.set_outputdir(self.outputdir)
        print "Set output directory to %s" % self.outputdir
        
    def set_configfile(self):
        configfile = ConfigFile(self.options.configfile,self.options.configpath)
        configfile.get_env(self.options.env)
        self.parameters = configfile.parameters
        self.config = configfile.config
        ChorusGlobals.set_parameters(self.parameters)
        ChorusGlobals.set_configinfo(self.config)

    def set_logserver(self, name = LogType.ChorusCore, level=Level.debug,
                formatter=Formatter.Console):
        self.logserver=LogServer(name, level, formatter, 
                                 colorconsole = False if not hasattr(self,"options") else self.options.color)
        ChorusGlobals.set_logserver(self.logserver)
        ChorusGlobals.set_logger(self.logserver.get_logger())
    
    def set_xml_file(self):
        if self.options.xml:
            print self.options.xml
            if os.path.isfile(self.options.xml):
                if str(self.options.xml).endswith(".xml"):
                    ChorusGlobals.set_xml_file(self.options.xml)
                    return
                else:
                    print "The test execution configuration file should be an XML file"
            else:
                print "Can't find xml file %s" % (str(self.options.xml))
        ChorusGlobals.set_xml_file(None)
        
#     def close_logserver(self):
#         self.logserver.close_logger()

class ConfigFile:
    '''Read Config file'''
    parameters={}
    def __init__(self, config_filename, config_filepath=None):
        self.CONFIG_KEY = CommonConstants.CONFIG_KEY
        self.logger = ChorusGlobals.get_logger()
        if config_filepath=="":
            config_filepath = "Config"
        else:
            config_filepath = os.path.join("Config",config_filepath)
        config_paths = config_filepath.split(os.path.sep)
        self.config_filepath = Utils.get_filestr(config_paths, config_filename)
        self.cfg=Utils.read_config(self.config_filepath)
        try:
            self.get_config()
            self.get_parameters()
        except Exception,e:
            traceback.print_exc()
            self.logger.critical("Cannot get suite information from config file %s with error: %s:%s" % (config_filename,str(Exception),str(e)))
            raise Exception("Cannot get suite information from config file %s with error: %s:%s" % (config_filename,str(Exception),str(e)))
    
    def write_config(self):
        with open(self.config_filepath, 'wb') as config_file:
            self.cfg.write(config_file)
    
    def get_config(self):
        section = self.CONFIG_KEY
        tmpdict = {}
        for option in self.cfg.options(section):
            if option.lower() in ["include_testsuite","exclude_testsuite","include_testcase","exclude_testcase","scope","env","baseline"]:
                real_option = option.lower()
            else:
                real_option = option
            tmpdict[real_option] = self.cfg.get(section, option)
        self.config = tmpdict
    
    def get_env(self, env = None):
        if env:
            new_envs = env.split(",")
        elif self.config.has_key(CommonConstants.ENV_KEY) and self.config[CommonConstants.ENV_KEY]!=self.CONFIG_KEY:
            new_envs = self.config[CommonConstants.ENV_KEY].split(",")
        else:
            new_envs = None
            self.logger.info("Load Default section as environment")
        if new_envs:
            for new_env in new_envs:
                env_key = new_env.strip()
                if self.parameters.has_key(env_key):
                    self.config[CommonConstants.ENV_KEY]=env_key
                    for key in self.parameters[env_key]:
                        if key.lower() in ["include_testsuite","exclude_testsuite","include_testcase","exclude_testcase","scope","env","baseline"]:
                            real_key = key.lower()
                        else:
                            real_key = key
                        self.config[real_key]=self.parameters[env_key][key]
                    self.logger.info("Load %s section as environment" % env_key)
                else:
                    self.logger.warning("Cannot load %s section, will use Default instead" % env_key)     
    
    def get_parameters(self):
        for section in self.cfg.sections():
            if section!=self.CONFIG_KEY:
                tmpdict = {}
                for option in self.cfg.options(section):
                    tmpdict[option] = self.cfg.get(section, option)
                self.parameters[section] = tmpdict