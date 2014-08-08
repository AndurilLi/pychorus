'''
Created on Jan 19, 2014

@author: mxu, Anduril
@target: provide reusable functions
'''
import os, stat, shutil, errno, ConfigParser,pyclbr,copy,json, base64
import datetime, random
from subprocess import Popen, PIPE
import traceback
def remove_path(path):
    '''Remove file or folder'''
    try:
        
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=False, onerror=handle_readonly)
        elif os.path.exists(path):
            os.remove(path)
        print "Remove Directory %s Successfully" % path
    except Exception,e:
        traceback.print_exc()
        print e
        raise Exception("Cannot remove the directory %s" % path)

def handle_readonly(func, path, exc):
    '''Callable function for removing readonly access'''
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise Exception("Cannot handle read-only file, need to remove %s manually" % path)
    
def create_folder(folderpath, foldername, refreshflag=True):
    '''create a folder: 
       refreshflag=True: if folder exists, then delete it and re-create; else just create the folder
       refreshflag=False: if folder doesn't exist, then create the folder'''
    if folderpath=="" or os.path.isdir(folderpath):
        newfolder = os.path.join(folderpath,foldername)
        if os.path.isdir(newfolder):
            if refreshflag:
                try:
                    remove_path(newfolder)
                    os.makedirs(newfolder)
                except:
                    for filename in os.listdir(newfolder):
                        os.remove(os.path.join(newfolder, filename))
        else:
            os.makedirs(newfolder)
    else:
        raise Exception("Invalid Folder %s" % folderpath)
    return newfolder

def get_filelist(paths = None,filename = ''):
    fullpath = os.getcwd()
    fullpath_list = fullpath.split(os.sep)
    for path in paths:
        fullpath_list.append(path)
    if filename:
        fullpath_list.append(filename)
    return fullpath_list

def get_filestr(paths = None,filename = ''):
    '''Return File Fullpath'''
    fullpath = ""
    for path in paths:
        fullpath = os.path.join(fullpath, path)
    if not os.path.abspath(fullpath):
        fullpath = os.path.join(os.getcwd(), fullpath)
    if not os.path.exists(fullpath):
        os.makedirs(fullpath)
    return os.path.join(fullpath,filename)

def dump_dict_to_file(dictobj,paths,filename):
    filename = get_filestr(paths,filename)
    if os.path.exists(filename):
        os.remove(filename)
    jsonobj = json.dumps(dictobj,indent=2,sort_keys=True)
    write_to_file(filename,jsonobj)

def write_to_file(filename, content, opentype="wb"):
    f = file(filename,opentype)
    f.write(content)
    f.close()
    
def copy_to_file(src, dst):
    shutil.copy(src, dst)

def copy_folder(src, dst):
    """
    copy file from src to dst 
    also support recursively copy an entire directory tree rooted at src
    """
    shutil.rmtree(dst,ignore_errors=True)
    if not os.path.isdir(dst):   
        try:
            shutil.copytree(src, dst)
        except OSError as exc: 
            if exc.errno == errno.ENOTDIR:
                shutil.copy(src, dst)
            else: 
                traceback.print_exc()
                raise

def read_config(config_file):
    '''Read cfg file'''
    cfg = ConfigParser.RawConfigParser()
    cfg.optionxform = str
    cfg.read(config_file)
    if not cfg.sections():
        raise Exception("Cannot read config info from %s at %s, please check you configfile!" % config_file)
    else:
        print "Set config file to %s" % config_file
    return cfg

def get_timestamp():
    '''Return currenttime in '''
    now = datetime.datetime.utcnow()
    timestamp = '%s%s%s%s%s%s%s' % (now.year,now.month,now.day,now.hour,now.minute,now.second,now.microsecond)
    return timestamp

def class_browser(module, path=None):
    return pyclbr.readmodule_ex(module, path or [])

def create_entity(obj):
    return copy.copy(obj)

def _decode_list(lst):
    '''Written by Huangfu'''
    newlist = []
    for i in lst:
        if isinstance(i, unicode):
            i = i.encode('utf-8')
        elif isinstance(i, list):
            i = _decode_list(i)
        newlist.append(i)
    return newlist

def _decode_dict(dct):
    '''Written by Huangfu'''
    newdict = {}
    for k, v in dct.iteritems():
        if isinstance(k, unicode):
            k = k.encode('utf-8')
        if isinstance(v, unicode):
            v = v.encode('utf-8')
        elif isinstance(v, list):
            v = _decode_list(v)
        newdict[k] = v
    return newdict

def get_dict_from_json(data):
    try:
        jsonobj = json.loads(data,object_hook=_decode_dict)
        return jsonobj
    except Exception,e:
        raise Exception("Get json from string failed with error %s" % str(e))
    
def get_json_from_file(paths = None,filename = None):
    """
    get json from file
    
    @param paths: paths where file is kept
    @type paths: str
    @param filename: name of the file from which you want to read
    @type filename: str
    
    @return: jsonobj  
    """
    try:
        if paths:
            filestream = open(get_filestr(paths,filename), 'rb')
        else:
            filestream = open(get_filestr(filename))
        jsonobj = json.load(filestream,object_hook=_decode_dict)
        filestream.close()
        return jsonobj
    except Exception,e:
        traceback.print_exc()
        raise Exception("Open file %s error or Json type not correct due to '%s'" % (filename,str(e)))

