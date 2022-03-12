from validation.instance_loader import Instance
from validation.solution_loader import Solution
from validation.solution_validator import SolutionValidator
from validation.instance_validator import InstanceValidator
import json
import os
import sys
import numpy as np
# FIXME
# import pandas as pd
import warnings
from helpers import log

VERSION = "0.3.1"

force_overwrite = False

def validate_instance(instance_file, instance_format, output):
    '''
    Validates an instance and computes a few instance features.

    It requires an instance file to be specified, and optionally an instance format and an output file.
    '''
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return super(NpEncoder, self).default(obj)

    # open instance file
    with open(instance_file) as f:
        inst_content = f.read()

    if not instance_format:
        instance_format = instance_file.split(".")[-1]

    # activate validator, print result
    result = InstanceValidator.validate(inst_content, instance_format)
    if not output:
        return result
    else:
        if not os.path.isfile(output) or force_overwrite or click.confirm(f"The specified output file {output} exists, do you want to overwrite it"):
            with open(output, 'w') as f:
                f.write(json.dumps(result, indent=4, cls=NpEncoder))

def validate_solution(instance_file, solution_json, instance_format, solution_format, output, ignore_forbidden):
    '''
        Validates a solution against an instance and computes a few solution features.

        It requires an instance file and a solution file to be specified, and optionally an instance format, 
        a solution format and an output file.
    '''

    # open instance file
    with open(instance_file) as f:
        inst_content = f.read()

    # # open solution file
    # with open(solution_file) as f:
    #     sol_content = f.read()

    if not instance_format:
        instance_format = instance_file.split(".")[-1]

    # if not solution_format:
    #     solution_format = solution_file.split(".")[-1]

    sol_content = json.dumps(solution_json)

    # activate validator, print result
    result = SolutionValidator.validate(inst_content, instance_format, sol_content, solution_format, ignore_forbidden)
    if not output:
        return result
    else:
        if not os.path.isfile(output) or force_overwrite or click.confirm(f"The specified output file {output} exists, do you want to overwrite it"):
            with open(output, 'w') as f:
                f.write(json.dumps(result, indent=4))

# FIXME
# REQUIRES PANDAS, works with Python3 as of now
def instance_features(instances, output):
    '''
   Computes a table of instance features from a directory, according
    '''
    # TODO: remove later (currently a few divisions by zero occur in feature computation)
    warnings.filterwarnings("ignore")
    df = pd.DataFrame()
    with click.progressbar(instances, label='Computing features', file=sys.stderr, item_show_func=lambda f: os.path.basename(f) if f else '') as bar:
        for instance_file in bar:
            # open instance file
            with open(instance_file) as f:
                inst_content = f.read()

            instance_format = instance_file.split(".")[-1]

            # activate validator, accumulate result
            result = InstanceValidator.validate(inst_content, instance_format)
            df_row = pd.json_normalize(result['features'])
            df_row.insert(0, 'instance', os.path.basename(instance_file))
            df = pd.concat([df, df_row])
    
    df = df.sort_values('instance')
    
    if output:
        df.to_csv(output)
    else:
        print(df.to_string())