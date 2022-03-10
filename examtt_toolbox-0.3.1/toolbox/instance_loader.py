import json
from itertools import combinations, product
import math
from collections import defaultdict, OrderedDict, namedtuple
from toolbox.constants import *
from toolbox.minizinc import MiniZincData
import logging
try:
    import coloredlogs
    coloredlogs.install()
except ImportError:
    pass

log = logging.getLogger('costs')

Event = namedtuple('Event', ['course', 'exam', 'part'])

class Course(object):
    def __init__(self, teachers, **kwargs):
        self.name = kwargs.get('Course')
        self.parts = kwargs.get('ExamType').split('And')
        self.number_of_exams = kwargs.get('NumberOfExams')
        self.distances_between_exams = (kwargs.get('MinimumDistanceBetweenExams', 0), kwargs.get('MaximumDistanceBetweenExams', math.inf))
        if kwargs.get('WrittenOralSpecs') is not None:
            self.part_distances = [(kwargs.get('WrittenOralSpecs').get('MinDistance', 0), kwargs.get('WrittenOralSpecs').get('MaxDistance', math.inf))]
            self.same_day = kwargs.get('WrittenOralSpecs').get('SameDay', False)
        else:
            self.part_distances = [(0, math.inf) for _ in range(len(self.parts) - 1)] # in form of (min, max), given for consecutive parts (therefore len(self.parts) - 1)
            self.same_day = False            
        self.rooms = []
        if kwargs.get('RoomsRequested') is not None and kwargs.get('RoomsRequested').get('Number') > 0:
            # assume that the 'Written' is always the first part and the room request refers mainly to that part
            self.rooms.append((kwargs.get('RoomsRequested').get('Type'), kwargs.get('RoomsRequested').get('Number')))
            if len(self.parts) == 2:
                if kwargs.get('WrittenOralSpecs') is not None and kwargs.get('WrittenOralSpecs').get('RoomForOral', False):
                    self.rooms.append(('Small', 1)) # make a duplicate of the room request also for the oral
                else:
                    self.rooms.append(None) # no room required for that part (the oral)
        else:
            self.rooms = [None] * len(self.parts)
            if kwargs.get('WrittenOralSpecs') is not None and kwargs.get('WrittenOralSpecs').get('RoomForOral', False):
                self.rooms[self.parts.index('Oral')] = ('Small', 1)
        _teacher = kwargs.get('Teacher')
        if _teacher not in teachers:
            raise ValueError("Teacher of course {} ({}) is not present in the list of teachers".format(self.name, _teacher))
        self.teacher = _teacher
        self.period_constraints = [defaultdict(lambda: []) for __ in range(len(self.parts))]
        self.room_constraints = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 'Indifferent')))
        self.curricula_primary = set()
        self.curricula_secondary = set()

    def add_to_primary_curriculum(self, curriculum):
        self.curricula_primary.add(curriculum)

    def add_to_secondary_curriculum(self, curriculum):
        self.curricula_secondary.add(curriculum)
        
    def __repr__(self):
        return "Name: {}, {}, Parts: {}, Distances: {}/{}, Rooms: {}".format(self.name, \
            self.number_of_exams, self.parts, self.distances_between_exams, \
            self.part_distances, self.rooms)

class Room(object): 
    def __init__(self, **kwargs):
        self.name = kwargs.get('Room')
        self.type = kwargs.get('Type')
        self.members = set(map(lambda r: r, kwargs.get('Members', [])) )
        self.constraints = {}
        self.global_constraints = None

    def dispatch_composite(self, rooms):
        if self.type != 'Composite':
            return
        _members = set(map(lambda r: rooms.get(r), self.members))
        if None in _members:
            raise ValueError('There are one or more wrong room members in composite room {}'.format(_members))
        self.members = _members
         
    def __repr__(self):
        res = "Room: {}, Type: {}".format(self.name, self.type)
        if self.type == 'Composite':
            return "{}, Members: {}".format(res, self.members)
        else:
            return res

    def compatible_room(self, required_type, quantity):
        if quantity > 1:
            if len(self.members) < quantity:
                return False
            if sum(map(lambda r: r.compatible_room(required_type, 1), self.members)) >= quantity:
                return True
        else:
            # TODO: check if it is meaningful, a composite room is incompatible with a single room request, regardless of the type
            if self.type == 'Composite':
                return False
            if required_type == 'Small':
                return True
            if required_type == 'Medium':
                return self.type != 'Small'
            if required_type == 'Large':
                return self.type == 'Large'
        return False
            

