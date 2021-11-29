from helpers import *

def expand_exams(courses, flat_courses, course):
    exam_type = course['ExamType']
    if exam_type == "WrittenAndOral":
        written_course = course.copy();
        written_course['ExamType'] = 'Written'
        # written_course['ExamOrder'] = 0
        flat_courses.append(written_course)
        oral_course = course.copy();
        oral_course['ExamType'] = 'Oral'
        # oral_course['ExamOrder'] = 1
        flat_courses.append(oral_course)
    else:
        new_course = course.copy();
        flat_courses.append(new_course)
        flat_done = True

def flat_map_courses(courses):
    flat_courses = []

    while (len(courses) != 0):
        flat_done = False
        course = courses.pop()
        number_of_exams = course['NumberOfExams']

        for i in range(0, number_of_exams):
            course['NumberOfExams'] = 1;
            course['ExamOrder'] = i
            expand_exams(courses, flat_courses, course)
            flat_done = True

        if not flat_done: flat_courses.append(course)

    return flat_courses

# constraints are provided all as Undesired (soft)
def add_possible_rooms(courses, rooms, constraints):
    for course in courses:
        req_rooms = course['RoomsRequested']
        room_numbers = req_rooms['Number']

        is_oral = course['ExamType'] == 'Oral'
        specs = course.get('WrittenOralSpecs')
        room_for_oral = is_oral and specs and specs.get('RoomForOral')

        if room_numbers == 0:
            course['PossibleRooms'] = []
        elif room_for_oral:
            course['PossibleRooms'] = list(filter(None, list(map(lambda x: x['Room'], rooms))))
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
                match = room.get('Members') and len(room['Members']) == room_numbers
                if match: return room['Room']
                return None
            course['PossibleRooms'] = list(filter(None, list(map(fun, rooms))))

    return courses

def add_curricula_info(courses, curricula):
    for course in courses:
        course_name = course['Course']
        relevant_primaries = list(filter(lambda val : course_name in val['PrimaryCourses'], curricula))
        primary_courses = list(map(lambda val : val['PrimaryCourses'], relevant_primaries))
        relevant_secondaries = list(filter(lambda val : course_name in val['SecondaryCourses'], curricula))
        secondary_courses = list(map(lambda val : val['SecondaryCourses'], relevant_primaries))

        primary_courses = flat_map(lambda x: x, primary_courses)
        secondary_courses = flat_map(lambda x: x, secondary_courses)

        if course_name in primary_courses: primary_courses.remove(course_name)
        if course_name in secondary_courses: secondary_courses.remove(course_name)

        course['PrimaryCourses'] = primary_courses
        course['SecondaryCourses'] = secondary_courses

    return courses

def sieve_periods(periods, period_constraints):
    _periods = periods.copy()
    for constraint in period_constraints:
        periods.remove(constraint['Period'])

    return periods

def add_possible_periods(courses, periods, constraints):
    for course in courses:
        _periods = periods.copy()
        course_name = course['Course']
        exam_type = course['ExamType']
        exam_order = course.get('ExamOrder')
        filter_fun = lambda x: \
            (x.get('Part') == None or x['Part'] == exam_type) and \
            (exam_order == None or x['Exam'] == exam_order) \
            and x['Course'] == course_name
        forbidden_periods = list(filter(filter_fun, constraints))
        forbidden_periods = list(map(lambda x: x['Period'], forbidden_periods))

        for f_period in forbidden_periods: 
            if f_period in _periods: 
                _periods.remove(f_period)

        course['PossiblePeriods'] = _periods

    return courses