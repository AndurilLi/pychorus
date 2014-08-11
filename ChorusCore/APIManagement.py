'''
Created on May 13, 2013

@author: mxu, modified by Anduril
'''
import httplib2, urllib, json,time, base64
import Utils
import copy,os
import importlib
import ChorusGlobals
from ChorusConstants import CommonConstants
import traceback
class RequestMode:
    www_form = "application/x-www-form-urlencoded"
    multi_form = 'multipart/form-data; boundary=%s'
    
class ResponseType:
    text_xml = "text/xml"
    text_plain = "text/plain"
    text_html = "text/html"
    application_xml = "application/xml"
    application_json = "application/json"

class Request:
    '''Generate a simple request template, it contains multiple functions'''
    def __init__(self,
                 url = None, 
                 method = None, 
                 url_parameters = None, 
                 parameters = None, 
                 headers = {}, 
                 body = None,
                 ignored_keys = None,
                 header_keys = None,
                 base_url = None,
                 follow_redirects = True,
                 mode = None,
                 upload_files = {},
                 credentials = None,
                 timeout = None):
        self.logger = ChorusGlobals.get_logger()
        if base_url:
            base_url = base_url
        else:
            try:
                base_url = ChorusGlobals.get_baseurl()
            except Exception, e:
                traceback.print_exc()
                self.logger.critical("Cannot initiate global baseurl, error: %s" % str(e))
                raise Exception("Cannot initiate global baseurl, error: %s" % str(e))
             
        if not url:
            self.url = base_url
            self.endpoint = base_url
        else:
            self.endpoint = url
            if base_url.endswith("/") and url.startswith("/"):
                self.url = base_url[0:-1] + url
            elif (not base_url.endswith("/")) and (not url.startswith("/")):
                self.url = base_url + "/" + url
            else:
                self.url = base_url + url
            
            

        if not method:
            self.logger.critical("Not define http method")
            raise Exception("Not define http method")
        else:
            self.method = method
            
        self.url_parameters = url_parameters
        self.parameters = parameters
        if headers:
            self.headers = {}
            for key,value in headers.items():     
                self.headers[key.lower()] = value
        else:
            self.headers = {}
        self.body = body
        self.ignored_keys = ignored_keys
        self.header_keys = header_keys
        self.cert = None
        self.key = None
        self.cert_domain = ''
        self.follow_redirects=follow_redirects
        self.proxy_host=None
        self.proxy_port=None
        self.proxy_type=None
        if mode:
            self.set_request_mode(mode)
        else:
            self.mode = None
        self.upload_files = upload_files
        self.credentials = credentials
        self.timeout = timeout
    
    def set_request_mode(self, header_mode):
        self.headers["content-type"] = header_mode
        self.mode = header_mode
        
    def set_response_type(self, header_type):
        self.headers["accept"] = header_type
    
    def enable_proxy(self,proxy_host,proxy_port,proxy_type,proxy_rdns=None,proxy_user=None,proxy_pass=None):
        '''HTTP=3,SOCKS4=1,SOCKS5=2'''
        self.proxy_type=int(proxy_type)
        self.proxy_host=proxy_host
        self.proxy_port=int(proxy_port)
        self.proxy_rdns=proxy_rdns
        self.proxy_user=proxy_user
        self.proxy_pass=proxy_pass
                
        
    def add_certificate(self, key_file, cert_file, domain = None):
        self.key = key_file
        self.cert = cert_file  
        if domain:
            self.cert_domain = domain
        
          
    def ShowURL(self,status):
        if self.parameters:
            params = urllib.urlencode(self.parameters)
            url = "?".join([self.url,params])
        else:
            url = self.url
        message={'status':status,
                'method':self.method,
                'URL':url,
                'body':self.body,
                'headers':self.headers,
                'ignored_keys':self.ignored_keys,
                "redirects":self.follow_redirects}
        del_para={}
        for m in message:
            if not message[m]:
                del_para[m]=True
        for n in del_para:
            del(message[n])
        return message
    
    def adjust_postbody(self):
        '''added by Anduril, adjust body for different request type'''
        if not self.mode:
            if isinstance(self.body, dict):
                body = json.dumps(self.body)
            else:                
                body = self.body
        else:
            if self.mode == RequestMode.www_form:
                body = urllib.urlencode(self.body)
            elif self.mode == RequestMode.multi_form:
                boundary = Utils.get_random_str(16)
                body = self.encode_multipart_formdata(boundary)
        return body
    
    def encode_multipart_formdata(self, boundary):
        '''added by Anduril, for multi part http request'''
        import mimetypes
        boundary = "--------------------"+boundary
        self.headers["content-type"] = self.mode % boundary
        CRLF = "\r\n"
        tempbody = []
        if self.body and isinstance(self.body, dict):
            for key, value in self.body.items():
                tempbody.append("--"+boundary)
                tempbody.append('Content-Disposition: form-data; name="%s"' % key)
                tempbody.append('')
                tempbody.append(value)
        if self.upload_files:
            for key, filepath in self.upload_files.items():
                try:
                    filename = os.path.basename(filepath)
                    filetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
                    filedata = open(filepath,'rb').read()
                    tempbody.append("--"+boundary)
                    tempbody.append('Content-Type: %s' % filetype)
                    tempbody.append('Content-Transfer-Encoding: binary')
                    tempbody.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key,filename))
                    tempbody.append('')
                    tempbody.append(filedata)
                except Exception,e:
                    self.logger.error("Cannot open file at %s" % filepath)
                    self.logger.error("Open error %s" % str(Exception)+str(e))
                    continue
        tempbody.append('--'+boundary+"--")
        tempbody.append('')
        body = CRLF.join(tempbody)
        return body
    
    def send(self):
        '''
        self.result is used for api comparison
        self.response is the responsed data returned
        Make sure use the output correctly
        '''
        if '%s' in self.url:
            if self.url_parameters==None:
                self.logger.critical("url and it's parameters don't match")
                raise Exception("url and it's parameters don't match")

            self.url = self.url % self.url_parameters
        
        
        if self.parameters:
            params = urllib.urlencode(self.parameters)
            url = "?".join([self.url,params])
            params_for_read = []
            for key,value in self.parameters.items():
                params_for_read.append(str(key)+"="+str(value))
            url_for_read = self.url+"?"+"&".join(params_for_read)
        else:
            url_for_read = self.url
            url = self.url
            
        self.realbody = self.adjust_postbody()

        self.logger.info(self.method.upper() + ' - ' + url)
        
        try:
            if self.proxy_host and self.proxy_port and self.proxy_type:
                proxy=httplib2.ProxyInfo(self.proxy_type,self.proxy_host,self.proxy_port,self.proxy_rdns,self.proxy_user,self.proxy_pass)
                http = httplib2.Http(proxy_info=proxy,disable_ssl_certificate_validation=True)
            else:
                http = httplib2.Http(disable_ssl_certificate_validation=True)
            if self.cert and self.key:
                http.add_certificate(self.key, self.cert, self.cert_domain)
            if self.credentials:
                http.add_credentials(self.credentials["name"], self.credentials["password"], 
                                     self.credentials["domain"])
                
            http.follow_redirects=self.follow_redirects
            starttime = time.time()
            resp, content = http.request(url,
                                     self.method.upper(),
                                     headers = self.headers,
                                     body = self.realbody                                 
                                     )
            endtime = time.time()
            self.time_taken = Utils.round_sig(endtime-starttime)
        except Exception, e:
            traceback.print_exc()
            self.logger.critical("Call %s exception %s:%s" % (self.url,str(Exception),str(e)))
            raise Exception("Call %s exception %s:%s" % (self.url,str(Exception),str(e)))
            
        try:
            content_dict = Utils.get_dict_from_json(content)
        except:
            content_dict = content
        
        result = {}
        
        if self.ignored_keys:
            Utils.del_dict_keys(content_dict, self.ignored_keys)
            
        headers = {}
        if self.header_keys:
            for item in self.header_keys:
                if resp.has_key(item):
                    headers[item] = resp[item]
                else:
                    self.logger.critical("No such headers %s in %s response" % (item, url_for_read))
            if headers:
                result['headers'] = headers
        result['status'] = resp['status']
        result['data'] = content_dict
        newresp = {}
        for key in resp:
            newresp[key]=resp[key]
        self.result = result
        self.response = Response(response_data = content_dict, response_header = newresp, status = ' '.join([str(resp.status), resp.reason]),url = url_for_read)
        self.jsdata = self.generate_detail()
        if self.timeout and str(self.timeout).isdigit() == True:
            from PerformanceManagement import Performance_Result
            Performance_Result.add(self.endpoint, self.jsdata, self.time_taken, self.timeout)
        return self
    
    def generate_detail(self):
        if self.mode:
            body = {
                        "mode": self.mode,
                        "uploaded_files": self.upload_files,
                        "body_para":self.body
                    }
        else:
            body = self.realbody
        try:
            json.dumps(body)
            reqbody = body
        except:
            reqbody = base64.b64decode(body)
        try:
            json.dumps(self.response.data)
            respbody = self.response.data
        except:
            respbody = base64.b64decode(self.response.data)
        try:
            api = {
                        "url": self.response.url,
                        "method" : self.method,
                        "request_parameters" : self.parameters,
                        "request_headers" : self.headers,
                        "request_body":  reqbody,
                        "response_headers": self.response.headers,
                        "response_body": respbody,
                        "response_status": self.response.status,
                        "time_taken": self.time_taken
                    }
            return json.dumps(api)
        except:
            self.logger.error("json dumps error %s" % str(api))
            return json.dumps({
                                "url": self.response.url,
                                "method" : self.method,
                                "request_parameters" : self.parameters,
                                "time_taken": self.time_taken
                               })
 
