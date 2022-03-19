import time
from helpers import *
from enums import *
from preprocess import *
from solution import *
import math

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
    courses = add_curricula_info(courses, curricula, primary_primary_distance, slots_per_day)
    courses = add_same_teacher_courses(courses)
    courses = order_course_by_constraints(courses)
    courses = group_by_exams_and_parts(courses)
    # courses = group_by_course(courses)

    return courses, hard_constraints, constraints

"""
Run a greedy search -
This section contains the main logic to run a greedy search from 
the initial solution by mutation operators
"""
def run_greedy_search(instances, hard_constraints, instance_path, constraints, attempts = 1000):
    solution = Solution.try_solving(instances, hard_constraints, instance_path=instance_path, constraints=constraints)

    best_cost = float('inf')
    last_solution = solution

    for i in range(0, attempts):
        mutated_solution = Solution.try_mutating(last_solution)
        if (mutated_solution == None): continue

        # save_solution(instance_path, mutated_solution.export(), True)

        if (mutated_solution.cost < best_cost):
            best_cost = mutated_solution.cost
            last_solution = mutated_solution
            print(best_cost)

"""
Run a simluated annealing search -
This section contains the main logic to run a simluated annealing search from 
the initial solution by mutation operators
"""
def sim_annealing(
    instances, 
    hard_constraints,
    instance_path,
    constraints,
    maxsteps=1000,
    debug=True
):
    def acceptance_probability(cost, new_cost, temperature):
        if new_cost < cost:
            return 1
        else:
            p = math.exp(- (new_cost - cost) / temperature)
            return p
    def temperature(fraction):
        return max(0.01, min(1, 1 - fraction))

    state = Solution.try_solving(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    cost = state.cost
    states, costs = [state], [cost]
    for step in range(maxsteps):
        fraction = step / float(maxsteps)
        T = temperature(fraction)
        new_state = Solution.try_mutating(state)
        new_cost = new_state.cost
        if debug: print("Step #{:>2}/{:>2} : T = {:>4.3g}, cost = {:>4.3g}, new_cost = {:>4.3g} ...".format(step, maxsteps, T, cost, new_cost))
        if acceptance_probability(cost, new_cost, T) > random.random():
            state, cost = new_state, new_cost
            states.append(state)
            costs.append(cost)
            print(cost)
            # state.validate()
            # print(state.validation_results["cost"])
    return state

"""
Solve one instance -
This section contains the main logic to solve one instance
"""
def run_solver(instance_path):
    start_time = time.time()
    tprint("Running solver on instance:", instance_path)

    data = parse(instance_path)
    instances, hard_constraints, constraints = process(data)
    # save_file("preprocess.json", instances, ".")

    solution = Solution.try_solving(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    save_solution(instance_path, solution.export())

    end_time = time.time()

    tprint("Solver completed. Check solutions folder.")
    tprint(f"Completed in {end_time-start_time:.2f}s.")
    run_greedy_search(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    sim_annealing(instances, hard_constraints, instance_path=instance_path, constraints=constraints)

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
