import random
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

    def available_room_period(self, rooms, periods, course):
        rooms = rooms.copy()
        periods = periods.copy()
        room = None
        period = None

        def pairs(one, two):
            for p in one:
                for r in two:
                    yield p, r

        if len(rooms) == 0:
            for p in periods:
                    no_room = self.taken_period_room.get(p, {}).get('noRoom', [])
                    taken = self.taken_period_room.get(p, {}).get('noRoom', [])
                    period_course = self.taken_period_room.get(p, {}).get('noRoom', [])

                    primary_course_conflicts = any(item in course["PrimaryCourses"] for item in period_course)
                    same_teacher_conflicts = any(item in course["SameTeacherCourses"] for item in period_course)

                    conflict = period_course and ( primary_course_conflicts or same_teacher_conflicts )

                    if not taken and not conflict:
                        period = p
                        if len(no_room) == 0:
                            self.taken_period_room[period]['noRoom'] = []
                        self.taken_period_room[period]['noRoom'].append(course['Course'])
                        break
        else:
            for p, r in pairs(periods, rooms):
                    taken = self.taken_period_room.get(p, {}).get(r, {})
                    period_course = self.taken_period_room.get(p, {}).values()

                    primary_course_conflicts = any(item in course["PrimaryCourses"] for item in period_course)
                    same_teacher_conflicts = any(item in course["SameTeacherCourses"] for item in period_course)

                    conflict = period_course and ( primary_course_conflicts or same_teacher_conflicts )

                    if not taken and not conflict:
                        room = r
                        period = p
                        self.taken_period_room[period][room] = course['Course']
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

    def multiple_exams_constraint_propagation(self, course, courses, period):
        name = course['Course']
        exam_type = course['ExamType']
        exam_nr = course['ExamOrder']

        # related_courses = list(filter(lambda x: x['Course'] == name and x['ExamOrder'] > exam_nr, courses))

        for _course in courses:
            if _course['Course'] == name and _course['ExamOrder'] < exam_nr:
                periods = _course['PossiblePeriods']
                _course['PossiblePeriods'] = list(filter(lambda x: x < period, periods))
            elif _course['Course'] == name and _course['ExamOrder'] >= exam_nr:
                periods = _course['PossiblePeriods']
                _course['PossiblePeriods'] = list(filter(lambda x: x > period, periods))

    def two_part_constraint_propagation(self, course, courses, period):
        name = course['Course']
        exam_type = course['ExamType']
        if exam_type == 'Oral': return

        # related_courses = list(filter(lambda x: x['Course'] == name and x['ExamType'] == 'Written', courses))

        for _course in courses:
            if _course['Course'] == name and _course['ExamOrder'] == 'Written':
                periods = _course['PossiblePeriods']
                _course['PossiblePeriods'] = list(filter(lambda x: x > period, periods))

    def solve(self):
        self.cost = 0
        self.assignments = []

        # dict(sorted(x.items(), key=lambda item: item[1]))
        courses = self.instances.copy()

        random.shuffle(courses)
        while len(courses) > 0:
            _courses = courses.pop(0)
            for course in _courses:
                course_name = course['Course']

                exam_type = course['ExamType']
                exam_order = course['ExamOrder']
                two_part = course.get('TwoPart')
                multiple_exams = course.get('MultipleExams')

                rooms = course.get('PossibleRooms')
                periods = course.get('PossiblePeriods')

                room, period = self.available_room_period(rooms, periods, course)
                if period == None:
                    print("Impossible encountered. Retrying...")
                    return None

                if multiple_exams == True: self.multiple_exams_constraint_propagation(course, _courses, period)
                if two_part == True: self.two_part_constraint_propagation(course, _courses, period)

                event = Event(exam_order, exam_type, period, room, course_name)
                self.add_event(course_name, event)

        return self.export()

    @staticmethod
    def try_solving(instances, hard_constraints):
        solution = None
        while solution == None:
            solution = Solution(instances, hard_constraints).solve()
        return solution

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