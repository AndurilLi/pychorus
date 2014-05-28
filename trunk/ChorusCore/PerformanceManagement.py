'''
Created on Mar 23, 2014

@author: Anduril
@target: provide Perofrmance result
'''
import Utils
class Performance_Object:
    def __init__(self, name, status, detail, time_taken):
        self.name = name
        self.status = status
        self.detail = detail
        self.time_taken = Utils.round_sig(time_taken*1000)
        
class Performance_Result:
    data = []
    number = 0
    @classmethod
    def add(cls, name, status, detail, time_taken):
        cls.data.append(Performance_Object(name, status, detail, time_taken))
        cls.number += 1
        
a=1