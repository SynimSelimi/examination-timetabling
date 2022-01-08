import random
import time
from helpers import flat_map
from collections import defaultdict
import copy

class Solution:
    def __init__(self, instances, hard_constraints):
        self.instances = instances
        self.cost = 0
        self.assignments = []
        self.course_assignment_ids = {}
        self.last_assignment_id = 0
        self.taken_period_room = defaultdict(dict)
        self.hard_constraints = hard_constraints
        self.room_period_constraints = list(
            filter(lambda val: val['Type'] == 'RoomPeriodConstraint', self.hard_constraints)
        )
        self.last_period = None

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

        # two_part = course.get('TwoPart')
        # min_distance_of_exams = two_part and course.get('MinimumDistanceBetweenExams')
        # specs = course.get('WrittenOralSpecs')
        # min_two_part_distance = specs and specs.get('MinDistance')

        # if min_distance_of_exams:
        #     periods.sort(key=lambda x: random.randint(0,1), reverse=True)

        # periods = sorted(periods, key=lambda x: x)

        if len(rooms) == 0:
            for p in periods:
                conflict_courses = []
                period_course = self.taken_period_room.get(p, {}).values()
                no_room_courses = self.taken_period_room.get(p, {}).get('noRoom', [])
                conflict_courses.extend(period_course)
                conflict_courses.extend(no_room_courses)

                primary_course_conflicts = any(item in course["PrimaryCourses"] for item in conflict_courses)
                same_teacher_conflicts = any(item in course["SameTeacherCourses"] for item in conflict_courses)

                conflict = conflict_courses and (primary_course_conflicts or same_teacher_conflicts)

                if not conflict:
                    period = p
                    if len(no_room_courses) == 0:
                        self.taken_period_room[period]['noRoom'] = []
                    self.taken_period_room[period]['noRoom'].append(course['Course'])
                    break
        else:
            for p, r in pairs(periods, rooms):
                taken = False
                is_composite = ":" in r

                if is_composite:
                    com_rooms = r.split(':')[1].split(',')
                    for c in com_rooms:
                        if self.taken_period_room.get(p, {}).get(c, {}):
                            taken = True
                            break
                else:
                    taken = self.taken_period_room.get(p, {}).get(r, {})

                if taken:
                    continue

                no_room_courses = self.taken_period_room.get(p, {}).get('noRoom', [])
                period_course = self.taken_period_room.get(p, {}).values()

                conflict_courses = []
                conflict_courses.extend(period_course)
                conflict_courses.extend(no_room_courses)

                primary_course_conflicts = any(item in course["PrimaryCourses"] for item in conflict_courses)
                same_teacher_conflicts = any(item in course["SameTeacherCourses"] for item in conflict_courses)

                conflict = conflict_courses and (primary_course_conflicts or same_teacher_conflicts)

                if not taken and not conflict:
                    period = p
                    if is_composite:
                        room = r.split(":")[0]
                        com_rooms = r.split(':')[1].split(',')
                        for c in com_rooms:
                            self.taken_period_room[period][c] = course['Course']
                    else:
                        room = r
                        self.taken_period_room[period][room] = course['Course']
                    break

        return room, period

    # # # # # # # # # # # #
    # To Do Take into account same day constraints (soft)
    # To do add EventRoomConstraint to a temporary memory set (soft)
    # To Do check MinimumDistanceBetweenExams (soft), simply add to propagation period
    # To Do check MaxDistance MinDistance for WrittenOral (soft), simply add to propagation period
    # To Do check PrimaryPrimaryDistance (soft)
    # To Do calculate cost
    # # # # # # # # # # # #

    # #####################
    # INVALID
    # D3-2-16.json +
    # D3-3-16.json +
    # D3-3-18.json +
    # D4-1-17.json +
    # D4-3-17.json +
    # D4-3-18.json +
    # D5-1-17.json +
    # D5-1-18.json +
    # D5-3-18.json +
    # NOT RUNNING (due to order of allocating courses)
    # D6-1-16.json +
    # D6-1-17.json +
    # D6-1-18.json +
    # D6-2-* +
    # D6-3-* +
    # D6-2-17.json
    # #####################

    def multiple_exams_constraint_propagation(self, course, courses, period):
        name = course['Course']
        exam_type = course['ExamType']
        exam_nr = course['ExamOrder']
        two_part = course.get('TwoPart')

        for _course in courses:
            if _course['Course'] == name and int(_course['ExamOrder']) > int(exam_nr):
                periods = _course['PossiblePeriods']
                _course['PossiblePeriods'] = list(filter(lambda x: x > period, periods))
            if _course['Course'] == name and int(_course['ExamOrder']) == (int(exam_nr) + 1):
                _course['PredecessorAllocated'] = two_part != True or (two_part == True and exam_type == 'Oral' and course['WrittenAllocated'] == True)

    def two_part_constraint_propagation(self, course, courses, period):
        name = course['Course']
        exam_type = course['ExamType']
        exam_nr = course['ExamOrder']
        if exam_type != 'Written': return

        for _course in courses:
            if _course['Course'] == name and _course['ExamOrder'] == exam_nr and _course['ExamType'] == 'Oral':
                _course['WrittenAllocated'] = True
                periods = _course['PossiblePeriods']
                _course['PossiblePeriods'] = list(filter(lambda x: x > period, periods))

    # def distribute_periods(self, periods, len_courses):
    #     if (self.last_period == None): return periods

    #     def rotate_array(a,d):
    #         temp = a.copy()
    #         n=len(temp)
    #         temp[:]=temp[d:n]+temp[0:d]
    #         return temp

    #     # shifted_periods = rotate_array(periods, int(index * (len(periods) / total_courses)))
    #     shifted_periods = rotate_array(periods, int(-len_courses/3))
    #     return shifted_periods

    # def reorder(self, courses):
    #     _courses = courses.copy()
    #     reordered_courses = []

    #     while len(_courses) > 0:
    #         _course = _courses.pop(0)
    #         if len(_course) != 0:
    #             _flat_course = _course.pop(0)
    #             reordered_courses.append(_flat_course)
    #             _courses.append(_course)

    #     return _courses

    # def shuffle_by_exams_and_parts(self, courses):
    #     _courses = courses.copy()
    #     random.shuffle(_courses)

    #     flat_courses = flat_map(lambda x: x, _courses)
    #     grouped_courses = []
    #     orders = set(map(lambda x:x['ExamOrder'], flat_courses))
    #     for order in orders:
    #         order_courses = list(filter(lambda x: x['ExamOrder'] == order, flat_courses))
    #         order_courses = sorted(order_courses, key=lambda x: x['ExamType'] == 'Oral')
    #         grouped_courses.append(order_courses)

    #     return grouped_courses

    def solve(self):
        self.cost = 0
        self.assignments = []

        grouped_courses = self.instances.copy()
        total_events = 0
        courses = []
        to_group = random.randint(0,1) == 0
        for group in grouped_courses:
            total_events += len(group)
            group_courses = group.copy()
            random.shuffle(group_courses)
            if to_group:
                group_courses = sorted(group_courses, key=lambda x: x['ExamType'] == 'Oral')
            courses += group_courses

        reallocations = 0

        while len(courses) > 0:
            # _courses = courses.pop(0)
            # for course in _courses:
            course = courses.pop(0)
            course_name = course['Course']
            # print(course_name)

            exam_type = course['ExamType']
            exam_order = course['ExamOrder']
            two_part = course.get('TwoPart')
            written_allocated = course.get('WrittenAllocated')
            predecessor_allocated = course.get('PredecessorAllocated')
            multiple_exams = course.get('MultipleExams')

            if reallocations > 250:
                return None

            if two_part == True and exam_type == 'Oral' and written_allocated == False:
                print(reallocations, end="\r")
                courses.insert(int(len(courses)/2), course)
                reallocations += 1
                continue

            if multiple_exams == True and predecessor_allocated == False:
                print(reallocations, end="\r")
                courses.insert(int(len(courses)/2), course)
                reallocations += 1
                continue

            rooms = course.get('PossibleRooms')
            periods = course.get('PossiblePeriods')

            room, period = self.available_room_period(rooms, periods, course)

            if period == None:
                percentage = '{0:.2f}%'.format((total_events - len(courses)) * 100 / total_events)
                print("Retrying... ", percentage, end="\r")
                return None

            self.last_period = period
            if multiple_exams == True: self.multiple_exams_constraint_propagation(course, courses, period)
            if two_part == True: self.two_part_constraint_propagation(course, courses, period)

            event = Event(exam_order, exam_type, period, room, course_name)
            self.add_event(course_name, event)

        return self.export()

    @staticmethod
    def try_solving(instances, hard_constraints):
        solution = None
        attempt = 0
        while solution == None and attempt < 100:
            solution = Solution(copy.deepcopy(instances), hard_constraints).solve()
            attempt += 1

        if attempt < 100:
            return solution
        else:
            print("Could not solve in time!")
            return None

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