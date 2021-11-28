from helpers import *
from enums import *
from preprocess import *

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

    hard_constraints = list(filter(lambda val: val['Level'] == 'Forbidden', constraints))

    # DO SOMETHING WITH THE DATA
    # THEN RETURN THE PROCESSED DATA
    courses = flat_map_courses(courses)
    courses = add_possible_rooms(courses, rooms)
    courses = add_possible_periods(courses, rooms)
    courses = add_curricula_info(courses, curricula)
    processed_data = data
    return courses

def solve(instances):
    return instances

"""
Main program -
This section runs the solution
"""
def main():
    print("Running solver on instance:", get_filepath())

    data = parse()
    instances = process(data)
    solution = solve(instances)
    save_solution(get_filepath(), solution)

    print("Solver completed.")
    print("Solution instances are in solutions.")

"""
Execution
"""
if __name__ == '__main__':
    main()
