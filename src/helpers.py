import time
import json
import os
import sys
import string
import random
from pathlib import Path
import logging

# import imp
# try:
#     imp.find_module('names')
#     import names
#     names_imported = True
# except ImportError:
#     names_imported = False

"""
Helper methods -
This section contains all helper methods, which aid in 
file manipulation, enumeration, system os paths, etc.
"""

def read_file(filepath):
    try:
        with open(filepath) as file:
            data = json.load(file)
        return data
    except:
        print("Cannot open file! Might not exist.")
        return None

def save_file(filepath, data, folder = 'modified_instances'):
    Path(folder).mkdir(parents=True, exist_ok=True)
    try:
        with open(filepath, 'w+', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        print("Cannot write to file!")
        return False

def get_filepath(default_file = 'instances/D1-1-16.json'):
    if len(sys.argv) > 1: return sys.argv[1]
    return default_file

pluck = lambda dict, *args: (dict.get(arg) for arg in args)

def random_range(threshold = 20, size = 5):
    random_size = random.randint(0, size)
    threshold_range = range(1, threshold)
    return random.sample(threshold_range, random_size)

def map_filter(fun, dict):
    def some(value): return value != None
    list(map(fun, dict))

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
    return f'{folder}/SOLUTION-{filename}'

def flat_map(f, xs):
    ys = []
    for x in xs:
        ys.extend(f(x))
    return ys

def tprint(*msg):
    now = time.strftime("%H:%M:%S")
    print(f"[{now}]", *msg)

def ordered_shuffle(courses):
    _courses = courses.copy()
    random.shuffle(_courses)
    ordered_courses = sorted(_courses, key=len, reverse=True)
    return ordered_courses

def grouped_shuffle(courses):
    _courses = courses.copy()
    shuffled_courses = []
    light_courses = []
    heavy_courses = []

    while len(_courses) > 0:
        _course = _courses.pop(0)
        if len(_course) > 2:
            heavy_courses.append(_course)
        else:
            light_courses.append(_course)

    random.shuffle(heavy_courses)
    random.shuffle(light_courses)
    shuffled_courses = heavy_courses + light_courses

    return shuffled_courses

def solve_all_arg():
    return len(sys.argv) > 1 and sys.argv[1] == 'all'

def log(filename = None, disabled = True):
    if (filename is not None):
        logging.basicConfig(
            filename=filename,
            format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
            filemode='w',
            level=logging.INFO
        )
    log = logging.getLogger('costs')
    log.disabled = disabled
    return log

def flatten(some_list):
    def process(sth):
        if isinstance(sth, (list, tuple, set, range)):
            for sub in sth:
                yield from process(sub)
        else:
            yield sth

    return list(process(some_list))