class Instance(object):
    '''Class representing a problem instance of the Graduation Timetabling Problem'''    

    formats = ['json', 'dzn']
    '''List of available formats (str)'''

    default_format = 'json'
    '''Default format (str)'''
     
    @staticmethod
    def un_camel(input):
        output = [input[0].lower()]
        for c in input[1:]:
            if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                output.append('_')
                output.append(c.lower())
            else:
                output.append(c)
        return str.join('', output)
    

    def __init__(self, inst_content, inst_format=None):
        '''Loads an instance object from the instance content as string'''

        if inst_format not in self.formats:
            raise ValueError('Unsupported instance format: ' + str(inst_format) + '. Try one of {' + ','.join(map(str,self.formats)) + '} instead.')

        self.format = inst_format

        if inst_format == 'json':
            data = json.loads(inst_content)    
            self.periods = data.get('Periods')
            self.slots_per_day = data.get('SlotsPerDay')
            self.teachers = set(data.get('Teachers'))   
            self.courses = OrderedDict((c.name, c) for c in map(lambda d: Course(self.teachers, **d), data.get('Courses', [])))
            self.primary_primary_distance = data.get('PrimaryPrimaryDistance', 2 * self.slots_per_day)
            self.primary_secondary_distance = data.get('PrimarySecondaryDistance', self.slots_per_day)
            self.ordered_rooms = list(map(lambda d: Room(**d), data.get('Rooms', [])))
            self.rooms = {r.name: r for r in self.ordered_rooms}
            for r in self.rooms.values():
                r.dispatch_composite(self.rooms)
            self.period_constraints = {}

            # Dispatch all constraints
            for c in data.get('Constraints', []):
                try:
                    _period = c.get('Period')
                    if 'Period' in c.get('Type') and (_period < 0 or _period >= self.periods):
                        raise ValueError("Wrong period {} in constraint {}".format(_period, json.dumps(c)))
                    _level = c.get('Level')
                    if _level not in ("Forbidden", "Undesired", "Preferred"):
                        raise ValueError("Wrong constraint level {} in constraint {}".format(_level, json.dumps(c)))
                    if c.get('Type') == 'EventPeriodConstraint':
                        course = self.courses[c.get('Course')]
                        _parts = [c.get('Part')]
                        # TODO: currently if the part is not present it means all parts
                        if _parts[0] is None:
                            _parts = course.parts
                        elif _parts[0] not in course.parts:
                            raise ValueError("Wrong constraint, part {} is not part of the course {}, {}".format(_parts[0], course.name, json.dumps(c)))
                        for part in _parts:
                            course.period_constraints[course.parts.index(part)][_period].append((c.get('Exam', 1), _level))
                        # TODO: check that there are no multiple constraints for the same course/exam/part/period combination
                    elif c.get('Type') == 'PeriodConstraint':
                        if _period in self.period_constraints:
                            raise ValueError('Multiple PeriodConstraint definitions for the same period')
                        self.period_constraints[_period] = _level
                    elif c.get('Type') == 'RoomPeriodConstraint':
                        room = self.rooms[c['Room']]
                        if _period in room.constraints:
                            raise ValueError('Multiple RoomPeriodConstraint definitions for the same period')
                        room.constraints[_period] = _level
                    elif c.get('Type') == 'EventRoomConstraint':
                        course = self.courses[c.get('Course')]
                        _exams = [c.get('Exam')]
                        # TODO: currently if the exam is not present it means all exams
                        if _exams[0] is None:
                            _exams = list(range(course.number_of_exams))  
                                                                      
                        _parts = [c.get('Part')]
                        # TODO: currently if the part is not present it means all parts
                        if _parts[0] is None:
                            _parts = course.parts
                        elif _parts[0] not in course.parts:
                            raise ValueError("Wrong constraint, part {} is not part of the course {}, {}".format(_parts[0], course.name, json.dumps(c)))
                        for exam, part in product(_exams, _parts):
                            course.room_constraints[c['Room']][exam][course.parts.index(part)] = _level
                    elif c.get('Type') == 'RoomConstraint':
                        room = self.rooms[c['Room']]
                        if room.global_constraints is not None:
                            raise ValueError("Multiple RoomConstraint definitions for the same room")
                        room.global_constraints = _level
                    else:
                        raise ValueError("Wrong constraint type {}".format(c.get('Type')))  
                except Exception as e:
                    print("Constraint {} is wrong {}".format(c, e))
                    raise e
            # Dispatch curricula
            self.curricula = {}
            for q in data.get('Curricula', []):
                self.curricula[q.get('Curriculum')] = {}
                _members = set(map(lambda c: self.courses.get(c), q.get('PrimaryCourses', [])))
                if None in _members:
                    raise ValueError('There are one or more wrong primary courses in curriculum {}: {}'.format(q.get('Curriculum'), c.get('PrimaryCourses')))
                self.curricula[q.get('Curriculum')]['primary'] = _members
                for course in _members:
                    course.add_to_primary_curriculum(q.get('Curriculum'))
                _members = set(map(lambda c: self.courses.get(c), q.get('SecondaryCourses', [])))
                if None in _members:
                    raise ValueError('There are one or more wrong secondary courses in curriculum {}: {}'.format(q.get('Curriculum'), c.get('SecondaryCourses')))
                self.curricula[q.get('Curriculum')]['secondary'] = _members
                for course in _members:
                    course.add_to_secondary_curriculum(q.get('Curriculum'))
        
            # post-processing
            # check room availability
            for course in self.courses.values():
                for part in range(len(course.parts)):
                    if course.rooms[part] is None:
                        continue
                    type, number = course.rooms[part]
                    compatible_rooms = set(filter(lambda r: r.type == type, self.rooms.values()))
                    if len(compatible_rooms) < number:
                        raise ValueError('Course {} requires {} rooms of type {} for {} but only {} are available'.format(course.name, number, type, course.parts[part], len(compatible_rooms)))                                    
                    
            # explicitly compute the set of available periods for each course (not forbidden) 
            for course in self.courses.values():
                # domain consistency: remove forbidden values
            #    start_part = course.parts[0]
                course.available_periods = [[set(range(self.periods)) for __ in range(len(course.parts))] for ___ in range(course.number_of_exams)]
                for part in range(len(course.parts)):
                    for period, constraints in course.period_constraints[part].items():
                        for (exam, level) in constraints:
                            if level != 'Forbidden':
                                continue
                            course.available_periods[exam][part].discard(period)
                # second part of domain consistency: remove periods if not enough rooms are available at that time
                for part in range(len(course.parts)):
                    if course.rooms[part] is None:
                        continue
                    type, number = course.rooms[part]
                    compatible_rooms = set(filter(lambda r: r.type == type, self.rooms.values()))
                    for exam in range(course.number_of_exams):
                        periods_to_remove = []
                        for p in course.available_periods[exam][part]:
                            available_rooms_at_p = sum(1 if r.constraints.get(p) != 'Forbidden' else 0 for r in compatible_rooms)
                            if available_rooms_at_p < number:
                                periods_to_remove.append(p)
                        for p in periods_to_remove:
                                course.available_periods[exam][part].discard(p)
                # third part of domain consistency: if it's a sameday exam, then some periods can be removed
                if course.same_day:
                    parts = len(course.parts)
                    available_slots = [set(range(self.slots_per_day)) for __ in range(parts)]
                    for part in range(parts):
                        for slot in range(self.slots_per_day):
                            if slot < part:
                                available_slots[part].discard(slot)
                            remaining_parts = parts - 1 - part
                            if slot + remaining_parts >= self.slots_per_day:
                                available_slots[part].discard(slot)
                        for d in range(self.periods // self.slots_per_day):
                            for s in range(self.slots_per_day):
                                period = d * self.slots_per_day + s
                                if s not in available_slots[part]:
                                    for exam in range(course.number_of_exams):
                                        course.available_periods[exam][part].discard(period)
                    
                # filter out constraints (min distance, and also room unavailabilities)            
                def filter_constraint(D0, D1, t):
                    a, b = t
                    # consider the constraint $a \leq x_1 - x_0 \leq b$
                    # these are the propagation rules:
                    d0 = len(D0)
                    d1 = len(D1)
                    # propagation rules for $x_0 + a \leq x_1$
                    # 1.1 $\forall x \in D_0 \quad x + a \leq \max D_1$:
                    D0 = set(filter(lambda x: x <= max(D1) - a, D0))
                    # 1.2. $\forall x \in D_1 \quad \min D_0 + a \leq x$ 
                    D1 = set(filter(lambda x: min(D0) + a <= x, D1))
                    # propagation rules for $x_1 \leq x_0 + b$
                    # 2.1. $\forall x \in D_1 \quad x \leq \max D_0 + b$
                    D1 = set(filter(lambda x: x <= max(D0) + b, D1))
                    # 2.2. $\forall x \in D_0 \quad \min D_1 \leq x + b$
                    D0 = set(filter(lambda x: min(D1) - b <= x, D0))
                    return len(D0) < d0 or len(D1) < d1, D0, D1
                    
                
                changed = True
                # constraint propagation up to fixpoint
                try:                
                    while changed:
                        changed = False
                        # first ensure that the difference between the first parts is kept
                        part = 0
                        for exam_a, exam_b in combinations(range(course.number_of_exams), 2):
                            c, course.available_periods[exam_a][part], course.available_periods[exam_b][part] = filter_constraint(course.available_periods[exam_a][part], course.available_periods[exam_b][part], course.distances_between_exams)
                            changed = changed or c
                        # secondly ensure that the inner distance between parts is kept
                        for exam in range(course.number_of_exams):                    
                            for part_a in range(len(course.parts) - 1):
                                part_b = part_a + 1
                                c, course.available_periods[exam][part_a], course.available_periods[exam][part_b] = filter_constraint(course.available_periods[exam][part_a], course.available_periods[exam][part_b], course.part_distances[part_a])
                                changed = changed or c
                                                    
                except ValueError: # a domain has become empty
                    pass

            self.events = [] # this is the exploded viewpoint of each event
            for course in self.courses.values():
                for exam in range(course.number_of_exams):
                    for part in course.parts:
                        self.events.append(Event(course.name, exam, part))

            self._compute_easylocal_representation()  

        else: # format is dzn
            data = MiniZincData(inst_content)
            self.events = list(range(data.parameters['Events']))
            self.periods = data.parameters['Periods']
            self.roomed_event = data.parameters['RoomedEvent']
            self.dummy_room_required = not all(self.roomed_event)
            self.rooms = list(range(data.parameters['Rooms'] - (0 if not self.dummy_room_required else 1)))
            self.conflicts = data.parameters['Conflicts']
            self.distance_weight = data.parameters['DistanceWeight']
            self.min_distances = data.parameters['MinDistance']
            self.max_distances = data.parameters['MaxDistance']
            self.precedence = data.parameters['Precedence']
            self.event_period_constraints = data.parameters['EventPeriodConstraints']
            self.event_room_constraints = data.parameters['EventRoomConstraints']
            self.roomset_overlap = data.parameters['RoomsetOverlap']     
            self.room_period_constraints = data.parameters['RoomPeriodConstraints']

    def __str__(self):
        return '{}'.format(self.periods)

    def _compute_easylocal_representation(self):       
        # redundant roomed event, to be determined at first to decide whether to include or not the dummy room
        self.roomed_event = [1] * len(self.events)
        for i in range(len(self.events)):    
            course = self.courses[self.events[i].course]
            part = course.parts.index(self.events[i].part)
            if course.rooms[part] is None: # no room is requested
                self.roomed_event[i] = 0
        self.dummy_room_required = not all(self.roomed_event)

        # conflicts and distance weights
        self.conflicts = [[0] * len(self.events) for _ in range(len(self.events))]
        self.distance_weight = [[0] * len(self.events) for _ in range(len(self.events))]
        for i, j in combinations(range(len(self.events)), 2):
            # first, search for same course, same teacher, and same curriculum
            if self.events[i].course == self.events[j].course or \
                self.courses[self.events[i].course].teacher == self.courses[self.events[j].course].teacher or \
                self.courses[self.events[i].course].curricula_primary & self.courses[self.events[j].course].curricula_primary:
                self.conflicts[i][j] = -1
                self.conflicts[j][i] = -1
            if self.events[i].course == self.events[j].course:
                if self.events[i].exam == self.events[j].exam:
                    self.distance_weight[i][j] = WRITTEN_ORAL_DISTANCE_WEIGHT
                    self.distance_weight[j][i] = WRITTEN_ORAL_DISTANCE_WEIGHT
                elif self.events[i].part == self.events[j].part and self.courses[self.events[i].course].parts.index(self.events[i].part) == 0 and self.courses[self.events[j].course].parts.index(self.events[j].part) == 0: # NOTE: the same_course_distance is only among the first parts
                    self.distance_weight[i][j] = SAME_COURSE_DISTANCE_WEIGHT
                    self.distance_weight[j][i] = SAME_COURSE_DISTANCE_WEIGHT
            elif self.courses[self.events[i].course].curricula_primary & self.courses[self.events[j].course].curricula_primary and self.courses[self.events[i].course].parts.index(self.events[i].part) == 0 and self.courses[self.events[j].course].parts.index(self.events[j].part) == 0:
                self.distance_weight[i][j] = PRIMARY_PRIMARY_DISTANCE_WEIGHT
                self.distance_weight[j][i] = PRIMARY_PRIMARY_DISTANCE_WEIGHT
            elif self.courses[self.events[i].course].curricula_primary & self.courses[self.events[j].course].curricula_secondary or \
                self.courses[self.events[j].course].curricula_primary & self.courses[self.events[i].course].curricula_secondary:
                if self.conflicts[i][j] > -1:
                    self.conflicts[i][j] = max(PRIMARY_SECONDARY_CONFLICT_WEIGHT, self.conflicts[i][j])
                    self.conflicts[j][i] = max(PRIMARY_SECONDARY_CONFLICT_WEIGHT, self.conflicts[j][i])
                if self.courses[self.events[i].course].parts.index(self.events[i].part) == 0 and self.courses[self.events[j].course].parts.index(self.events[j].part) == 0:
                    self.distance_weight[i][j] = max(PRIMARY_SECONDARY_DISTANCE_WEIGHT, self.distance_weight[i][j])
                    self.distance_weight[j][i] = max(PRIMARY_SECONDARY_DISTANCE_WEIGHT, self.distance_weight[j][i])
            elif self.courses[self.events[i].course].curricula_secondary & self.courses[self.events[j].course].curricula_secondary and self.conflicts[i][j] > -1:
                self.conflicts[i][j] = max(SECONDARY_SECONDARY_CONFLICT_WEIGHT, self.conflicts[i][j])
                self.conflicts[j][i] = max(SECONDARY_SECONDARY_CONFLICT_WEIGHT, self.conflicts[j][i])
#                distance_weight[i][j] = SECONDARY_SECONDARY_DISTANCE_WEIGHT
#                distance_weight[j][i] = SECONDARY_SECONDARY_DISTANCE_WEIGHT

        # min/max distances
        self.min_distances = [[0] * len(self.events) for _ in range(len(self.events))]
        self.max_distances = [[float('inf')] * len(self.events) for _ in range(len(self.events))]
        self.precedence = [[0] * len(self.events) for _ in range(len(self.events))]
        for i, j in combinations(range(len(self.events)), 2):
            if self.events[i].course == self.events[j].course:
                # same course
                course = self.courses[self.events[i].course]
                if self.events[i].exam == self.events[j].exam:
                    # same exam (so it's distance between parts)
                    part_a = course.parts.index(self.events[i].part)
                    part_b = course.parts.index(self.events[j].part)
                    if part_b == part_a + 1:
                        d = course.part_distances[part_a]
                        self.min_distances[i][j] = max(self.min_distances[i][j], d[0])
                        self.max_distances[i][j] = min(self.max_distances[i][j], d[1])
                    if part_a < part_b:
                        self.precedence[i][j] = 1
                else:
                    # there are different exams (so it's distance between exams, if they're on the first part only)
                    d = course.distances_between_exams
                    self.min_distances[i][j] = max(self.min_distances[i][j], d[0])
                    self.max_distances[i][j] = min(self.max_distances[i][j], d[1])
                    if self.events[i].exam < self.events[j].exam:
                        self.precedence[i][j] = 1
            elif self.courses[self.events[i].course].curricula_primary & self.courses[self.events[j].course].curricula_primary:
                # exams in the same primary curriculum
                self.min_distances[i][j] = max(self.min_distances[i][j], self.primary_primary_distance)
                self.min_distances[j][i] = max(self.min_distances[j][i], self.primary_primary_distance)
            elif self.courses[self.events[i].course].curricula_primary & self.courses[self.events[j].course].curricula_secondary or self.courses[self.events[j].course].curricula_primary & self.courses[self.events[i].course].curricula_secondary:   
                # exams in the primary and secondary curriculum
                self.min_distances[i][j] = max(self.min_distances[i][j], self.primary_secondary_distance)
                self.min_distances[j][i] = max(self.min_distances[j][i], self.primary_secondary_distance)
        self.max_distances = [list(map(lambda v: min(v, self.periods), self.max_distances[i])) for i in range(len(self.events))]

        self.event_period_constraints = [[0] * self.periods for _ in range(len(self.events))]
        post_process_preferred = defaultdict(lambda: [])
        for i in range(len(self.events)):    
            course = self.courses[self.events[i].course]
            for period, constraints in course.period_constraints[course.parts.index(self.events[i].part)].items():
                for (exam, level) in filter(lambda e: e[0] == self.events[i].exam, constraints):
                    if level == 'Forbidden':
                        self.event_period_constraints[i][period] = -1
                    elif level == 'Undesired' and self.event_period_constraints[i][period] > -1:
                        self.event_period_constraints[i][period] = max(UNDESIRED_PERIOD_WEIGHT, self.event_period_constraints[i][period])
                    elif level == 'Preferred':
                        post_process_preferred[i].append(period)        

        # Global period constraints
        for p in self.period_constraints:
            if self.period_constraints[p] == 'Forbidden':
                for i in range(len(self.events)):
                    self.event_period_constraints[i][p] = -1
            elif self.period_constraints[p] == 'Undesired':
                for i in range(len(self.events)):
                    if self.event_period_constraints[i][p] > -1:
                        self.event_period_constraints[i][p] = max(UNDESIRED_PERIOD_WEIGHT, self.event_period_constraints[i][p])

        for i, preferred_periods in post_process_preferred.items():
            for p in range(self.periods):
                if p not in preferred_periods and self.event_period_constraints[i][p] > -1:
                    self.event_period_constraints[i][p] = max(INDIFFERENT_PERIOD_WEIGHT, self.event_period_constraints[i][p])
                elif p in preferred_periods and self.event_period_constraints[i][p] > -1:
                    self.event_period_constraints[i][p] = 0

        assert not any(all(map(lambda s: s == -1, r)) for r in self.event_period_constraints), "Some of the event period constraints are inconsistent"
        
        self.event_room_constraints = [[0] * (len(self.rooms) + 1 if self.dummy_room_required else len(self.rooms)) for _ in range(len(self.events))]
        post_process_preferred = defaultdict(lambda: [])
        # compatible room is subsumed by the EventRoomConstraints, i.e., a non-compatible room will be forbidden
        for i in range(len(self.events)):    
            course = self.courses[self.events[i].course]
            part = course.parts.index(self.events[i].part)
            exam = self.events[i].exam
            if self.dummy_room_required and course.rooms[part] is None: # if no room is requested, therefore all the other rooms are prohibited
                for r, _ in enumerate(self.ordered_rooms):
                    self.event_room_constraints[i][r] = -1
            else: # otherwise the dummy room is prohibited
                if self.dummy_room_required:
                    self.event_room_constraints[i][len(self.rooms)] = -1                
                for room, constraints in course.room_constraints.items():
                    room = self.rooms[room]
                    r = self.ordered_rooms.index(room)
                    level = constraints.get(exam, {}).get(part)
                    if level == 'Forbidden':
                        self.event_room_constraints[i][r] = -1
                    elif level == 'Undesired' and self.event_room_constraints[i][r] > -1:
                        self.event_room_constraints[i][r] = max(UNDESIRED_ROOM_WEIGHT, self.event_room_constraints[i][r])
                    elif level == 'Preferred':
                        post_process_preferred[i].append(r)
                # checking and translating room compatibility
                if course.rooms[part] is not None:
                    for r, room in enumerate(self.ordered_rooms):
                        if not room.compatible_room(*course.rooms[part]):
                            self.event_room_constraints[i][r] = -1         

        for i, preferred_rooms in post_process_preferred.items():
            for r in range(len(self.rooms)):
                if r not in preferred_rooms and self.event_room_constraints[i][r] > -1:
                    self.event_room_constraints[i][r] = max(INDIFFERENT_ROOM_WEIGHT, self.event_room_constraints[i][r])
                elif r in preferred_rooms and self.event_room_constraints[i][r] > -1:
                    self.event_room_constraints[i][r] = 0            

        assert not any(all(map(lambda s: s == -1, r)) for r in self.event_room_constraints), "Some of the event room constraints are inconsistent"

        self.room_period_constraints = [[0] * self.periods for _ in range(len(self.rooms) + 1 if self.dummy_room_required else len(self.rooms))]
        # Room period constraints    
        for r, room in enumerate(self.ordered_rooms):                
            for (period, level) in room.constraints.items():
                if level == 'Forbidden':
                    self.room_period_constraints[r][period] = -1
                elif level == 'Undesired':
                    if self.room_period_constraints[r][period] > -1:
                        self.room_period_constraints[r][period] = max(UNDESIRED_ROOM_WEIGHT, self.room_period_constraints[r][period])

        for r, room in enumerate(self.ordered_rooms):
            for level in room.global_constraints or []:
                for p in range(self.periods):
                    if self.room_period_constraints[r][p]> -1:
                        self.room_period_constraints[r][p] = max(UNDESIRED_ROOM_WEIGHT, self.room_period_constraints[r][p])

        # take into account composite rooms, which takes the worst constraint values among its component
        for r, room in enumerate(self.ordered_rooms):
            if not room.members: # this is applicable to composite moves only
                continue
            for p in range(self.periods):
                    for c_room in room.members:
                        c_r = self.ordered_rooms.index(c_room)
                        if self.room_period_constraints[c_r][p] == -1:
                            self.room_period_constraints[r][p] = -1
                        elif self.room_period_constraints[c_r][p] > 0 and self.room_period_constraints[r][p] > -1:
                            self.room_period_constraints[r][p] = max(self.room_period_constraints[c_r][p], self.room_period_constraints[r][p])
                
                        
        self.roomset_overlap = [[0] * (len(self.rooms) + 1 if self.dummy_room_required else len(self.rooms)) for _ in range(len(self.rooms) + 1 if self.dummy_room_required else len(self.rooms))]
        for r1, r2 in combinations(range(len(self.ordered_rooms)), 2):
            room1, room2 = self.ordered_rooms[r1], self.ordered_rooms[r2]
            if room1 in room2.members or room2 in room1.members:
                self.roomset_overlap[r1][r2] = 1
                self.roomset_overlap[r2][r1] = 1
            elif room1.members & room2.members:
                self.roomset_overlap[r1][r2] = 1
                self.roomset_overlap[r2][r1] = 1
            self.roomset_overlap[r1][r1] = 1
            self.roomset_overlap[r2][r2] = 1


    def to_dzn(self):
        def matrix_repr(lines, processing=str):
            p = "["
            if len(lines) == 0:
                print(f"{p}]")
                return p
            indent = 4
            for i, l in enumerate(lines):
                if i > 0:
                    p += " " * indent
                p += f"|{', '.join(map(processing, l))}"
                if i < len(lines) - 1:
                    p += "\n"
            p += "|]"
            return p

        result = []
        # scalars
        result.append(f'Events = {len(self.events)};')
        result.append(f'Periods = {self.periods};')
        result.append(f'Rooms = {len(self.rooms) + 1 if self.dummy_room_required else len(self.rooms)};') 
        result.append(f'RoomedEvent = {self.roomed_event};')
        # conflicts and distance weights
        result.append(f'Conflicts = {matrix_repr(self.conflicts)};') 
        result.append(f'DistanceWeight = {matrix_repr(self.distance_weight)};')
        result.append(f'MinDistance = {matrix_repr(self.min_distances)};') 
        result.append(f'MaxDistance = {matrix_repr(self.max_distances)};')      
        result.append(f'Precedence = {matrix_repr(self.precedence)};')
        result.append(f'EventPeriodConstraints = {matrix_repr(self.event_period_constraints)};')
        result.append(f'EventRoomConstraints = {matrix_repr(self.event_room_constraints)};')
        result.append(f'RoomPeriodConstraints = {matrix_repr(self.room_period_constraints)};')
        result.append(f'RoomsetOverlap = {matrix_repr(self.roomset_overlap)};')
        

        return "\n".join(result)
