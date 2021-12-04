from collections import defaultdict

class Solution:
    def __init__(self, instances, hard_constraints):
        self.instances = instances
        self.cost = 0
        self.assignments = []
        self.course_assignment_ids = {}
        self.last_assignment_id = 0
        self.taken_period_room = defaultdict(dict)
        self.hard_constraints = hard_constraints
        self.room_period_constraints = list(filter(lambda val: val['Type'] == 'RoomPeriodConstraint', self.hard_constraints))

        self.import_constraints()

    def import_constraints(self):
        for c in self.room_period_constraints:
            room, period = c['Room'], c['Period']
            self.taken_period_room[period][room] = 'Constraint'

    def available_room_period(self, rooms, periods, course_name):
        rooms = rooms.copy()
        periods = periods.copy()
        room = None
        period = None

        def pairs(one, two):
            for p in one:
                for r in two:
                    yield p, r

        if len(rooms) == 0:
            period = periods.pop(0)
            room = None
        else:
            for p, r in pairs(periods, rooms):
                    taken = self.taken_period_room.get(p, {}).get(r, {})
                    if not taken:
                        room = r
                        period = p
                        self.taken_period_room[period][room] = course_name
                        break

        return room, period

    # # # # # # # # # # # # 
    # To Do add possible RoomPeriodConstraint to the busy roomPeriodSets (solution in import_constraints, needs review)
    # To Do Take into account same day constraints
    # To do add EventRoomConstraint to a temporary memory set
    # To Do check MinimumDistanceBetweenExams
    # To Do check MaxDistance MinDistance for WrittenOral (soft)
    # To Do check PrimaryPrimaryDistance (soft)
    # To Do check if courses have the same teacher (cannot be assigned same period)
    # To Do check if courses are primary (cannot be assigned same period)
    # To Do calculate cost
    # # # # # # # # # # # # 

    def solve(self):
        self.cost = 0
        self.assignments = []

        # dict(sorted(x.items(), key=lambda item: item[1]))
        courses = self.instances.copy()

        while len(courses) > 0:
            course = courses.pop(0)
            course_name = course['Course']

            exam_type = course['ExamType']
            exam_order = course['ExamOrder']

            rooms = course.get('PossibleRooms')
            periods = course.get('PossiblePeriods')

            room, period = self.available_room_period(rooms, periods, course_name)

            event = Event(exam_order, exam_type, period, room, course_name)
            self.add_event(course_name, event)

        return self.export()

    def add_event(self, course_name, event):
        if course_name not in self.course_assignment_ids.keys():
            assignment = Assignment(course_name)
            self.course_assignment_ids[course_name] = self.last_assignment_id
            self.assignments.append(assignment)
            self.last_assignment_id += 1
        else:
            assignment_id = self.course_assignment_ids[course_name]
            assignment = self.assignments[assignment_id]
            
        assignment.add_event(event)

    def export(self):
        assignments = []
        for assignment in self.assignments:
            assignments.append(assignment.export())

        return {
            'Assignments': assignments,
            'Cost': self.cost
        }

    def import_data(self, data):
        pass

class Assignment:
    def __init__(self, course):
        self.course = course
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def export(self):
        export_events = []
        for event in self.events:
            export_event = event.export()
            export_events.append(export_event)

        return {
            'Course': self.course,
            'Events': export_events
        }

class Event:
    def __init__(self, exam, part, period, room, course):
        self.exam = exam
        self.part = part
        self.period = period
        self.room = room
        self.course = course

    def export(self):
        return {
            'Exam': self.exam,
            'Part': self.part,
            'Period': self.period,
            'Room': self.room,
            'Course': self.course
        }