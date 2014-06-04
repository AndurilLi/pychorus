'''
Created on Mar 23, 2014

@author: Anduril
@target: provide Perofrmance result
'''
import time, json
import Utils
from functools import wraps
import ChorusGlobals

class Performance_Object:
    def __init__(self, name, status, detail, time_taken):
        self.name = name
        self.status = status
        self.detail = detail
        self.time_taken = Utils.round_sig(time_taken)
        
class Performance_Result:
    data = []
    status = True
    number = 0
    @classmethod
    def add(cls, name, detail, time_taken, timeout=30):
        status = True if time_taken <= timeout else False
        if not status:
            cls.status = False
        js_detail = cls.generate_json(detail)
        cls.data.append(Performance_Object(name, status, js_detail, time_taken))
        ChorusGlobals.get_logger().info("Add Performance Result %s, status %s, time_taken %s" % (name, status, str(time_taken)))
        cls.number += 1
    
    @staticmethod
    def generate_json(detail):
        try:
            finaldetail = Utils.parse_description(detail) if type(detail)==str else detail
            jsdata = json.dumps(finaldetail)
        except Exception,e:
            message = "The input detail cannot be transfer into json type, error is %s" % str(e)
            ChorusGlobals.get_logger().warning(message)
            jsdata = json.dumps({"message":message})
        return jsdata
        
def EAFlag(name=None, detail=None, timeout=30):
    def _eawrapper(func):
        def __wrapper(*args, **kwargs):
            final_name = func.__name__ if not name else name
            final_detail = func.__doc__ if not detail else detail
            start_time = time.time()
            response = func(*args, **kwargs)
            end_time = time.time()
            time_taken = Utils.round_sig(end_time-start_time, 3)
            Performance_Result.add(final_name, final_detail, time_taken, timeout)
            return response
        return wraps(func)(__wrapper)
    return _eawrapper