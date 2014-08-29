'''
Created on Mar 9, 2014

@author: Anduril
'''
from setuptools import setup

setup(
        name = "ChorusCore",
        version = "1.0.001",
        description = "A test framework based on unittest, support baselines assertion, give pretty html report",
        author = "Anduril, mxu",
        author_email = "yjckralunr@gmail.com",
        packages = ['ChorusCore'],
        zip_safe = False,
        include_package_data = True,
        install_requires = [
                                'httplib2>=0.8',
                                'Jinja2>=2.6',
                                'mysql-connector-python>=1.1.6,<1.1.7',
                                'pycrypto>=2.6,<2.7',
                                'Pillow>=2.5.1',
                                'paramiko',
                                'psutil',
                                "web.py"
                            ],
        entry_points = {"console_scripts":['chorusrun=ChorusCore.RunTest:main',
                                           'chorussetup=ChorusCore.CreateSamples:main',
                                           'chorusmodify=ChorusCore.RunTest:modify_config',
                                           'chorusserver=ChorusCore.ChorusServer:main']},
        url = "https://github.com/ChorusCore/"
      )
