'''
Created on Aug 4, 2014

@author: pli
'''
import web, sys, os, optparse, json, base64, traceback
import Utils
from LogServer import LogServer, LogType, Formatter
from SSHHelper import SSHHelper
from APIManagement import Request

class SVNAccount:
    username = None
    password = None
    
    @classmethod
    def setup(cls, username, password):
        cls.username = username
        cls.password = password

class Server:
    workdirectory = None
    msglogger = None
    reqlogger = None
    
    @classmethod
    def setup(cls, directory = None):
        if not directory:
            cls.workdirectory = os.path.abspath(os.path.join(os.getcwd(),"Output"))
        else:
            cls.workdirectory = os.path.abspath(os.path.join(directory,"Output"))
        if not os.path.isdir(cls.workdirectory):
            os.makedirs(cls.workdirectory)
        cls.msgserver = LogServer()
        cls.msgserver.add_filehandler(filepath=cls.workdirectory, filename="Server.log")
        cls.msglogger = cls.msgserver.get_logger()
        cls.reqserver = LogServer(name = LogType.Request, formatter=Formatter.Request)
        cls.reqserver.add_filehandler(formatter=Formatter.Request, filepath=cls.workdirectory, filename="Request.log")
        cls.reqlogger = cls.reqserver.get_logger()
        cls.msglogger.info("Set working directory %s" % cls.workdirectory)
        
class RequestHandler:
    def GET(self):
        self.get_request()
        return self.message_helper("URL not set", "200 OK")
    def POST(self):
        self.get_request()
        return self.message_helper("URL not set", "200 OK")
    def PUT(self):
        self.get_request()
        return self.message_helper("URL not set", "200 OK")
    def DELETE(self):
        self.get_request()
        return self.message_helper("URL not set", "200 OK")
    
    def _parse_parameters(self):
        parameters = {}
        params = web.ctx.env["QUERY_STRING"]
        if params:
            for para in params.split("&"):
                key, value = para.split("=")
                parameters[key] = value
        return parameters
    
    def _parse_reqheaders(self):
        headers = {}
        for key, value in web.ctx.env.items():  # @UndefinedVariable
            if key.startswith("HTTP_"):
                real_key = key.split("HTTP_",2)[1].replace("_", "-")
                headers[real_key] = value
            elif key.startswith("CONTENT_"):
                real_key = key.replace("_", "-")
                headers[real_key] = value
        headers = dict((k.encode('utf-8'),v.encode('utf-8')) for k,v in headers.items())
        return headers
    
    def message_helper(self, message, status):
        try:
            json.dumps(self.request["requestbody"])
        except:
            self.request["requestbody"] = base64.b64encode(self.request["requestbody"])
            Server.msglogger.info("Request body is encoded with base64")
        self.request["responsebody"] = message
        self.request["status"] = status
        Server.reqlogger.info("", extra = self.request)
        web.ctx.status = status
        del self.request
        return message
    
    def get_request(self):
        self.request = {
                            "url": web.ctx.fullpath.encode('utf-8'),
                            "method": web.ctx.method.encode('utf-8'),
                            "requestheaders": self._parse_reqheaders(),
                            "requestbody": web.data(),
                            "path": str(web.ctx.path).encode('utf-8'),
                            "parameters": self._parse_parameters(),
                            "remote_address":":".join([web.ctx.env["REMOTE_ADDR"],web.ctx.env["REMOTE_PORT"]]),   
                        }
    
