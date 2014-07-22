# pychorus

A test framework for mobile, web and server integration test

## Installation

```
>>pip install ChorusCore
```

## Create a project

```
>>chorussetup chorusproject
```

## Launch

```
>>cd chorusproject
>>chorusrun
```

## Modify Config file

```
>>chorusmodify -c default.cfg -s MYENV -k Scope -v Sanity,Regression
will change default.cfg file MYENV section key Scope value to "Sanity,Regression"
```

## Supported assertions:

### All unittest assertions

### Internal assertions which will save baseline

```python
>>assertBool(name, content, levels)
>>assertData(name, content, levels)
>>assertDataOnFly(name, data1, data2, levels, cptype)
>>assertHTTPResponse(name, response, levels, logic)
>>assertImageData(name, imagedata, levels, image_logic, imagetype)
>>assertScreenShot(name, driver, levels, image_logic, imagetype, elements, coordinates)
>>assertText(name, content, levels, logic)
```

## Useful Tips

1. chorusrun --color\n

It will give a colorful logs in command line, based on different log level.

2. chorusrun -e MYENV

It will reload the environment to MYENV, and related keys in MYENV section will be reloaded in configinfo

3. You may use "from ChorusCore import ChorusGlobals" to load global variables

4. You may modify chorusrun.py to redesign the project preparation

5. You may use "from ChorusCore import Utils" to import some common useful functions

6. ChorusCore.APIManagement and ChorusCore.DBOperation will provide HTTPAPI and MySQL basic functions support

7. You may create Performance report by below lines:

```
>>from ChorusCore.PerformanceManagement import Performance_Result
>>Performance_Result.add(name, status, detail, time_taken)
```

If there Performance_Result.data is not empty, then it will generate Performance.html in the Output folder

8.. You may generate your own log file by below lines:

```python
>>from ChorusCore.ProjectConfiguration import ProjectConfiguration
>>from ChorusCore.LogServer import Level
>>proj = ProjectConfiguration()
>>proj.set_logserver(level=Level.debug)
>>proj.logserver.add_filehandler(level=Level.error, filepath = <filepath>, filename = "error.log")
```