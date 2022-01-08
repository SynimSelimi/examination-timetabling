from helpers import *
from collections import defaultdict

def expand_exams(flat_courses, course):
    exam_type = course['ExamType']
    if exam_type == "WrittenAndOral":
        written_course = course.copy()
        written_course['ExamType'] = 'Written'
        written_course['TwoPart'] = True
        # written_course['ExamOrder'] = 0
        flat_courses.append(written_course)
        oral_course = course.copy()
        oral_course['ExamType'] = 'Oral'
        oral_course['TwoPart'] = True
        oral_course['WrittenAllocated'] = False
        # oral_course['ExamOrder'] = 1
        flat_courses.append(oral_course)
    else:
        new_course = course.copy()
        flat_courses.append(new_course)

def flat_map_courses(courses):
    flat_courses = []

    while (len(courses) != 0):
        flat_done = False
        course = courses.pop()
        number_of_exams = course['NumberOfExams']

        if number_of_exams > 1: course['MultipleExams'] = True

        for i in range(0, number_of_exams):
            course['NumberOfExams'] = 1
            course['ExamOrder'] = i
            course['PredecessorAllocated'] = True if i == 0 else False
            expand_exams(flat_courses, course)
            flat_done = True

        if not flat_done: flat_courses.append(course)

    return flat_courses

# constraints are provided all as Undesired (soft)
def add_possible_rooms(courses, rooms, constraints):
    _courses = courses.copy()
    for course in _courses:
        req_rooms = course['RoomsRequested']
        room_numbers = req_rooms['Number']

        is_oral = course['ExamType'] == 'Oral'
        specs = course.get('WrittenOralSpecs')
        room_for_oral = specs and specs.get('RoomForOral')

        course['PossibleRooms'] = []

        if is_oral and room_for_oral:
            def fun(room):
                match = room['Type'] != "Composite"
                if match: return room['Room']
                return None
            course['PossibleRooms'] = list(filter(None, list(map(fun, rooms))))
        elif is_oral and specs and not room_for_oral:
            course['PossibleRooms'] = []
        elif room_numbers == 1:
            room_type = req_rooms['Type']
            def fun(room):
                match = room['Type'] == room_type
                if match: return room['Room']
                return None
            course['PossibleRooms'] = list(filter(None, list(map(fun, rooms))))
        elif room_numbers > 1:
            room_type = req_rooms['Type']
            def fun(room):
                match = room.get('Members') and len(room['Members']) == room_numbers and \
                    any(_room['Type'] == room_type and _room['Room'] == room['Members'][0] for _room in rooms)
                if match: return room['Room'] + ":" + ",".join(room['Members'])
                return None
            course['PossibleRooms'] = list(filter(None, list(map(fun, rooms))))

    return _courses

def add_curricula_info(courses, curricula):
    _courses = courses.copy()
    for course in _courses:
        course_name = course['Course']
        relevant_primaries = list(filter(lambda val : course_name in val['PrimaryCourses'], curricula))
        primary_courses = list(map(lambda val : val['PrimaryCourses'], relevant_primaries))
        relevant_secondaries = list(filter(lambda val : course_name in val['SecondaryCourses'], curricula))
        secondary_courses = list(map(lambda val : val['SecondaryCourses'], relevant_secondaries))

        primary_courses = flat_map(lambda x: x, primary_courses)
        secondary_courses = flat_map(lambda x: x, secondary_courses)

        if course_name in primary_courses: primary_courses.remove(course_name)
        if course_name in secondary_courses: secondary_courses.remove(course_name)

        course['PrimaryCourses'] = primary_courses
        course['SecondaryCourses'] = secondary_courses

    return _courses

def add_same_teacher_courses(courses):
    _courses = courses.copy()
    course_per_teacher = defaultdict(list)  

    for course in _courses:
        course_per_teacher[course['Teacher']].append(course['Course'])

    for course in _courses:
        unique_teacher_courses = list(set(course_per_teacher[course['Teacher']]))
        course['SameTeacherCourses'] = list(filter(lambda x: x != course["Course"], unique_teacher_courses))

    return _courses

def sieve_periods(periods, period_constraints):
    _periods = periods.copy()
    for constraint in period_constraints:
        _periods.remove(constraint['Period'])

    return _periods

def add_possible_periods(courses, periods, event_period_constraints):
    _courses = courses.copy()
    for course in _courses:
        _periods = periods.copy()
        course_name = course['Course']
        exam_type = course['ExamType']
        exam_order = course.get('ExamOrder')
        filter_fun = lambda x: \
            (x.get('Part') == None or x['Part'] == exam_type) and \
            x['Exam'] == exam_order \
            and x['Course'] == course_name
        forbidden_periods = list(filter(filter_fun, event_period_constraints))
        forbidden_periods = list(map(lambda x: x['Period'], forbidden_periods))

        for f_period in forbidden_periods: 
            if f_period in _periods: 
                _periods.remove(f_period)

        course['PossiblePeriods'] = _periods

    return _courses

def order_course_by_constraints(courses):
    _courses = courses.copy()
    ordered_courses = sorted(_courses, key=len, reverse=True)
    return ordered_courses

def group_by_course(courses):
    _courses = courses.copy()
    grouped_courses = []

    while len(_courses) > 0:
        new_course = []
        _course = _courses.pop(0)
        related_courses = list(filter(lambda x: x['Course'] == _course['Course'], _courses))
        for r_course in related_courses: _courses.remove(r_course)
        new_course.append(_course)
        new_course.extend(related_courses)
        grouped_courses.append(new_course)

    return grouped_courses

def group_by_exams_and_parts(courses):
    # matrix = [ExamOrder{i} = [One Part + Written TwoPart, Oral TwoPart]]
    _courses = courses.copy()
    grouped_courses = []
    orders = set(map(lambda x:x['ExamOrder'], _courses))
    for order in orders:
        order_courses = list(filter(lambda x: x['ExamOrder'] == order, _courses))
        grouped_courses.append(order_courses)

    return grouped_courses