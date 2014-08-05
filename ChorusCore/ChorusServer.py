'''
Created on Aug 4, 2014

@author: pli
'''
import web, sys, os, optparse
import Utils, json
from SSHHelper import SSHHelper
from APIManagement import Request

class SVNAccount:
    username = None
    password = None
    
    @classmethod
    def setup(cls, username, password):
        cls.username = username
        cls.password = password

class Constants:
    workdirectory = None
    
    @classmethod
    def setup(cls, directory = None):
        if not directory:
            cls.workdirectory = os.path.abspath(os.path.join(os.getcwd(),"Output"))
        else:
            cls.workdirectory = os.path.abspath(os.path.join(directory,"Output"))
        if not os.path.isdir(cls.workdirectory):
            os.makedirs(cls.workdirectory)
                
class RequestHandler:
    def GET(self):
        return "URL not set"
    def POST(self):
        return "URL not set"
    def PUT(self):
        return "URL not set"
    def DELETE(self):
        return "URL not set"

class UpdateBaseline:
    def GET(self):
        rawdata = web.input()
        os.chdir(Constants.workdirectory)
        try:
            data = Utils.get_dict_from_json(rawdata.data)
            print data
            suitename = data["suite_name"]
            svnflag = True if data.get("svnlink") and data.get("comment") else False
            baseline_paths = os.path.split(os.path.join(data["baseline_path"].replace("\\\\","\\"),suitename))
            output_paths = os.path.split(os.path.join(data["output_path"].replace("\\\\","\\"), suitename))
            helper = SSHHelper("localhost")
            if not data.get("ci_link"):
                ci_link = None
                baseline_path = Utils.get_filestr(baseline_paths)
                os.chdir(baseline_path)
            else:
                ci_link = data["ci_link"]
                job_name = ci_link.split("/")[-3]
                work_path = Utils.get_filestr(job_name)
                baseline_path = os.path.join(work_path, baseline_paths[-1])
                if os.path.exists(baseline_path):
                    os.chdir(baseline_path)
                    result = helper.exe_cmd("svn up . --username=%s --password=%s" % (SVNAccount.username, SVNAccount.password),printcmd=False)
                    if result.code != 0:
                        raise Exception("svn up failed")
                else:
                    os.chdir(work_path)
                    result = helper.exe_cmd("svn co %s --username=%s --password=%s" % (data["svnlink"],SVNAccount.username, SVNAccount.password),printcmd=False)
                    if result.code != 0:
                        raise Exception("svn checkout failed")
                    os.chdir(baseline_path)
                baseline_paths = os.path.split(baseline_path) + [suitename]
            base_filename = suitename + ".base"
            baseline_caselist = Utils.get_json_from_file(baseline_paths, base_filename)
            if not ci_link:
                output_caselist = Utils.get_json_from_file(output_paths, base_filename)
            else:
                ci_basefile = ci_link+"/"+suitename+"/"+base_filename
                api = Request(method="GET", base_url=ci_basefile)
                resp, content = api.send()
                if resp["status"]!="200":
                    return "Invalid CI link %s" % ci_basefile
                output_caselist = Utils.get_dict_from_json(content)
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
                result = helper.exe_cmd("svn add . --force")
                if result.code != 0:
                    raise Exception("svn add failed")
                result = helper.exe_cmd('''svn ci . -m "%s"''' % data["comment"])
                if result.code != 0:
                    raise Exception("svn checkin failed")
            web.ctx.headers = [("Access-Control-Allow-Origin","*")]
            return 'Update Successful'
        except Exception, e:
            return "Problem on updating: %s" % str(e)
    
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
        os.chdir(Constants.workdirectory)
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
    Constants.setup(options.output)
    urls = (
            '/update_baseline', "UpdateBaseline",
            '/qr_decode', "QRDecode",
            '^.*', 'RequestHandler'
            )
    app = web.application(urls, globals())
    sys.argv[1:] = ["%s" % (str(options.port))]
    app.run()
    
main(sys.argv)