def del_dict_keys(obj, keys):
    if isinstance(obj, dict) and isinstance(obj, dict):
        for key in create_entity(obj).keys():
            if key in keys:
                print key
                del(obj[key])
            else:
                del_dict_keys(obj[key], keys)               

    elif isinstance(obj, list) or isinstance(obj, tuple):

        length = len(obj)
            
        for index in range(0, length):
            del_dict_keys(obj[index],keys)

    return obj

def get_current_classname(obj):
    infolist = obj.__module__.split('.')
    return infolist[-1]

def simple_compare(obj1, obj2):
    if type(obj1)!=type(obj2):
        return False
    else:
        if obj1!=obj2:
            return False
        else:
            return True
        
def base64decode(value):
    return base64.b64decode(value)

def exec_cmd(arg_list, communication = None, wait = True, return_process = True):
    '''Written by Huangfu, enhanced by Mingze'''
    process = Popen(arg_list, stdin = PIPE, stdout = PIPE, stderr = PIPE)
    if communication != None:
        process.communicate(communication)
    elif wait:
        output = process.communicate()    
    if return_process:
        return process
    else: 
        return output

def whereis(*args):
    suffixs=(".exe", ".bat", ".sh", ".pl")
    paths = os.environ['PATH'].split(os.pathsep)
    #print "System paths: %s" % os.environ['PATH']
    for path in paths:
            for arg in args:
                    path_exec = path + os.sep + arg
#                    print "Executable: %s" % path_exec
                    isexist = False
                    file_exec = ""
                    if os.path.exists(path_exec):
                        isexist = True
                        file_exec = path_exec
                    else:
                        for suffix in suffixs:
                            if os.path.exists(path_exec + suffix):
                                isexist = True
                                file_exec = path_exec + suffix
                    if isexist:
                        #print "Executable file is found:%s" % file_exec
                        return file_exec
    print "No executable files found! Please add it into environment path"
    return ""

def get_parameters(*args):
    import ChorusGlobals
    parameters = ChorusGlobals.get_parameters()
    result = None
    if parameters.has_key(args[0]):
        result = parameters[args[0]]
    if len(args)==1:
        return result    
    for path in args[1:]:
        if result:
            if result.has_key(path):
                result = result[path]
            else:
                result = None
    if not result:
        ChorusGlobals.get_logger().warning("No value retrieved for path %s" % str(args))
    return result

def get_random_str(length = 16):
    import string
    return ''.join(random.sample(string.ascii_letters+string.digits,length))

def extract_str(rawstr, start, end):
    try:
        temp1=rawstr.split(start)
        temp2=temp1[1].split(end)
        newstr=temp2[0]
        return newstr
    except Exception:
        return ""

def parse_error(msg):
    temp_msgs = msg.strip().split("\n")
    temp_msgs2 = temp_msgs[-1].split(":")
    error_type = temp_msgs2[0].strip()
    error_content = temp_msgs2[1].strip()
    error_line_info = "\n"+"\n".join(temp_msgs[1:-1]).strip()
    return error_type, error_content, error_line_info

def parse_description(description):
    desp = []
    try:
        lines = description.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                key = extract_str(line, "[", "]")
                value = line[line.find("]")+1:].strip()
                desp.append([key,value])
        return desp
    except Exception:
        return []
    
def round_sig(x, sig = 3):
    '''return by default 3 significant digit number'''
    from math import log10, floor
    try:
        return round(x, sig - int(floor(log10(abs(x))))-1)
    except:
        return 0
    
def qr_decode_deprecated(element=None, image_filepath=None, parse_url="http://zxing.org/w/decode"):
    from APIManagement import Request,RequestMode
    try:
        if element:
            element.get_screenshot_as_file("temp_code.png")
            filepath = "temp_code.png"
        elif image_filepath:
            filepath = image_filepath
        else:
            print "No input value"
            return False
        req = Request(base_url=parse_url, method="POST", mode=RequestMode.multi_form,
                      upload_files={"f":filepath})
        req.send()
        data = req.result["data"].split('<pre style="margin:0">')
        if element:
            os.remove(filepath)
        return data[-1].split("</pre>")[0]
    except Exception, e:
        traceback.print_exc()
        print "Decode QRCode meets error %s" % str(e)
        return False

def qr_decode(element=None, image_filepath=None, parse_url="http://chorusserver.labs.microstrategy.com:8765/qr_decode"):
    from APIManagement import Request,RequestMode
    try:
        if element:
            element.get_screenshot_as_file("temp_code.png")
            filepath = "temp_code.png"
        elif image_filepath:
            filepath = image_filepath
        else:
            print "No input value"
            return False
        req = Request(base_url=parse_url, method="POST", mode=RequestMode.multi_form,
                      upload_files={"f":filepath})
        req.send()
        if element:
            os.remove(filepath)
        if req.result["status"] == "200":
            return req.result["data"]
        else:
            print "QRDecode Server Error: %s" % req.result["data"]
    except Exception, e:
        traceback.print_exc()
        print "Decode QRCode meets error %s" % str(e)
    return qr_decode_deprecated(element, image_filepath)


def get_svninfo():
    from SSHHelper import SSHHelper
    ssh = SSHHelper("localhost")
    try:
        result = ssh.exe_cmd("svn info", shell=True)
    except Exception, e:
        traceback.print_exc()
        message = "svn get failed with error %s" % str(e)
        print message
        return (False, message.replace("'","\\'"))
    if result.code == 0:
        print "Getting svn info success"
        for line in result.stdout.split("\n"):
            if line.startswith("URL: "):
                return (True, line.split("URL: ")[1].strip())
    else:
        message = "Getting svn info failed %s" % result.stderr
        print message
        return (False, message.replace("'","\\'"))
    