'''
Created on Aug 4, 2014

@author: pli
'''
import web, sys, os, optparse
import Utils
from SSHHelper import SSHHelper
from APIManagement import Request

class SVNAccount:
    username = None
    password = None
    
    @classmethod
    def setup(cls, username, password):
        cls.username = username
        cls.password = password

class UpdateBaseline:
    def GET(self):
        rawdata = web.input()
        cwd = os.getcwd()
        try:
            data = Utils.get_dict_from_json(rawdata.data)
            print data
            suitename = data["suite_name"]
            svnflag = True if data.get("svnlink") and data.get("comment") else False
            baseline_paths = data["baseline_path"].replace("\\\\","\\").split(os.path.sep) + [suitename]
            if not data.get("ci_link"):
                output_paths = data["output_path"].replace("\\\\","\\").split(os.path.sep) + [suitename]
                ci_link = None
            else:
                helper = SSHHelper("localhost")
                ci_link = data["ci_link"]
                job_name = ci_link.split("/")[-3]
                work_path = Utils.get_filestr(job_name)
                baseline_path = os.path.join(work_path, baseline_paths[-2])
                if os.path.exists(baseline_path):
                    os.chdir(baseline_path)
                    helper.exe_cmd("svn up .")
                else:
                    helper.exe_cmd("svn co %s --username=%s --password=%s" % (data["svnlink"],SVNAccount.username, SVNAccount.password),printcmd=False)
                    os.chdir(baseline_path)
                baseline_paths = baseline_path.split(os.path.sep) + [suitename]
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
                    image_name = output_caselist[casename][assertionname]["image_name"]
                    self.copy_image(suitename, image_name, baseline_paths, ci_link)
                if not baseline_caselist.get(casename):
                    baseline_caselist[casename] = {}
                baseline_caselist[casename][assertionname] = output_caselist[casename][assertionname]
            Utils.dump_dict_to_file(baseline_caselist, baseline_paths, base_filename)
            if svnflag:
                pass
            return 'Update Successful'
        except Exception, e:
            return "Problem on updating: %s" % str(e)
        finally:
            os.chdir(cwd)
    
    def copy_image(self, suitename, image_name, baseline_paths, ci_link):
        if not ci_link:
            image_path = Utils.get_filestr(baseline_paths, image_name)
            os.remove(image_path)
            ci_basefile = ci_link+"/"+suitename+"/"+image_name
            api = Request(method="GET", base_url=ci_basefile)
            pass
    
class QRDecode:
    def POST(self):
        #TODO
        rawdata = web.input(f="")
        print rawdata
        return '{"status":"OK"}'

def main(argv = sys.argv):
    parser = optparse.OptionParser()
    parser.add_option("--port", dest="port", default="8080", help="Chorus Server Port")
    parser.add_option("-u", "--username", dest="username", help="svn username")
    parser.add_option("-p", "--password", dest="password", help="svn password")
    options, argv = parser.parse_args(list(argv))
    SVNAccount.setup(options.username, options.password)
    urls = (
            '/update_baseline', "UpdateBaseline",
            '/qr_decode', "QRDecode"
            )
    app = web.application(urls, globals())
    sys.argv[1:] = ["0.0.0.0:%s" % (str(options.port))]
    app.run()