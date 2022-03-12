#!/usr/bin/env python3
from itertools import combinations, product
from collections import defaultdict, namedtuple
from validation.instance_loader import Instance
from validation.solution_loader import Solution
from validation.constants import *
from helpers import log

try:
    import coloredlogs
    coloredlogs.install()
except ImportError:
    pass

class SolutionValidator(object):
    '''Solution validation logic'''    

    @classmethod
    def validate(cls, inst_content, inst_format, sol_content, sol_format, ignore_forbidden=False):
        '''Takes a solution and an instance input as string, evaluates its validity, computes features'''

        # correctly handle None format
        if not inst_format:
            inst_format = Instance.default_format

        # correctly handle None format
        if not sol_format:
            sol_format = Solution.default_format      

        # initialize costs
        cost_components = {}
        cost = None

        instance = Instance(inst_content, inst_format)
        solution = Solution(sol_content, sol_format, instance)

        # basic consistency checkings for assignment
        if solution.assignments: # this might be not available when not a json / json pair is provided
            cls.check_assignments(instance, solution, ignore_forbidden)
        # Check constraints (tabled ones)
        cost_components['hard_components'] = { 
            'conflicts': 0,
            'multiple_room_occupation': 0,
            'precedence': 0,
            'forbidden_period': 0,
            'forbidden_room': 0,
            'forbidden_room_period': 0
        }
        cost_components['soft_components'] = { 
           'conflicts': 0,
           'min_directional_distance': 0,
           'max_directional_distance': 0,
           'min_undirectional_distance': 0,
           'max_undirectional_distance': 0,
           'period_preference': 0,
           'room_preference': 0,
           'undesired_room_period': 0
        }

        # timetable is now the reference, together with the matrix representation

        # pair of events constraints
        for e1, e2 in combinations(range(len(solution.timetable)), 2):
            p1, r1 = solution.timetable[e1] 
            p2, r2 = solution.timetable[e2]
            p1, r1 = p1 - 1, r1 - 1
            p2, r2 = p2 - 1, r2 - 1
            # 1. they are in the same period 
            if p1 == p2:
                if instance.conflicts[e1][e2] == -1:
                    cost_components['hard_components']['conflicts'] += instance.conflicts[e1][e2]
                    log().error(f"Conflicts between events {e1}@{p1} and {e2}@{p2}: prohibited")
                elif instance.conflicts[e1][e2] > 0:
                    log().warn(f"Soft conflict between events {e1}@{p1} and {e2}@{p2}: {instance.conflicts[e1][e2]}")
                    cost_components['soft_components']['conflicts'] += instance.conflicts[e1][e2]
                if instance.roomset_overlap[r1][r2] > 0:
                    log().error(f"Room clash for events {e1}@{p1}/{r1} and {e2}@{p2}/{r2}")
                    cost_components['hard_components']['multiple_room_occupation'] += 1
            # 2. a precedence between events is required
            if instance.precedence[e1][e2] > 0 and p1 >= p2:
                cost_components['hard_components']['precedence'] += instance.precedence[e1][e2]
                log().error(f"Precedence between events {e1}@{p1} and {e2}@{p2} not respected")
            # 3. distances
            # 3.1 directional distances
            if instance.precedence[e1][e2] > 0 and instance.distance_weight[e1][e2] > 0:
                if instance.min_distances[e1][e2] > 0 and p2 - p1 < instance.min_distances[e1][e2]:
                    cost_components['soft_components']['min_directional_distance'] += instance.distance_weight[e1][e2] * (instance.min_distances[e1][e2] - (p2 - p1))
                    log().warn(f"Directional min distance between events {e1}@{p1} and {e2}@{p2} ({instance.min_distances[e1][e2]}) not respected (weight {instance.distance_weight[e1][e2]})")
                if instance.max_distances[e1][e2] < instance.periods and p2 - p1 > instance.max_distances[e1][e2]:
                    cost_components['soft_components']['max_directional_distance'] += instance.distance_weight[e1][e2] * ((p2 - p1) - instance.max_distances[e1][e2])
                    log().warn(f"Directional max distance between events {e1}@{p1} and {e2}@{p2} ({instance.max_distances[e1][e2]}) not respected (weight {instance.distance_weight[e1][e2]})")
            # 3.2 undirectional distances
            elif instance.distance_weight[e1][e2] > 0:
                if instance.min_distances[e1][e2] > 0 and abs(p2 - p1) < instance.min_distances[e1][e2]:
                    cost_components['soft_components']['min_undirectional_distance'] += instance.distance_weight[e1][e2] * (instance.min_distances[e1][e2] - abs(p2 - p1))
                    log().warn(f"Min distance between events {e1}@{p1} and {e2}@{p2} ({instance.min_distances[e1][e2]}) not respected (weight {instance.distance_weight[e1][e2]})")
                if instance.max_distances[e1][e2] < instance.periods and abs(p2 - p1) > instance.max_distances[e1][e2]:
                    cost_components['soft_components']['max_undirectional_distance'] += instance.distance_weight[e1][e2] * (abs(p2 - p1) - instance.max_distances[e1][e2])
                    log().warn(f"Max distance between events {e1}@{p1} and {e2}@{p2} ({instance.max_distances[e1][e2]}) not respected (weight {instance.distance_weight[e1][e2]})")
        # single event
        for e, (p, r) in enumerate(solution.timetable):
            p, r = p - 1, r - 1
            # 4. forbidden periods
            if instance.event_period_constraints[e][p] == -1:
                cost_components['hard_components']['forbidden_period'] += 1
                log().error(f'Event {e}@{p} is assigned to a forbidden period')
            # 5. forbidden rooms
            if instance.event_room_constraints[e][r] == -1:
                cost_components['hard_components']['forbidden_room'] += 1
                log().error(f'Event {e}@{p}/{r} is assigned to a forbidden room')
            # 6. period preference costs
            if instance.event_period_constraints[e][p] > 0:
                cost_components['soft_components']['period_preference'] += instance.event_period_constraints[e][p]
                log().warn(f'Event {e}@{p} is assigned to an undesired/not preferred period')
            # 7. room preference costs
            if instance.event_room_constraints[e][r] > 0:
                cost_components['soft_components']['room_preference'] += instance.event_room_constraints[e][r]
                log().error(f'Event {e}@{p}/{r} is assigned to an undesired/not preferred room')
        # room
        for e, (p, r) in enumerate(solution.timetable):
            p, r = p - 1, r - 1
            # 8. forbidden rooms in a period
            if instance.room_period_constraints[r][p] == -1:
                cost_components['hard_components']['forbidden_room_period'] += 1
                log().error(f'Event {e}@{p}/{r} is assigned to a room that is forbidden in that period')
            # 9. undesired rooms in a period
            elif instance.room_period_constraints[r][p] > 0:
                cost_components['soft_components']['undesired_room_period'] += 1
                log().error(f'Event {e}@{p}/{r} is assigned to a room that is undesired in that period')

        cost_components['conflicts'] = 0
        cost_components['distances'] = 0

        cost_components['hard_violations'] = 0
        for component in cost_components['hard_components']:
            cost_components['hard_violations'] += cost_components['hard_components'][component] 

        cost_components['soft_violations'] = 0
        for component in cost_components['soft_components']:
            cost_components['soft_violations'] += cost_components['soft_components'][component]
        
        cost = 1000 * cost_components['hard_violations'] + cost_components['soft_violations']
        
        if solution.computed_cost is not None and solution.computed_cost != cost:
            log().error(f"The cost written in the solution file is {solution.computed_cost} while the validator has computed {cost}")

        return {
            'valid': cost_components['hard_violations'] == 0,
            'format': sol_format,
            'cost_components': cost_components,
            'cost': cost
        }

    @classmethod
    def check_assignments(cls, instance, solution, ignore_forbidden):
        for c, assignment in solution.assignments.items():
                assert c in instance.courses, f"Course {c} do not belong to the set of courses"
                course = instance.courses[c]
                assert len(assignment) == len(course.parts) * course.number_of_exams, f"Event assignment of course {course.name} are different than those expected {len(assignment)}/{len(course.parts) * course.number_of_exams}"
                for event in assignment:
                    if event.room is not None:
                        assert event.room in instance.rooms, "Room {event.room} do not belong to the set of rooms"
                        room = instance.rooms[event.room]
                    else:
                        room = None
                    assert event.period >= 0 and event.period < instance.periods
                    assert event.exam >= 0 and event.exam < course.number_of_exams           
             
        # Curriculum related violations and costs: these are a bit complex because the worst case has to be taken
        CurriculumClash = namedtuple('CurriculumClash', ['priority', 'common_periods'])
        CurriculumDistances = namedtuple('CurriculumDistance', ['priority', 'value', 'first', 'second'])
        curriculum_clashes = defaultdict(lambda: [])
        curriculum_distances = defaultdict(lambda: [])
        PRIMARY, MIXED, SECONDARY = 2, 1, 0
        MIN_DISTANCE_PRIMARY = instance.primary_primary_distance
        MIN_DISTANCE_PRIMARY_SECONDARY = instance.primary_secondary_distance
        for curriculum_name, curriculum in instance.curricula.items():
            for course_a, course_b in combinations(curriculum['primary'], 2):
                common_periods = set(a.period for a in solution.assignments[course_a.name]) & set(a.period for a in solution.assignments[course_b.name])
                if course_a.name > course_b.name:
                    course_a, course_b = course_b, course_a
                if common_periods:    
                    curriculum_clashes[(course_a.name, course_b.name)].append(CurriculumClash(PRIMARY, common_periods))
                    log().error(f'[curricula] curriculum {curriculum_name} clashing primary course {course_a.name} and {course_b.name}')
                # distances are between first_parts only
                for p_a, p_b in product(filter(lambda a: course_a.parts.index(a.part) == 0, solution.assignments[course_a.name]), filter(lambda a: course_b.parts.index(a.part) == 0, solution.assignments[course_b.name])):
                    if abs(p_a.period - p_b.period) < MIN_DISTANCE_PRIMARY:
                        d = MIN_DISTANCE_PRIMARY - abs(p_a.period - p_b.period)
                        curriculum_distances[(course_a.name, course_b.name)].append(CurriculumDistances(PRIMARY, d, p_a, p_b))
                        log().warn(f'[curricula] curriculum {curriculum_name} distance between course {course_a.name}@{p_a} and {course_b.name}@{p_b} as primary courses under minimum ({MIN_DISTANCE_PRIMARY} expected, found {abs(p_a.period - p_b.period)})')
            for course_a, course_b in product(curriculum['primary'], curriculum['secondary']):
                common_periods = set(a.period for a in solution.assignments[course_a.name]) & set(a.period for a in solution.assignments[course_b.name])
                if course_a.name > course_b.name:
                    course_a, course_b = course_b, course_a
                if common_periods:
                    curriculum_clashes[(course_a.name, course_b.name)].append(CurriculumClash(MIXED, common_periods))
                    log().warn(f'[curricula] curriculum {curriculum_name} clashing primary/secondary course {course_a.name} and {course_b.name} at {common_periods}')
                for p_a, p_b in product(filter(lambda a: course_a.parts.index(a.part) == 0, solution.assignments[course_a.name]), filter(lambda a: course_b.parts.index(a.part) == 0, solution.assignments[course_b.name])):
                    if abs(p_a.period - p_b.period) < MIN_DISTANCE_PRIMARY_SECONDARY:
                        d = MIN_DISTANCE_PRIMARY_SECONDARY - abs(p_a.period - p_b.period)
                        curriculum_distances[(course_a.name, course_b.name)].append(CurriculumDistances(MIXED, d, p_a, p_b))
                        log().warn(f'[curricula] curriculum {curriculum_name} distance between course {course_a.name}@{p_a} and {course_b.name}@{p_b} as primary/secondary courses under minimum (expected {MIN_DISTANCE_PRIMARY_SECONDARY}, found {abs(p_a.period - p_b.period)})')
            for course_a, course_b in combinations(curriculum['secondary'], 2):
                common_periods = set([a.period for a in solution.assignments[course_a.name]]) & set([a.period for a in solution.assignments[course_b.name]])
                if course_a.name > course_b.name:
                    course_a, course_b = course_b, course_a
                if common_periods:
                    curriculum_clashes[(course_a.name, course_b.name)].append(CurriculumClash(SECONDARY, common_periods))
                    log().warn(f'[curricula] curriculum {curriculum_name} clashing secondary course {course_a.name} and {course_b.name} at {common_periods}')

        for courses, clashes in curriculum_clashes.items():
            primary_clashes = set()
            mixed_clashes = set()
            secondary_clashes = set()
            for clash in clashes:
                if clash.priority == PRIMARY:
                    primary_clashes |= clash.common_periods
                elif clash.priority == MIXED:
                    mixed_clashes |= clash.common_periods
                else:
                    secondary_clashes |= clash.common_periods
            log().info(f'[curricula_summary] {courses[0]} {courses[1]} have {len(primary_clashes)} primary curriculum clashing')
            log().info(f'[curricula_summary] {courses[0]} {courses[1]} have {len(mixed_clashes - primary_clashes)} primary/secondary curriculum clashing')
            log().info(f'[curricula_summary] {courses[0]} {courses[1]} have {len(secondary_clashes - (mixed_clashes | primary_clashes))} secondary curriculum clashing')
        
        for courses, distances in curriculum_distances.items():
            primary_distance = defaultdict(lambda: 0)
            secondary_distance = defaultdict(lambda: 0)
            for distance in distances:
                if distance.priority == PRIMARY:
                    primary_distance[(distance.first, distance.second)] = max(primary_distance[(distance.first, distance.second)], distance.value)
                elif distance.priority == MIXED and (distance.first, distance.second) not in primary_distance:
                    secondary_distance[(distance.first, distance.second)] = max(secondary_distance[(distance.first, distance.second)], distance.value)            
            for value in primary_distance.values():
                log().warn(f'[curricula_summary] {courses[0]} {courses[1]} in the same primary curiculum have distance below minimum {value}')
            for value in primary_distance.values():
                log().warn(f'[curricula_summary] {courses[0]} {courses[1]} in the same primary/secondary curiculum have distance below minimum {value}')

        # Teacher related violations
        for course_a, course_b in combinations(solution.assignments, 2):
            course_a, course_b = instance.courses[course_a], instance.courses[course_b]
            if course_a.teacher != course_b.teacher:
                continue
            common_periods = set([a.period for a in solution.assignments[course_a.name]]) & set([a.period for a in solution.assignments[course_b.name]])
            if common_periods:
                log().error(f'[teacher] course {course_a.name} and {course_b.name} with same teacher {course_a.teacher} at same period(s) {common_periods}')
        used_rooms = defaultdict(lambda: [0] * instance.periods)
        for c, assignment in solution.assignments.items():
            course = instance.courses[c]
            for a in assignment:
                event_index = instance.events.index((course.name, a.exam, a.part))
                preferred_periods = [p for p, val in course.period_constraints[course.parts.index(a.part)].items() if any(True for v in val if v[0] == a.exam and v[1] == 'Preferred')]
                if preferred_periods and a.period not in preferred_periods:
                    log().warn(f'[preferred period] course {course.name}-{a.exam}-{a.part} (event {event_index}) not assigned to course preferred periods {preferred_periods} but to {a.period} instead')
                if a.period in course.period_constraints[course.parts.index(a.part)]:
                    forbidden = any(True for c in course.period_constraints[course.parts.index(a.part)][a.period] if c[0] == a.exam and c[1] == 'Forbidden')
                    undesired = any(True for c in course.period_constraints[course.parts.index(a.part)][a.period] if c[0] == a.exam and c[1] == 'Undesired')
                    if not ignore_forbidden and forbidden:
                        log().error(f'[forbidden period] course {course.name}-{a.exam}-{a.part} (event {event_index}) assigned to course forbidden period {a.period}')
                    if undesired:
                        log().warn(f'[undesired period] course {course.name}-{a.exam}-{a.part} (event {event_index}) assigned to course undesired period {a.period}')
                if a.period in instance.period_constraints:
                    forbidden = any(True for l in [instance.period_constraints[a.period]] if l == 'Forbidden')
                    undesired = any(True for l in [instance.period_constraints[a.period]] if l == 'Undesired')
                    if not ignore_forbidden and forbidden:
                        log().error(f'[forbidden period] course {course.name}-{a.exam}-{a.part} (event {event_index}) assigned to overall forbidden period {a.period}')
                    if undesired:
                        log().warn(f'[undesired period] course {course.name}-{a.exam}-{a.part} (event {event_index}) assigned to overall undesired period {a.period}')
                if a.room in course.room_constraints and course.room_constraints[a.room][course.parts.index(a.part)] is not None:
                    if not not ignore_forbidden and course.room_constraints[a.room][course.parts.index(a.part)] == 'Forbidden':
                        log().error(f'[forbidden room] course {course.name}-{a.exam}-{a.part} (event {event_index}) assigned to course forbidden room {a.room}')
                    if course.room_constraints[a.room][course.parts.index(a.part)] == 'Undesired':
                        log().warn(f'[undesired room] course {course.name}-{a.exam}-{a.part} (event {event_index}) assigned to course undesired room {a.room}')     
                if a.room is None:
                    if course.rooms[course.parts.index(a.part)] is not None:
                        log().error(f'[unsuitable room] course {course.name}/{a.part} has been assigned to no room, while requesting {course.rooms[course.parts.index(a.part)]}')
                    continue
                if course.rooms[course.parts.index(a.part)] is None:
                    log().error(f'[unsuitable room] course {course.name}/{a.part} has been assigned a room while requesting None')
                    continue
                required_rooms_type = course.rooms[course.parts.index(a.part)][0]
                required_rooms_number = course.rooms[course.parts.index(a.part)][1]
                suitable_assigned_rooms = 0
                room = instance.rooms[a.room]
                if a.period in room.constraints:
                    if not ignore_forbidden and room.constraints[a.period] == 'Forbidden':
                        log().warn(f'[forbidden room] course {course.name}/{a.part} assigned to room {a.room} forbidden at period {a.period}')
                    elif room.constraints[a.period] == 'Undesired':
                        log().warn(f'[undesired room] course {course.name}/{a.part} assigned to room {a.room} undesired at period {a.period}')
                if room.type != 'Composite':
                    used_rooms[room.name][a.period] += 1
                    if required_rooms_type == 'Small' or (required_rooms_type == 'Medium' and room.type != 'Small') or (required_rooms_type == 'Large' and room.type == 'Large'):
                        suitable_assigned_rooms += 1
                else:
                    for r in room.members:
                        used_rooms[r][a.period] += 1
                        if required_rooms_type == 'Small' or (required_rooms_type == 'Medium' and r.type != 'Small') or (required_rooms_type == 'Large' and r.type == 'Large'):
                            suitable_assigned_rooms += 1
                if suitable_assigned_rooms < required_rooms_number:
                    log().error(f'[unsuitable room] course {course.name}/{a.part} has been assigned to {suitable_assigned_rooms} rooms of required type, while requesting {course.rooms[course.parts.index(a.part)]}')
        for r, r_a in used_rooms.items():
            multiple_occupation = sum(max(0, u - 1) for u in r_a)
            if multiple_occupation:
                log().error(f'[multiple occupation] room {r} is assigned multiple times {multiple_occupation} at the same period')
        for c, assignment in solution.assignments.items():
            course = instance.courses[c]
            start_periods = list(a.period for a in assignment if a.part == course.parts[0]) # Relies on assignment ordering for the exam number
            for i, j in combinations(range(len(start_periods)), 2):
                if start_periods[j] < start_periods[i] + course.distances_between_exams[0]:
                    log().warn(f'[distance between exam] course {course.name} has exams at {start_periods[i]} and {start_periods[j]}, under min distance (expected {course.distances_between_exams[0]}, found {start_periods[i] - start_periods[j]})')
                if start_periods[j] > start_periods[i] + course.distances_between_exams[1]:
                    log().warn(f'[distance between exam] course {course.name} has exams at {start_periods[i]} and {start_periods[j]}, above max distance (expected {course.distances_between_exams[1]}, found {start_periods[j] - start_periods[i]})')
            for exam in range(course.number_of_exams):
                exam_periods = { a.part: a.period for a in assignment if a.exam == exam }
                for i, j in combinations(range(len(course.parts)), 2):
                    part_a = course.parts[i]
                    part_b = course.parts[j]
                    # FIXME: currently in the data it will be counted twice
                    # FIXME: eventually remove same day
                    if course.same_day:
                        day_part_a, day_part_b = exam_periods[part_a] // instance.slots_per_day, exam_periods[part_b] // instance.slots_per_day
                        if day_part_a != day_part_b or exam_periods[part_b] <= exam_periods[part_a]:
                            log().warn(f'[not same day] course {course.name} requires same day parts but given {day_part_a}@{exam_periods[part_a]}/{day_part_b}@{exam_periods[part_b]}')
                    else:
                        # min/max distance                    
                        if exam_periods[part_b] < exam_periods[part_a] + course.part_distances[i][0]:
                            log().warn(f'[distance between parts] course {course.name} has exam parts at {exam_periods[part_a]} and {exam_periods[part_b]}, under min distance (expected {course.part_distances[i][0]}, found {exam_periods[part_b] - exam_periods[part_a]})')
                        if exam_periods[part_b] > exam_periods[part_a] + course.part_distances[i][1]:
                            log().warn(f'[distance between parts] course {course.name} has exam parts at {exam_periods[part_a]} and {exam_periods[part_b]}, above max distance (expected {course.part_distances[i][1]}, found {exam_periods[part_b] - exam_periods[part_a]}')


