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
def greedy_search(instances, hard_constraints, instance_path, constraints, attempts = 2500):
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
            if i % 10 == 0:
                last_solution.validate()
                print(best_cost, last_solution.validation_results['cost'], last_solution.validation_results['valid'])

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
    debug=False
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
            if step % 10 == 0:
                state.validate()
                print(state.cost, state.validation_results['cost'], state.validation_results['valid'])
    return state

"""
Run hill climbing search -
This section contains the main logic to run a hill climbing search from 
the initial solution by mutation operators
"""
def hillclimbing(instances, hard_constraints, instance_path, constraints, old_solution=None):
    solution = None

    def get_best_neighbour(solution):
        best_cost = solution.cost
        best_solution = solution

        for i in range(0, 45):
            mutated_solution = None
            while mutated_solution == None:
                mutated_solution = Solution.try_mutating(best_solution)

            if (mutated_solution.cost < best_cost):
                best_cost = mutated_solution.cost
                best_solution = mutated_solution
        return best_solution

    while solution == None:
        if old_solution == None:
            solution = Solution.try_solving(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
        else:
            solution = old_solution
    neighbour = get_best_neighbour(solution)
    last_solution = solution

    while neighbour.cost < solution.cost:
        solution = neighbour
        neighbour = get_best_neighbour(neighbour)

    return solution

"""
Run an interated local search -
This section contains the main logic to run an interated local search from 
the initial solution by mutation operators
"""
def iterated_local_search(
    instances, 
    hard_constraints,
    instance_path,
    constraints,
    iterations=15,
):
    def new_home_base(home, new):
        EXPLORATION = 0.10
        better_home_solution = home.cost < new.cost
        if (better_home_solution == True and random.random() > EXPLORATION):
            return home
        else:
            return new

    best_solution = hillclimbing(instances, hard_constraints, instance_path, constraints, None)
    home = best_solution
    working_solution = best_solution
    best_solutions = []

    for n in range(iterations):
        perturbed_solution = None
        while perturbed_solution == None:
            perturbed_solution = Solution.try_mutating(home, perturb=True)

        working_solution = hillclimbing(None, None, None, None, perturbed_solution)
        home = new_home_base(home, working_solution)

        print(home.cost)
        if home.cost < best_solution.cost:
            best_solution = home
            best_solutions.append(home)
        
        
        if best_solution.cost == 0:
            break

        # test_evaluation(working_solution)
            # if n % 2 == 0:
            #     best_solution.validate()
            #     print(best_solution.cost, best_solution.validation_results['cost'], best_solution.validation_results['valid'])
    
    return best_solution

def test_evaluation(solution):
    # {
    #    "hard_components":{
    #       "conflicts":0,
    #       "multiple_room_occupation":0,
    #       "precedence":0,
    #       "forbidden_period":0,
    #       "forbidden_room":0,
    #       "forbidden_room_period":0
    #    },
    #    "soft_components":{
    #       "conflicts":11,
    #       "min_directional_distance":0,
    #       "max_directional_distance":45,
    #       "min_undirectional_distance":0,
    #       "max_undirectional_distance":0,
    #       "period_preference":4,
    #       "room_preference":0,
    #       "undesired_room_period":0
    #    },
    #    "conflicts":0,
    #    "distances":0,
    #    "hard_violations":0,
    #    "soft_violations":60
    # }
    solution.validate()
    base_cost = solution.cost
    validator_cost = \
        solution.validation_results['cost_components']['soft_components']['conflicts']
    
    if (base_cost != validator_cost):
        print("FALSE EVALUATION", base_cost, validator_cost, abs(base_cost - validator_cost))
    else:
        print("TRUE EVALUATION", base_cost, validator_cost, abs(base_cost - validator_cost))

def run_ils_with_timeout(instances, hard_constraints, instance_path, constraints):
    start = time.time()
    best_result = None
    best_score = 999999999
    average_score = 0
    iterations = 0

    while True:
        result = iterated_local_search(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
        end = time.time()
        duration = end - start
        if (result.cost < best_score):
            best_score = result.cost
            best_result = result
        print(best_score)
        # test_evaluation(result)
        average_score += result.cost
        iterations += 1
        if (duration > 600 or best_score == 0): break

    best_result.validate()
    best_result_json = best_result.export()
    best_result_json['Duration_in_s'] = (end - start)
    best_result_json['Iterations'] = iterations
    best_result_json['Average_score'] = average_score / iterations
    save_solution(instance_path, best_result_json)
    print("BEST", best_result.cost, best_result.validation_results['cost'], best_result_json['Duration_in_s'])
    print("average_score", average_score/iterations)

def measure(instances, hard_constraints, instance_path, constraints):
    start = time.time()
    best_result = None
    best_score = 999999999
    average_score = 0
    iterations = 0

    while True:
        result = iterated_local_search(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
        end = time.time()
        if (result.cost < best_score):
            best_score = result.cost
            best_result = result
        print(best_score)
        test_evaluation(result)
        average_score += result.cost
        iterations += 1
        if ((end - start) > 60): break

    best_result.validate()
    save_solution(instance_path, best_result.export())
    print("BEST", best_score, best_result.validation_results['cost'])
    print("average_score", average_score/iterations)

"""
Solve one instance -
This section contains the main logic to solve one instance
"""
def run_solver(instance_path):
    # start_time = time.time()
    tprint("Running solver on instance:", instance_path)

    data = parse(instance_path)
    instances, hard_constraints, constraints = process(data)
    # save_file("preprocess.json", instances, ".")
    # solution = Solution.try_solving(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    # save_solution(instance_path, solution.export())
    # end_time = time.time()

    run_ils_with_timeout(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    # measure(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    # iterated_local_search(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    # hillclimbing(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    # greedy_search(instances, hard_constraints, instance_path=instance_path, constraints=constraints)
    # sim_annealing(instances, hard_constraints, instance_path=instance_path, constraints=constraints)

    tprint("Solver completed. Check solutions folder.")
    # tprint(f"Completed in {end_time-start_time:.2f}s.")

"""
Solve all instances -
This section contains the main logic to solve all instances,
which are present in the instances folder
"""
def solve_all_instances(folder = 'instances', resolve_all = False):
    solved_instances = []

    if resolve_all:
        for _, _, files in os.walk('solutions'):
            for filename in files:
                instance = '-'.join(filename.split('-')[1:])
                solved_instances.append(instance)

    for _, _, files in os.walk(folder):
        print("Solving all instances.")
        for filename in files:
            if filename in solved_instances: continue
            run_solver(f'{folder}/{filename}')

def print_results(folder = 'solutions'):
    results = []
    for _, _, files in os.walk(folder):
        for filename in files:
            solution = '-'.join(filename.split('-')[1:])
            f = open(f"{folder}/{filename}")
            data = json.load(f)
            results.append(f"{solution}\t{data['Average_score']}\t{data['Validation']['cost']}\t{data['Duration_in_s']}")

    print("\n".join(results))


"""
Main program -
This section runs the solver
"""
def main():
    if solve_all_arg(): solve_all_instances(resolve_all = True)
    else: run_solver(get_filepath())

"""
Execution
"""
if __name__ == '__main__':
    main()
    print_results()
