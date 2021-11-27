import json
import os
import sys
import string
import random
from pathlib import Path

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