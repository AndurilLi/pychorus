'''
Created on Jan 16, 2012

@author: mxu, Anduril
@target: Provide logserver and basic logformat
'''
import logging, os, sys
import Utils

class LogType:
    ChorusCore = "ChorusCore"
    Script = "Script"
    Request = "Request"

class Formatter:
    Console = "%(levelname)s - %(message)s"
    ChorusCore = "%(asctime)s - %(name)s - {%(pathname)s:%(lineno)d} - %(levelname)s - %(message)s"
    Script = "%(asctime)s - %(levelname)s - %(message)s - {%pathname)s:%(lineno)d}"
    Request = "-----------------\nREQUEST DETECTED - %(method)s - %(url)s \nREQUEST_HEADERS: %(requestheaders)s \nREQUEST_BODY: %(requestbody)s \
    \nREQUEST_PARAMETERS: %(parameters)s \
    \n\nRESPONSE_STATUS: %(status)s \nRESPONSE_BODY: %(responsebody)s \
    \n\nCall-in IP Address: %(remote_address)s \
    \n-----------------\n"

    
class Level:
    notset = logging.NOTSET
    debug = logging.DEBUG
    info = logging.INFO
    warning = logging.WARNING
    error = logging.ERROR
    critical = logging.CRITICAL

class LogServer:
    filehandler=[]
    def __init__(self,name=LogType.ChorusCore,level=Level.debug,
                formatter=Formatter.Console, colorconsole = False):
        rootlogger = logging.getLogger()
        rootlogger.setLevel(Level.notset)
        self.logger=logging.getLogger(name)
        self.logger.setLevel(Level.notset)
        self.add_consolehandler(level, formatter, colorconsole)

    def get_logger(self):
        return self.logger
    
    def add_consolehandler(self,level=Level.debug,
                    formatter=Formatter.ChorusCore, colorconsole = False):
        if not colorconsole:
            self.consolehandler=logging.StreamHandler(stream = sys.stdout)
        else:
            self.consolehandler=ColoredConsoleHandler(stream = sys.stdout)
        self.consolehandler.setFormatter(logging.Formatter(formatter))
        self.consolehandler.setLevel(level)
        self.logger.addHandler(self.consolehandler)
    
    def add_filehandler(self,level=Level.debug,
                    formatter=Formatter.ChorusCore,
                    filepath=None,filename=None):
        if filename is None or filepath is None:
            raise Exception("Invalid Log file path %s and name %s" % (filepath,filename))
        logfile = os.path.join( filepath, filename)
        handler=logging.FileHandler(logfile)
        handler.setFormatter(logging.Formatter(formatter))
        handler.setLevel(level)
        self.logger.addHandler(handler)
        self.filehandler.append(handler)
        
    def flush_console(self):
        self.consolehandler.flush()
    
    def close_logger(self):
        self.consolehandler.flush()
        self.logger.removeHandler(self.consolehandler)
        self.consolehandler.close()
        for handler in self.filehandler:
            handler.flush()
            self.logger.removeHandler(handler)
            handler.close()

class ColoredConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        # Need to make a actual copy of the record
        # to prevent altering the message for other loggers
        myrecord = Utils.create_entity(record)
        levelno = myrecord.levelno
        if(levelno >= 50):  # CRITICAL / FATAL
            color = '\x1b[31m'  # red
        elif(levelno >= 40):  # ERROR
            color = '\x1b[31m'  # red
        elif(levelno >= 30):  # WARNING
            color = '\x1b[33m'  # yellow
        elif(levelno >= 20):  # INFO
            color = '\x1b[32m'  # green
        elif(levelno >= 10):  # DEBUG
            color = '\x1b[35m'  # blue
        else:  # NOTSET and anything else
            color = '\x1b[0m'  # normal
        myrecord.msg = color + str(myrecord.msg) + '\x1b[0m'  # normal
        logging.StreamHandler.emit(self, myrecord)