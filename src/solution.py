import random
import time
import json
from helpers import flat_map, flatten
from validation import validate_solution
from collections import defaultdict
import copy
from evaluation import evaluate

class Solution:
    def __init__(self, instances, hard_constraints, with_validation = False, instance_path = None, constraints = None):

        self.instances = instances
        self.cost = 0
        self.assignments = []
        self.course_assignment_ids = {}
        self.last_assignment_id = 0
        self.taken_period_room = defaultdict(dict)
        self.hard_constraints = hard_constraints
        self.constraints = constraints
        self.room_period_constraints = list(
            filter(lambda val: val['Type'] == 'RoomPeriodConstraint', self.hard_constraints)
        )
        self.validation_results = {}
        self.with_validation = with_validation
        self.last_period = None
        self.instance_path = instance_path
        self.import_constraints()
        self.attempt = 0
        self.ancestors = 0

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
                conflict_courses = flatten(conflict_courses)

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
                conflict_courses = flatten(conflict_courses)

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

    def distribute_periods(self, periods):
        def rotate_array(a,d):
            temp = a.copy()
            n=len(temp)
            temp[:]=temp[d:n]+temp[0:d]
            return temp

        shifted_periods = rotate_array(periods, -int(len(periods)/2))
        return shifted_periods

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

        grouped_courses = copy.deepcopy(self.instances)
        total_events = 0
        courses = []
        to_group = random.randint(0,1) == 0
        smart_injection = random.randint(0,1) == 0
        randomize_rooms = random.randint(0,1) == 0
        for group in grouped_courses:
            total_events += len(group)
            group_courses = group.copy()
            random.shuffle(group_courses)
            if to_group:
                group_courses = sorted(group_courses, key=lambda x: x['ExamType'] == 'Oral')
            courses.extend(group_courses)

        reallocations = 0

        while len(courses) > 0:
            course = courses.pop(0)
            course_name = course['Course']

            exam_type = course['ExamType']
            exam_order = course['ExamOrder']
            two_part = course.get('TwoPart')
            written_allocated = course.get('WrittenAllocated')
            predecessor_allocated = course.get('PredecessorAllocated')
            multiple_exams = course.get('MultipleExams')

            if reallocations > 250:
                return None

            if two_part == True and exam_type == 'Oral' and written_allocated == False:
                # print(reallocations, end="\r")
                courses.insert(random.randint(int(len(courses)/2), len(courses)), course)
                reallocations += 1
                continue

            if multiple_exams == True and predecessor_allocated == False:
                # print(reallocations, end="\r")
                courses.insert(random.randint(int(len(courses)/2), len(courses)), course)
                reallocations += 1
                continue

            rooms = course.get('PossibleRooms')
            if randomize_rooms == True: random.shuffle(rooms)
            periods = course.get('PossiblePeriods')
            if exam_order % 2 == 1: periods = self.distribute_periods(periods)

            room, period = self.available_room_period(rooms, periods, course)

            if period == None:
                percentage = '{0:.2f}%'.format((total_events - len(courses)) * 100 / total_events)
                print("Retrying... ", percentage, end="\r")
                return None

            self.last_period = period
            if multiple_exams == True: self.multiple_exams_constraint_propagation(course, courses, period)
            if two_part == True: self.two_part_constraint_propagation(course, courses, period)
            
            # if smart_injection == True:
            #     def swap(list, pos1, pos2): list[pos1], list[pos2] = list[pos2], list[pos1]
            #     for _course in courses:
            #         if _course['Course'] == course_name and multiple_exams and int(_course['ExamOrder']) > int(exam_order):
            #             _course_index = courses.index(_course)
            #             swap(courses, random.randint(_course_index - 1, len(courses)-1), _course_index)
            #             print("\t\t\tsmart_injection at", reallocations, end="\r")
            #         if _course['Course'] == course_name and _course['ExamOrder'] == exam_order and two_part and course['ExamType'] == 'Written' and _course['ExamType'] == 'Oral':
            #             _course_index = courses.index(_course)
            #             swap(courses, random.randint(_course_index - 1, len(courses)-1), _course_index)
            #             print("\t\t\tsmart_injection at", reallocations, end="\r")

            event = Event(exam_order, exam_type, period, room, course_name, course)
            self.add_event(course_name, event)

        self.cost = evaluate(self)
        if self.with_validation: self.validate()
        return self.export()

    @staticmethod
    def try_solving(instances, hard_constraints, instance_path = None, constraints = None):
        solution_found = None
        solution = None
        attempt = 0

        while solution_found == None and attempt < 700:
            solution = Solution(
                copy.deepcopy(instances), hard_constraints, 
                instance_path=instance_path, constraints=constraints
            )
            solution_found = solution.solve()
            solution.attempt = attempt
            attempt += 1

        if attempt < 700:
            return solution
        else:
            print("Could not solve in time!")
            return None

    def new_available_room(self, rooms, current_room, period, course):
        rooms = rooms.copy()
        random.shuffle(rooms)
        room = None

        if len(rooms) == 0:
            return room
        else:
            for r in rooms:
                taken = False
                is_composite = ":" in r

                if is_composite:
                    com_rooms = r.split(':')[1].split(',')
                    for c in com_rooms:
                        if self.taken_period_room.get(period, {}).get(c, {}):
                            taken = True
                            break
                else:
                    taken = self.taken_period_room.get(period, {}).get(r, {})

                if taken:
                    continue

                no_room_courses = self.taken_period_room.get(period, {}).get('noRoom', [])
                period_course = self.taken_period_room.get(period, {}).values()

                conflict_courses = []
                conflict_courses.extend(period_course)
                conflict_courses.extend(no_room_courses)
                conflict_courses = flatten(conflict_courses)

                primary_course_conflicts = any(item in course["PrimaryCourses"] for item in conflict_courses)
                same_teacher_conflicts = any(item in course["SameTeacherCourses"] for item in conflict_courses)

                conflict = conflict_courses and (primary_course_conflicts or same_teacher_conflicts)

                if not taken and not conflict:
                    if is_composite:
                        room = r.split(":")[0]
                        com_rooms = r.split(':')[1].split(',')
                        for c in com_rooms:
                            self.taken_period_room[period][c] = course['Course']
                    else:
                        room = r
                        self.taken_period_room[period][room] = course['Course']
                    break

        if current_room != None and room != None:
            is_composite = ":" in current_room
            if is_composite:
                com_rooms = current_room.split(':')[1].split(',')
                for c in com_rooms:
                    self.taken_period_room[period][c] = None
            else:
                self.taken_period_room[period][current_room] = None

        return room

    def mutate_rooms(self):
        rooms_to_change = 50
        changed_rooms = 0

        courses = []
        grouped_courses = copy.deepcopy(self.instances)
        for group in grouped_courses:
            group_courses = group.copy()
            courses.extend(group_courses)

        for assignment in self.assignments:
            if rooms_to_change == changed_rooms: break
            for event in assignment.events:
                course = [x for x in courses if x['Course'] == assignment.course and x['ExamType'] == event.part and x['ExamOrder'] == event.exam][0]
                rooms = course['PossibleRooms']
                new_room = self.new_available_room(rooms, event.room, event.period, course)
                if new_room != None:
                    event.room = new_room
                    changed_rooms += 1
                    # print("CHANGED ROOMS ", changed_rooms, end="\r")

        if self.with_validation: self.validate()
        self.cost = evaluate(self)
        return self.export()

    def mutate_courses(self, feedback=False, convergence=True):
        if feedback == True:
            amount_of_change = random.random() * (0.5/(self.attempt/2 + 1)) + 0.02
        elif convergence == True:
            amount_of_change = random.random() * (0.5/(self.ancestors + 1)) + 0.02
        else:
            amount_of_change = random.random() * 0.5 + 0.1
        changed_courses = 0
        pending_course_events = []

        courses = []
        total_events = 0
        randomize_rooms = random.randint(0,1) == 0
        reallocations = 0

        grouped_courses = copy.deepcopy(self.instances)
        for group in grouped_courses:
            total_events += len(group)
            group_courses = group.copy()
            courses.extend(group_courses)

        total_courses = len(self.assignments)
        for assignment in random.sample(self.assignments, int(total_courses * amount_of_change)):
            course_events = [x for x in courses if x['Course'] == assignment.course]
            pending_course_events.extend(course_events)

            for event in assignment.events:
                room, period = event.room, event.period
                if room == None:
                    self.taken_period_room[period]['noRoom'].remove(assignment.course)
                else:
                    is_composite = ":" in room
                    if is_composite:
                        com_rooms = room.split(':')[1].split(',')
                        for c in com_rooms:
                            self.taken_period_room[period][c] = None
                    else:
                        self.taken_period_room[period][room] = None
            self.course_assignment_ids.pop(assignment.course)
            self.assignments.remove(assignment)

        self.reindex_assignments()
        random.shuffle(pending_course_events)
        courses = pending_course_events
        while len(courses) > 0:
            course = courses.pop(0)
            course_name = course['Course']

            randomize_periods = random.randint(0,1) == 0
            distribute_periods = random.randint(0,1) == 0
            exam_type = course['ExamType']
            exam_order = course['ExamOrder']
            two_part = course.get('TwoPart')
            written_allocated = course.get('WrittenAllocated')
            predecessor_allocated = course.get('PredecessorAllocated')
            multiple_exams = course.get('MultipleExams')

            if reallocations > 250:
                return None

            if two_part == True and exam_type == 'Oral' and written_allocated == False:
                # print(reallocations, end="\r")
                courses.insert(random.randint(int(len(courses)/2), len(courses)), course)
                reallocations += 1
                continue

            if multiple_exams == True and predecessor_allocated == False:
                # print(reallocations, end="\r")
                courses.insert(random.randint(int(len(courses)/2), len(courses)), course)
                reallocations += 1
                continue

            rooms = course.get('PossibleRooms')
            if randomize_rooms == True: random.shuffle(rooms)
            periods = course.get('PossiblePeriods')
            if distribute_periods and exam_order % 2 == 1: periods = self.distribute_periods(periods)
            if randomize_periods == True: random.shuffle(periods)

            room, period = self.available_room_period(rooms, periods, course)

            if period == None:
                percentage = '{0:.2f}%'.format((total_events - len(courses)) * 100 / total_events)
                print("Retrying mutate... ", percentage, end="\r")
                return None

            self.last_period = period
            if multiple_exams == True: self.multiple_exams_constraint_propagation(course, courses, period)
            if two_part == True: self.two_part_constraint_propagation(course, courses, period)

            event = Event(exam_order, exam_type, period, room, course_name, course)
            self.add_event(course_name, event)

        self.cost = evaluate(self)
        return self.export()

    @staticmethod
    def try_mutating(solution):
        mutation_success = None
        neighbour_solution = None
        attempt = 0
        to_mutate_courses = random.randint(0,1) > 0.2

        while mutation_success == None and attempt < 700:
            neighbour_solution = copy.deepcopy(solution)
            neighbour_solution.attempt = attempt
            if to_mutate_courses:
                mutation_success = neighbour_solution.mutate_courses()
            else:
                mutation_success = neighbour_solution.mutate_rooms()

            attempt += 1

        neighbour_solution.ancestors += 1

        if attempt < 700:
            return neighbour_solution
        else:
            print("Could not mutate in time!")
            return None

    def validate(self):
        start_time = time.time()
        validation_results = validate_solution(self.instance_path, self.export(), None, None, None, False)
        end_time = time.time()
        validation_results['finished_for'] = f"{end_time-start_time:.2f}s."
        self.validation_results = validation_results

    def reindex_assignments(self):
        self.course_assignment_ids = {}
        for index, assignment in enumerate(self.assignments):
            course_name = assignment.course
            self.course_assignment_ids[course_name] = index
            self.last_assignment_id = index + 1

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
            'Cost': self.cost,
            'Validation': self.validation_results
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
    def __init__(self, exam, part, period, room, course, course_metadata={}):
        self.exam = exam
        self.part = part
        self.period = period
        self.room = room
        self.course = course
        self.course_metadata = course_metadata

    def export(self):
        return {
            'Exam': self.exam,
            'Part': self.part,
            'Period': self.period,
            'Room': self.room,
            'Course': self.course
        }