class UpdateBaseline(RequestHandler):
    def GET(self):
        self.get_request()
        rawdata = web.input()
        os.chdir(Server.workdirectory)
        try:
            data = Utils.get_dict_from_json(rawdata.data)
            suitename = data["suite_name"]
            svnflag = True if data.get("svnlink") and data.get("comment") else False
            baseline_paths = os.path.split(os.path.join(data["baseline_path"].replace("\\\\","\\"),suitename))
            output_paths = os.path.split(os.path.join(data["output_path"].replace("\\\\","\\"), suitename))
            helper = SSHHelper("localhost")
            if not data.get("ci_link"):
                ci_link = None
                baseline_path = Utils.get_filestr(baseline_paths)
                os.chdir(baseline_path)
                if svnflag:
                    result = helper.exe_cmd("svn revert -R .",printcmd=False)
                    if result.code != 0:
                        return self.message_helper("svn revert failed %s" % result.stderr, "200 OK")
                    result = helper.exe_cmd("svn up .",printcmd=False)
                    if result.code != 0:
                        return self.message_helper("svn update failed %s" % result.stderr, "200 OK")
            else:
                ci_link = data["ci_link"]
                job_name = ci_link.split("/")[-3]
                work_path = os.path.join(Server.workdirectory, job_name)
                baseline_path = os.path.join(work_path, os.path.split(data["baseline_path"].replace("\\\\","\\"))[-1])
                if os.path.exists(baseline_path):
                    os.chdir(baseline_path)
                    result = helper.exe_cmd("svn up . --username=%s --password=%s" % (SVNAccount.username, SVNAccount.password),printcmd=False)
                    if result.code != 0:
                        return self.message_helper("svn update failed %s" % result.stderr, "200 OK")
                else:
                    os.mkdir(work_path)
                    os.chdir(work_path)
                    result = helper.exe_cmd("svn co %s --username=%s --password=%s" % (data["svnlink"],SVNAccount.username, SVNAccount.password),printcmd=False)
                    if result.code != 0:
                        return self.message_helper("svn checkout failed %s" % result.stderr, "200 OK")
                    os.chdir(baseline_path)
                baseline_paths = os.path.split(os.path.join(baseline_path,suitename))
            base_filename = suitename + ".base"
            baseline_caselist = Utils.get_json_from_file(baseline_paths, base_filename)
            if not ci_link:
                output_caselist = Utils.get_json_from_file(output_paths, base_filename)
            else:
                ci_basefile = ci_link+"/"+suitename+"/"+base_filename
                api = Request(method="GET", base_url=ci_basefile)
                resp = api.send()
                if resp.result["status"]!="200":
                    return self.message_helper("Invalid CI link %s" % ci_basefile, "200 OK")
                output_caselist = resp.result["data"]
            for baseline in data["baseline"]:
                casename, assertionname = baseline.split("/")
                if output_caselist[casename][assertionname].get("image_type"):
                    image_name = output_caselist[casename][assertionname]["image_name"] + "." + output_caselist[casename][assertionname]["image_type"]
                    self.copy_image(suitename, image_name, baseline_paths, output_paths, ci_link)
                if not baseline_caselist.get(casename):
                    baseline_caselist[casename] = {}
                baseline_caselist[casename][assertionname] = output_caselist[casename][assertionname]
            Utils.dump_dict_to_file(baseline_caselist, baseline_paths, base_filename)
            if svnflag:
                result = helper.exe_cmd("svn add . --force",printcmd=False)
                if result.code != 0:
                    return self.message_helper("svn add failed %s" % result.stderr, "200 OK")
                result = helper.exe_cmd('''svn ci . -m "%s"''' % data["comment"],printcmd=False)
                if result.code != 0:
                    return self.message_helper("svn checkin failed %s" % result.stderr, "200 OK")
            web.ctx.headers = [("Access-Control-Allow-Origin","*")]
            return self.message_helper('Update Successful', "200 OK")
        except Exception, e:
            traceback.print_exc()
            return self.message_helper("Problem on updating code logic: %s" % str(e), "500 Internal Server Error")
    
    def copy_image(self, suitename, image_name, baseline_paths, output_paths, ci_link):
        image_path = Utils.get_filestr(baseline_paths, image_name)
        if ci_link:
            ci_basefile = ci_link+"/"+suitename+"/"+image_name
            api = Request(method="GET", base_url=ci_basefile)
            resp = api.send()
            if resp.result["status"]!="200":
                raise Exception("picture %s cannot be downloaded" % ci_basefile)
            f = open(image_path, "wb")
            f.write(resp.result["data"])
            f.close()
        else:
            new_image_path = Utils.get_filestr(output_paths, image_name)
            Utils.copy_to_file(new_image_path, image_path)
    
class QRDecode:
    def POST(self):
        #TODO
        os.chdir(Server.workdirectory)
        rawdata = web.input(f="")
        print rawdata
        return '{"status":"OK"}'

def main(argv = sys.argv):
    parser = optparse.OptionParser()
    parser.add_option("--port", dest="port", default="8080", help="Chorus Server Port")
    parser.add_option("-u", "--username", dest="username", help="svn username")
    parser.add_option("-p", "--password", dest="password", help="svn password")
    parser.add_option("-o", "--output", dest="output", default="",
                      help="an output folder to handle svn project and save log file")
    options, argv = parser.parse_args(list(argv))
    SVNAccount.setup(options.username, options.password)
    Server.setup(options.output)
    urls = (
            '/update_baseline', "UpdateBaseline",
            '/qr_decode', "QRDecode",
            '^.*', 'RequestHandler'
            )
    app = web.application(urls, globals())
    sys.argv[1:] = ["%s" % (str(options.port))]
    app.run()
    