import time
from helpers import *
from enums import *
from preprocess import *
from solution import *

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

    periods = list(range(0, periods))
    hard_constraints = list(filter(lambda val: val['Level'] == 'Forbidden', constraints))
    period_constraints = list(filter(lambda val: val['Type'] == 'PeriodConstraint', hard_constraints))
    event_period_constraints = list(filter(lambda val: val['Type'] == 'EventPeriodConstraint', hard_constraints))
    event_room_constraints = list(filter(lambda val: val['Type'] == 'EventRoomConstraint', hard_constraints))

    periods = sieve_periods(periods, period_constraints)
    courses = flat_map_courses(courses)
    courses = add_possible_rooms(courses, rooms, event_room_constraints)
    courses = add_possible_periods(courses, periods, event_period_constraints)
    courses = add_curricula_info(courses, curricula)
    courses = add_same_teacher_courses(courses)
    courses = order_course_by_constraints(courses)
    courses = group_by_exams_and_parts(courses)
    # courses = group_by_course(courses)

    return courses, hard_constraints

"""
Solve one instance -
This section contains the main logic to solve one instance
"""
def run_solver(instance_path):
    start_time = time.time()
    tprint("Running solver on instance:", instance_path)

    data = parse(instance_path)
    instances, hard_constraints = process(data)
    # save_file("preprocess.json", instances, ".")
    solution = Solution.try_solving(instances, hard_constraints)
    save_solution(instance_path, solution.export())
    solution.mutate_rooms()
    save_solution(f"{instance_path}", solution.export(), True)

    end_time = time.time()

    tprint("Solver completed. Check solutions folder.")
    tprint(f"Completed in {end_time-start_time:.2f}s.")

"""
Solve all instances -
This section contains the main logic to solve all instances,
which are present in the instances folder
"""
def solve_all_instances(folder = 'instances'):
    for _, _, files in os.walk(folder):
        print("Solving all instances.")
        for filename in files: run_solver(f'{folder}/{filename}')

"""
Main program -
This section runs the solver
"""
def main():
    if solve_all_arg(): solve_all_instances()
    else: run_solver(get_filepath())

"""
Execution
"""
if __name__ == '__main__':
    main()
