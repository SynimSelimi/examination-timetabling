import json, re
import re
from collections import OrderedDict
try:
    import coloredlogs
    coloredlogs.install()
except ImportError:
    pass

def un_camel(input):
    output = [input[0].lower()]
    for c in input[1:]:
        if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            output.append('_')
            output.append(c.lower())
        else:
            output.append(c)
    return str.join('', output)

class EventAssignment(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, un_camel(k), kwargs[k])
        if not hasattr(self, 'room'):
            self.room = None
    
    def __repr__(self):
        return "<{} {} {} {}>".format(self.exam, self.part, self.period, self.room)    

class Solution(object):
    '''Class representing a problem solution'''

    formats = ['json', 'sol']
    '''List of available formats (str)'''

    default_format = formats[0]
    '''Default format (str)'''
    
    def __init__(self, sol_content, sol_format, instance):
        '''Loads a solution object from the solution content as a set of assignments'''
        self.computed_cost = None

        if sol_format not in self.formats:
            raise ValueError('Unsupported solution format {}. Try one of {} instead'.format(sol_format, '{' + ','.join(map(str,self.formats)) + '}'))

        if sol_format == 'json':
            try:
                data = json.loads(sol_content)
                self.assignments = OrderedDict([(a.get('Course'), sorted([EventAssignment(**e) for e in a.get('Events')], key=lambda e: e.exam)) for a in data.get('Assignments', [])])  
                self.timetable = []              
                for event in instance.events:
                    e = next(filter(lambda e: e.exam == event.exam and e.part == event.part, self.assignments[event.course]))   
                    if e.room is not None:
                        for i, r in enumerate(instance.ordered_rooms):
                            if r.name == e.room:
                                break
                        room = i
                    else:
                        room = len(instance.ordered_rooms)
                    self.timetable.append((e.period + 1, room + 1))
            except Exception as e:
                raise ValueError(str(e))