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

    # DO SOMETHING WITH THE DATA
    # THEN RETURN THE PROCESSED DATA

    periods = sieve_periods(periods, period_constraints)
    courses = flat_map_courses(courses)
    courses = add_possible_rooms(courses, rooms)
    courses = add_possible_periods(courses, periods, slots_per_day, event_period_constraints)
    courses = add_curricula_info(courses, curricula)

    return courses

"""
Main program -
This section runs the solution
"""
def main():
    print("Running solver on instance:", get_filepath())

    data = parse()
    instances = process(data)
    # To Do add possible RoomPeriodConstraint to the busy roomPeriodSets
    # To Do Take into account same day constraints
    # To Do check MinimumDistanceBetweenExams
    # To Do check MaxDistance MinDistance for WrittenOral
    solution = Solution(instances).solve()
    save_solution(get_filepath(), solution)

    print("Solver completed.")
    print("Solution instances are in solutions.")

"""
Execution
"""
if __name__ == '__main__':
    main()