class Response:
    '''Provide a class to handle response'''
    def __init__(self, response_data = None, response_header = None, status = None, header_keys = None, ignored_keys = None, url = None):
        self.data = response_data
        self.headers = response_header
        self.status = status    
        self.url = url
    
class HTTP_API:
    '''
    Base class to handle http test objects
    '''


    def __init__(self, template = None, ignored_keys = None, header_keys = None, template_path = None, follow_redirects = True):
        '''
        Init
        '''
        self.logger = ChorusGlobals.get_logger()
        if template:
            if template_path:
                req, resp = self.load_template(template,
                                               ignored_keys,
                                                header_keys, 
                                                template_path,
                                                follow_redirects = follow_redirects)
            else:
                req, resp = self.load_template(template, 
                                           ignored_keys = ignored_keys, 
                                           header_keys = header_keys,
                                           follow_redirects = follow_redirects)
            
            self.request = req
            
            self.response = resp

        else:
            self.request = None
            self.response = None
        
    def load_template(self, template, ignored_keys = None, header_keys = None, path = None, follow_redirects = True ):
        '''
        if path is not specified, only first template found can be loaded
        '''
        try:
            filename = '%s.%s' % (CommonConstants.APITEMPLATE_FOLDER, template)
            obj = importlib.import_module(filename)
