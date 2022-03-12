#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from .instance_loader import Instance
import numpy as np

class InstanceValidator(object): 
    '''Instance validation logic'''    
    # 
    @classmethod
    def my_assert_eq(cls, v1, v2, message):
        if v1 != v2:
            raise ValueError(message.format(v1, v2))
            
    @classmethod
    def my_assert_leq(cls, v1, v2, message):
        if v1 > v2:
            raise ValueError(message.format(v1, v2))
    
    @classmethod
    def validate(cls, inst_content, inst_format):
        '''Takes an instance as input string, evaluates its validity, computes features'''

        # correctly handle None format
        if not inst_format:
            inst_format = Instance.default_format
            
        # initialize feature map
        features = {}

        instance = Instance(inst_content, inst_format) 
        if hasattr(instance, 'courses'):
            features['courses'] = len(instance.courses)
        else:
            features['courses'] = np.nan
        features['periods'] = instance.periods
        features['events'] = len(instance.events)
        if hasattr(instance.rooms, 'values'):
            features['rooms'] = len(list(filter(lambda r: r.type != 'Composite', instance.rooms.values())))
            features['composite_rooms'] = len(list(filter(lambda r: r.type == 'Composite', instance.rooms.values())))
        else:
            features['rooms'] = len(instance.rooms)
            features['composite_rooms'] = np.nan    
        if hasattr(instance, 'slots_per_day'):
            features['slots_per_day'] = instance.slots_per_day
        
        # semantically check courses and compute a period density per course (the harmonic mean of the periods available for each exam)
        available_periods = []
        n = 0
        empty_domains = []

        if hasattr(instance, 'courses'):
            for course in instance.courses.values():
                for exam in range(course.number_of_exams):
                    for part in range(len(course.parts)):
                        # TODO: what if there is no available period
                        available_periods.append(len(course.available_periods[exam][part]) / instance.periods)
                        n += 1
                        if course.available_periods[exam][part] == set():
                            empty_domains.append((course.name, exam, course.parts[part]))     
        else:
            for c in instance.event_period_constraints:
                available_periods.append((instance.periods - c.count(-1)) / instance.periods)
            n = len(instance.events)
        features['average_ratio_of_available_periods_per_event'] = np.mean(available_periods)
    
        if hasattr(instance, 'curricula'):
            overall_sum_of_curricula = 0
            features['curriculum_periods_density'] = { 'primary': 0, 'secondary': 0, 'overall': 0 }
            for curriculum in instance.curricula.values():
                for t in ('primary', 'secondary'):
                    features['curriculum_periods_density'][t] += sum(map(lambda c: c.number_of_exams * len(c.parts), curriculum[t])) / instance.periods
            features['curriculum_periods_density']['overall'] = sum(features['curriculum_periods_density'][t] for t in ('primary', 'secondary'))
            features['curriculum_periods_density'] = { t: features['curriculum_periods_density'][t] / len(instance.curricula) for t in features['curriculum_periods_density'].keys() }

        features['roomed_events'] = { 'total': len(instance.roomed_event), 'ratio': len(instance.roomed_event) / n }

        p = instance.periods
        # Room requests 
        strict_room_demand = []
        relaxed_room_demand = []
        total_room_demand = { 'Small': 0, 'Medium': 0, 'Large': 0 }

        if hasattr(instance, 'courses'):
            for course in instance.courses.values():
                for part in range(len(course.parts)):
                    if course.rooms[part] is None:
                        continue
                    type, number = course.rooms[part]
                    total_room_demand[type] += number
                    strictly_compatible_rooms = set(filter(lambda r: r.compatible_room(type, number) and (type == r.type or r.type == 'Composite'), instance.rooms.values()))
                    strict_room_demand.append(number / len(strictly_compatible_rooms))                    
                    relaxed_compatible_rooms = set(filter(lambda r: r.compatible_room(type, number), instance.rooms.values()))
                    relaxed_room_demand.append(number / len(relaxed_compatible_rooms))
            features['average_strict_room_demand_per_event'] = np.mean(strict_room_demand)
            features['average_relaxed_room_demand_per_event'] = np.mean(relaxed_room_demand)
            for type in ('Small', 'Medium', 'Large'):
                if total_room_demand[type] == 0:
                    features[f'overall_{type.lower()}_room_demand_per_period'] = 0.0
                else:
                    features[f'overall_{type.lower()}_room_demand_per_period'] = total_room_demand[type] / (p * len(set(filter(lambda r: r.compatible_room(type, number) and type == r.type, instance.rooms.values()))))
        else:
            # TODO: this is a different stuff
            pass

        # min, max and average distance between events
        features['min_distance'] = { 'min': np.min(instance.min_distances), 'max': np.max(instance.min_distances), 'average': np.mean(instance.min_distances) }
        max_distances = [v for v in np.array(instance.max_distances).flatten() if v < p]
        if max_distances:
            features['max_distance'] = { 'min': np.min(max_distances), 'max': np.max(max_distances), 'average': np.mean(max_distances) }
        else:
            features['max_distance'] = { 'min': np.nan, 'max': np.nan, 'average': np.nan }

        # conflicts
        n = len(instance.events)
        features['hard_conflict_density'] = np.sum(1.0 for v in np.array(instance.conflicts).flatten() if v == -1) / (n * (n - 1) / 2)
        features['soft_conflict_density'] = np.sum(1.0 for v in np.array(instance.conflicts).flatten() if v > 0) / (n * (n - 1) / 2)

        # weights
        features['average_distance_weights'] = np.mean(instance.distance_weight)

        # event period constraints    
        features['hard_event_period_constraints_density'] = np.sum(1.0 for v in np.array(instance.event_period_constraints).flatten() if v == -1) / (n * p)
        features['soft_event_period_constraints_density'] = np.sum(1.0 for v in np.array(instance.event_period_constraints).flatten() if v > 0) / (n * p)

        r = len(instance.rooms)

        if r > 0:
            # event room constraints
            features['hard_event_room_constraints_density'] = np.sum(1.0 for v in np.array(instance.event_room_constraints).flatten() if v == -1) / (n * r)
            features['soft_event_room_constraints_density'] = np.sum(1.0 for v in np.array(instance.event_room_constraints).flatten() if v > 0) / (n * r)

            # room period constraints
            features['hard_room_period_constraints_density'] = np.sum(1.0 for v in np.array(instance.room_period_constraints).flatten() if v == -1) / (r * p)
            features['soft_room_period_constraints_density'] = np.sum(1.0 for v in np.array(instance.room_period_constraints).flatten() if v > 0) / (r * p)

            # roomset overlap
            features['roomset_overlap_density'] = np.sum(instance.roomset_overlap) / (r * (r - 1) / 2)
        else:
            features['hard_event_room_constraints_density'] = 0.0
            features['soft_event_room_constraints_density'] = 0.0
            features['hard_room_period_constraints_density'] = 0.0
            features['soft_room_period_constraints_density'] = 0.0
            features['roomset_overlap_density'] = 0.0

        # precedence constraints
        features['precedence_density'] = np.sum(instance.precedence) / (n * (n - 1) / 2)

        r = {
            'valid': not empty_domains,
            'format': inst_format,
            'features': features
        }        
        if empty_domains:
            r['reason'] = { 
                "message": ["Course {}, exam {}, part {} has an empty set of available periods".format(*e) for e in empty_domains]
            }
        return r

def main():
    '''Entry point for when the validator is called from the command line, returns valid JSON'''

    # setup CLI
    parser = argparse.ArgumentParser(description='Instance validator')
    parser.add_argument('--inst-file', '-i', required = True, type = str, help='instance file')
    parser.add_argument('--inst-format', '-f', required = False, type = str, choices = Instance.formats, default=Instance.default_format, help='instance format name')
    args = parser.parse_args()

    with open(args.inst_file) as f:
        inst_content = f.read()
    # activate validator, print result
    result = InstanceValidator.validate(inst_content, args.inst_format)
    # print(json.dumps(result, indent=4))


# when invoked from the command line, call main()
if __name__ == '__main__':
    main()
