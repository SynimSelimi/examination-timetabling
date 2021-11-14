from helpers import *

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
    processed_data = data
    return data

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
