'''
Created on May 4, 2014

@author: Anduril
'''
import jpype,os

def start(jarfilenames, jarfilepath=""):
    '''jarfilenames=[jarfilename1, jarfilename2...], jarfilepath is the same format as os.path.join()'''
    classpath = []
    if jarfilepath and not os.path.isdir(jarfilepath):
        raise Exception("Cannot load filepath %s" % jarfilepath)
    rootpath = os.getcwd()
    fullpath = os.path.join(rootpath, jarfilepath)
    for filename in jarfilenames:
        filepath = os.path.join(fullpath, filename)
        if os.path.isfile(filepath):
            classpath.append(filepath)
        else:
            raise Exception("File %s doesn't existed" % filepath)
    jvmpath = jpype.getDefaultJVMPath()
    jpype.startJVM(jvmpath, "-Djava.class.path=%s" % os.pathsep.join(classpath))
     
def shutdown():
    jpype.shutdownJVM()
        