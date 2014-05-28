'''
Created on Mar 10, 2014

@author: mxu
'''
import sys, os
import Utils

def copy_sample_folder(foldername):
    current_dir_abs = os.path.abspath(os.path.dirname(__file__))
    sampler_folder = os.path.join(current_dir_abs, "Samples")
    output_dir_abs = os.getcwd()
    output_folder = os.path.join(output_dir_abs, foldername)
    Utils.copy_folder(sampler_folder, output_folder)

def main(argv=sys.argv):
    current_dir_abs = os.getcwd()
    sys.path.append(current_dir_abs)

    if len(sys.argv)==1:
        foldername = "chorus_project"
    elif len(sys.argv)==2 and not sys.argv[1].startswith("-") and sys.argv[1].find("help")==-1:
        foldername = sys.argv[1]
    else:
        print "please enter the folder name after chorussetup. E.g. chorussetup <foldername>."
        print "It will generate a chorus_project folder by default."
        sys.exit(2)

    copy_sample_folder(foldername)
    print "Generate a <%s> folder for sample chorus project successfully." % foldername
    print "To execute the project, just run 'chorusrun'. It will generate a HTML report in the Output folder"
    