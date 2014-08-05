'''
Created on Jan 19, 2014

@author: Anduril
@target: Provide global variables
'''

def set_outputdir(path):
    '''Mark output folder as global'''
    global outputdir
    outputdir = path
    
def get_outputdir():
    '''Return output folder'''
    return outputdir
        
def set_parameters(configfile):
    '''Mark configfile as global'''
    global parameters
    parameters = configfile
    
def get_parameters():
    '''Return config file'''
    return parameters

def init_logserver():
    import LogServer
    server = LogServer.LogServer("ChorusCore", 10, LogServer.Formatter.Console)
    set_logserver(server)
    set_logger(server.get_logger())

def set_logserver(logserverobj):
    '''Mark logserver as global'''
    global logserver
    logserver=logserverobj
    
def get_logserver():
    '''Return logserver'''
    if not globals().has_key("logserver"):
        init_logserver()
    return logserver

def set_logger(loggerobj):
    '''Mark logger as global'''
    global logger
    logger=loggerobj
    
def get_logger():
    '''Return logger'''
    if not globals().has_key("logger"):
        init_logserver()
    return logger

def set_current_suitename(suite_name):
    '''Mark current suitename as global'''
    global suitename
    suitename = suite_name
    
def get_current_suitename():
    '''Return current suitename'''
    return suitename

# def init_project():
#     import ProjectConfiguration,ProjectExecution
#     proj = ProjectConfiguration.ProjectConfiguration()
#     proj.setup()
#     if globals().has_key("suitename"):
#         suiteinfo["include_testsuite"] = suitename
#         if suiteinfo.has_key("exlude_testsuite"):
#             del suiteinfo["exlude_testsuite"]
#         if suiteinfo.has_key("exclude_testcase"):
#             del suiteinfo["exclude_testcase"]
#         if suiteinfo.has_key("include_testcase"):
#             del suiteinfo["include_testcase"]
#     ProjectExecution.init_testsuite()

def set_configinfo(suite_info):
    '''Mark suiteinfo as global'''
    global configinfo
    configinfo = suite_info

def get_configinfo():
    '''Return suiteinfo in config file'''
#     if not globals().has_key("suiteinfo"):
#         init_project()
    return configinfo

def set_suitedict(suite_dict):
    '''Mark suitedict as global'''

    global suitedict
    suitedict = suite_dict

def get_suitedict():
    '''Return suitedict generated from TestSuiteManagement'''
#     if not globals().has_key("suitedict"):
#         init_project()
    return suitedict

def init_testresult():
    '''Mark testresult as global'''
    from ChorusConstants import ProjectResult
    global testresult
    testresult = ProjectResult()

def set_baseurl(url):
    '''Mark baseurl as global'''
    global baseurl
    baseurl = url

def get_baseurl():
    '''Return baseurl'''
    return baseurl
    
def get_testresult():
    '''Return testresult'''
    return testresult

def set_baselinepath(baseline_path):
    '''Mark baselinepath as global'''
    global baselinepath
    baselinepath = baseline_path

def get_baselinepath():
    '''Return global baselinepath'''
    return baselinepath

def set_knownissuelist(issue_dict):
    '''Mark known_issue_list as global'''
    global known_issue_list
    known_issue_list = issue_dict

def get_knownissuelist():
    '''Return known issue list'''
    return known_issue_list

def set_xml_file(file_name):
    global xml_file_name
    xml_file_name = file_name

def get_xml_file():
    return xml_file_name
    