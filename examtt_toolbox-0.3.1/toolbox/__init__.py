import click
from toolbox.instance_loader import Instance
from toolbox.solution_loader import Solution
from toolbox.solution_validator import SolutionValidator
from toolbox.instance_validator import InstanceValidator
import logging
import json
import os
import sys
import numpy as np
import pandas as pd
import warnings

log = logging.getLogger('costs')

VERSION = "0.3.1"

force_overwrite = False

@click.group()
@click.version_option(version=VERSION)
@click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode, providing a detailed log')
@click.option('-f', '--force', is_flag=True, default=False, help='Force overwriting all outputs if provided')
@click.pass_context
def cli(ctx, verbose, force):
    """
        Italian Examination Timetabling problem toolbox.

        This package provides a few utilities for handling the Italian Examination Timetabling problem.
        Namely, it allows to validate a problem instance or a solution against an instance. 


        Currently it supports the following operations:

        examtt_toolbox validate-instance

        Given an instance in `json` format it states whether the instance is valid and computes a few 
        instance features.

        examtt_toolbox validate-solution

        Given an instance, in `json` format, and a solution either in `json` or in `datazinc` format, it verifies  whether the solution 
        is valid w.r.t. the instance and computes a few solution features.

        You can get more detailed usage information by issuing the above commands followed by the `--help` command line flag.
    """
    global force_overwrite
    if not verbose:
        log.setLevel(logging.ERROR)
    else:
        log.setLevel(logging.INFO)
    if force:
        force_overwrite = force

@cli.command()
@click.argument('instance-file', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True), required=True)
@click.option('-if', '--instance-format', type=click.Choice(['json']))
@click.option('-o', '--output', type=click.Path(file_okay=True, dir_okay=False, writable=True))
@click.pass_context
def validate_instance(ctx, instance_file, instance_format, output):
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
        print(json.dumps(result, indent=4, cls=NpEncoder))
    else:
        if not os.path.isfile(output) or force_overwrite or click.confirm(f"The specified output file {output} exists, do you want to overwrite it"):
            with open(output, 'w') as f:
                f.write(json.dumps(result, indent=4, cls=NpEncoder))


@cli.command()
@click.argument('instance-file', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True), required=True)
@click.argument('solution-file', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True), required=True)
@click.option('-if', '--instance-format', type=click.Choice(['json', 'dzn']))
@click.option('-sf', '--solution-format', type=click.Choice(['json', 'sol']))
@click.option('-o', '--output', type=click.Path(file_okay=True, dir_okay=False, writable=True))
@click.option('--ignore-forbidden', is_flag=True, default=False, help='Ignores forbidden periods/rooms in validation (temporary)')
@click.pass_context
def validate_solution(ctx, instance_file, solution_file, instance_format, solution_format, output, ignore_forbidden):
    '''
        Validates a solution against an instance and computes a few solution features.

        It requires an instance file and a solution file to be specified, and optionally an instance format, 
        a solution format and an output file.
    '''

    # open instance file
    with open(instance_file) as f:
        inst_content = f.read()

    # open solution file
    with open(solution_file) as f:
        sol_content = f.read()

    if not instance_format:
        instance_format = instance_file.split(".")[-1]

    if not solution_format:
        solution_format = solution_file.split(".")[-1]

    # activate validator, print result
    result = SolutionValidator.validate(inst_content, instance_format, sol_content, solution_format, ignore_forbidden)
    if not output:
        print(json.dumps(result, indent=4))
    else:
        if not os.path.isfile(output) or force_overwrite or click.confirm(f"The specified output file {output} exists, do you want to overwrite it"):
            with open(output, 'w') as f:
                f.write(json.dumps(result, indent=4))

@cli.command()
@click.argument('instance-file', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True), required=True)
@click.option('-if', '--instance-format', type=click.Choice(['json', 'dzn']))
@click.option('-of', '--output-format', type=click.Choice(['dzn']), default='dzn')
@click.option('-o', '--output', type=click.Path(file_okay=True, dir_okay=False, writable=True))
@click.pass_context
def translate_instance(ctx, instance_file, instance_format, output_format, output):
    '''
    Translates a json instance into its dzn representation
    '''
    # open instance file
    with open(instance_file) as f:
        inst_content = f.read()

    if not instance_format:
        instance_format = instance_file.split(".")[-1]

    instance = Instance(inst_content, instance_format)

    if not output:
        print(instance.to_dzn())
    else:
        if not os.path.isfile(output) or force_overwrite or click.confirm(f"The specified output file {output} exists, do you want to overwrite it"):
            with open(output, 'w') as f:
                f.write(instance.to_dzn())

@cli.command()
@click.argument('instances', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, readable=True), required=True, nargs=-1)
@click.option('-o', '--output', type=click.Path(file_okay=True, dir_okay=False, writable=True), help='Output to a csv file')
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



def main():
    cli(obj={})