#            obj = __import__(filename, globals(), locals(), [template,''], -1)
        except Exception,e:
            traceback.print_exc()
            self.logger.critical("Cannot load template %s, errors: %s" % (template,str(e)))
            raise Exception("Cannot load template %s, errors: %s" % (template,str(e)))
        if not obj:
            self.logger.critical("No api templates found!")
            raise Exception("No api templates found!")
            
        if not hasattr(obj, "url"):
            self.logger.critical("url is not defined")
            raise Exception("url is not defined")
        
        if not hasattr(obj, "method"):
            self.logger.critical("method is not defined")
            raise Exception("method is not defined")     
            
        req = Request(
                      obj.url,
                      obj.method,
                      copy.deepcopy(obj.url_parameters) if hasattr(obj, "url_parameters") else None,
                      copy.deepcopy(obj.parameters) if hasattr(obj, "parameters") else None,
                      copy.deepcopy(obj.headers) if hasattr(obj, "headers") else None,
                      copy.deepcopy(obj.body) if hasattr(obj, "body") else None,
                      ignored_keys if ignored_keys else copy.deepcopy(obj.ignored_keys) if hasattr(obj, "ignored_keys") else None,
                      header_keys if header_keys else copy.deepcopy(obj.header_keys) if hasattr(obj, "header_keys") else None,                
                      follow_redirects = follow_redirects,
                      mode = copy.deepcopy(obj.mode) if hasattr(obj, "mode") else None,
                      upload_files = copy.deepcopy(obj.upload_files) if hasattr(obj, "upload_files") else {}
                      )
        
        if not hasattr(obj, "response_data") and not hasattr(obj, "status"):
            resp = None
        else:
            resp = Response(
                            copy.deepcopy(obj.response_data) if hasattr(obj, "response_data") else None,
                            copy.deepcopy(obj.status) if hasattr(obj, "status") else None
                            )
        return req, resp
