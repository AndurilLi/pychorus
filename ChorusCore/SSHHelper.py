'''
Created on Jul 26, 2014

@author: pli
'''
import paramiko,traceback
from subprocess import Popen,PIPE,STDOUT
import sys
import threading
import os
import time

class SSHHelper:
    LOG_FILENAME = "ssh_paramiko.log"
    def __init__(self, ip, host_name = '', host_pwd = '', paramiko_logpath=""):
        '''Check IP address, prepare log filepath'''
        self.check_ip(ip)
        self.host_name = host_name
        self.host_pwd = host_pwd
        if paramiko_logpath:
            if os.path.isdir(paramiko_logpath):
                self.paramiko_logpath = os.path.join(paramiko_logpath, self.LOG_FILENAME)
            else:
                sys.stderr.write("Invalid paramiko_logpath")
                sys.exit(1)
        else:
            self.paramiko_logpath = "ssh_paramiko.log"
        
    def check_ip(self, ip):
        '''Check remote IP address, if it's local, then change ip to localhost, and mark remoteflag to False'''
        import socket
        local_name = socket.gethostname()
        local_ip = socket.gethostbyname(local_name)
        if ip.find(local_name) == 0:
            ip = ip.replace(local_name, "localhost")
        elif ip.find(local_ip) == 0:
            ip = ip.replace(local_ip, "localhost")
        self.ip = ip
        self.remote_flag = True if self.ip.find("localhost")!=0 else False
    
    def connect(self, hostkey=None):
        '''Connect ssh machine, if localhost then skip'''
        if self.remote_flag:
            try:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if hostkey:
                    self.ssh.load_host_keys(hostkey)
                paramiko.util.log_to_file(self.paramiko_logpath)
                self.ssh.connect(self.ip, username = self.host_name, password = self.host_pwd)
            except paramiko.AuthenticationException:
                sys.stderr.write("Authentication failed when connecting to %s" % self.host) 
                sys.exit(1)
            except Exception,e :
                traceback.print_exc()
                sys.stderr.write('cannot ssh connect to %s. error happens %s' %(self.ip,str(e))) 
                sys.exit(1)
            print "Server %s connected" % self.ip
        else:
            print "Localhost doesn't need to connect"
            
    def disconnect(self):
        '''Disconnect ssh machine, if localhost then skip'''
        if self.remote_flag and hasattr(self,"ssh"):
            try:
                self.ssh.close()
                del self.ssh
            except Exception,e :
                traceback.print_exc()
                sys.stderr.write('cannot ssh disconnect to device. %s' %(str(e)))
                sys.exit(1)
            print "Server %s disconnected" % self.ip
        else:
            print "Localhost doesn't need to disconnect"
    
    def start_blocking_session(self, cmd, logfilepath=None):
        '''Start a blocking session, by default the log will write to the console, 
        if input the logfilepath, then the log will also be print as a file'''
        if self.remote_flag:
            if not hasattr(self,"ssh"):
                sys.stderr.write("please connect first, and then to do execution")
                sys.exit(1)
            session = SSH_Blocking_Session(self.ssh, cmd, logfilepath)
            session.start()
        else:
            session = Local_Blocking_Session(cmd, logfilepath)
            session.start()
        time.sleep(7)
        if session.isAlive():
            return session
        else:
            sys.stderr.write("Cannot start session with %s" % cmd)
            sys.exit(1)
    
    def close_blocking_session(self, session, cmd="\x03Y\n"):
        '''default ssh close command is ctrl-C then Y and enter,
        For local session, it will use psutil to find child process and terminate'''
        session.stop(cmd)
    
    def get_system_type(self):
        '''return the operation system type'''
        platform = self.exe_cmd("uname -s", True)
        if platform.code == 0:
            return platform.stdout
        else:
            platform = self.exe_cmd("ver", True)
            if platform.find("Windows")!=-1:
                return "Windows"
            sys.stderr.write("Cannot get platform version")
            return None
              
    def exe_cmd(self, cmd, combine_error=False, nbytes=65536, shell = None, printcmd = True):
        '''execute a non-blocking command, can return 65536 byte by default'''
        if printcmd:
            print cmd
        if self.remote_flag:
            if not hasattr(self,"ssh"):
                sys.stderr.write("please connect first, and then to do execution")
                sys.exit(1)
            self.session = self.ssh.get_transport().open_session()
            if combine_error:
                self.session.set_combine_stderr(True)
            self.session.exec_command(cmd)
            while not self.session.exit_status_ready():
                pass
            output = CommandResult(self.session.recv(nbytes),
                                   None if combine_error else self.session.recv_stderr(nbytes),
                                   self.session.recv_exit_status())
        else:
            if shell:
                self.shelltype = shell
            else:
                self.shelltype = True if (sys.platform.startswith("win") or sys.platform.startswith("darwin")) else False
            popen_stderr = STDOUT if combine_error else PIPE
            self.session = Popen(cmd,shell=self.shelltype, stdin=PIPE,stdout=PIPE,stderr=popen_stderr)
            self.session.wait()
            output = CommandResult(self.session.stdout.read(),
                                   None if combine_error else self.session.stderr.read(),
                                   self.session.returncode)
        return output

class CommandResult:
    '''command execution default template'''
    def __init__(self, stdout, stderr, code):
        self.stdout = stdout.strip()
        self.stderr = stderr.strip() if stderr else ""
        self.code = code

class Local_Blocking_Session(threading.Thread):
    def __init__(self, cmd, logfilepath=None):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.filehandler = open(logfilepath,"wb") if logfilepath else None
        self.shelltype = True if sys.platform.find("win")==0 else False
        
    def run(self):
        self.session = Popen(self.cmd,shell=self.shelltype, stdin=PIPE,stdout=PIPE,stderr=STDOUT)
        while True:
            data = self.session.stdout.readline()
            if not data and self.session.returncode is not None:
                break
            if self.filehandler:
                self.filehandler.write(data)
            print data.strip()
            self.session.poll()
    
    def stop(self, cmd=None):
        '''cmd not use, just keep same as Remote mode'''
        import psutil
        psutil.Process(self.session.pid).get_children()[0].kill()
        if sys.platform.startswith("win"):
            os.system("taskkill /f /im adb.exe")
        self.session.kill()
        self.join()
        if self.filehandler:
            self.filehandler.close()

class SSH_Blocking_Session(threading.Thread):
    def __init__(self, ssh, cmd, logfilepath=None):
        threading.Thread.__init__(self)
        self.ssh = ssh
        self.cmd = cmd
        self.filehandler = open(logfilepath,"w") if logfilepath else None
        
    def run(self):
        print self.cmd
        self.session = self.ssh.get_transport().open_session()
        self.session.set_combine_stderr(True)
        self.session.get_pty()
        self.session.exec_command(self.cmd)
        while not self.session.exit_status_ready():
            if self.session.recv_ready():
                data = self.session.recv(65536) 
                if self.filehandler:
                    self.filehandler.write(data)
                print data.strip()

    def stop(self, cmd="\x03Y\n"):
        self.session.send(cmd)
        self.join()
        if self.filehandler:
            self.filehandler.close()