from helpers import *
from enums import *

"""
Parsing method -
This method contains the main instance parsing logic
"""
def parse(filepath = None):
    filepath = filepath or get_filepath()
    data = read_file(filepath)
    if not data: return None

    return data

def save_solution(filepath, data):
    folder = 'solutions'
    filename = os.path.basename(filepath)
    save_file(f'{folder}/SOLUTION-{filename}', data, folder)

def expand_exams(courses, flat_courses, course):
    exam_type = course['ExamType']
    if exam_type == "WrittenAndOral":
        written_course = course.copy();
        written_course['ExamType'] = 'Written'
        flat_courses.append(written_course)
        oral_course = course.copy();
        oral_course['ExamType'] = 'Oral'
        flat_courses.append(oral_course)
    else:
        new_course = course.copy();
        flat_courses.append(new_course)
        flat_done = True

def flat_map_courses(courses):
    print(len(courses))
    flat_courses = []

    while (len(courses) != 0):
        flat_done = False
        course = courses.pop()
        number_of_exams = course['NumberOfExams']

        for i in range(0, number_of_exams):
            course['NumberOfExams'] = 1;
            expand_exams(courses, flat_courses, course)
            flat_done = True

        if not flat_done: flat_courses.append(course)

    print(len(flat_courses))

    return flat_courses

def add_possible_rooms(courses, rooms):
    for course in courses:
        req_rooms = course['RoomsRequested']
        room_numbers = req_rooms['Number']

        if room_numbers == 0:
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
                match = room.get('Members') and len(room['Members']) == room_numbers
                if match: return room['Room']
                return None
            course['PossibleRooms'] = list(filter(None, list(map(fun, rooms))))

    return courses

"""
Process method -
This method contains the main instance processing and modeling logic
"""
def process(data):
    if not data: return None

    courses, periods, \
    slots_per_day, teachers, \
    constraints, rooms, curricula, \
    primary_primary_distance = \
    pluck(data, 
        'Courses', 'Periods', 'SlotsPerDay', 
        'Teachers', 'Constraints', 'Rooms', 
        'Curricula', 'PrimaryPrimaryDistance'
    )

    # DO SOMETHING WITH THE DATA
    # THEN RETURN THE PROCESSED DATA
    courses = flat_map_courses(courses)
    courses = add_possible_rooms(courses, rooms)
    processed_data = data
    return courses

def save_solution(filepath, data):
    folder = 'solutions'
    filename = os.path.basename(filepath)
    save_file(f'{folder}/SOLUTION-{filename}', data, folder)


"""
Main program -
This section runs the solution
"""
def main():
    print("Running solver on instance:", get_filepath())
    data = process(parse())
    save_solution(get_filepath(), data)
    print("Solver completed.")
    print("Solution instances are in solutions.")

"""
Execution
"""
if __name__ == '__main__':
    main()
