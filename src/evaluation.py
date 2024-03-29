from collections import defaultdict
from helpers import flatten

UNDESIRED_PERIOD_WEIGHT = 10
INDIFFERENT_PERIOD_WEIGHT = 2

UNDESIRED_ROOM_WEIGHT = 5
INDIFFERENT_ROOM_WEIGHT = 1

WRITTEN_ORAL_DISTANCE_WEIGHT = 15
SAME_COURSE_DISTANCE_WEIGHT = 12
PRIMARY_PRIMARY_DISTANCE_WEIGHT = 2
PRIMARY_SECONDARY_DISTANCE_WEIGHT = 2
PRIMARY_SECONDARY_CONFLICT_WEIGHT = 5
SECONDARY_SECONDARY_CONFLICT_WEIGHT = 1
SECONDARY_SECONDARY_DISTANCE_WEIGHT = 1


# UNDESIRED_PERIOD_WEIGHT
# INDIFFERENT_PERIOD_WEIGHT
# UNDESIRED_ROOM_WEIGHT
# INDIFFERENT_ROOM_WEIGHT
def room_and_period_costs(assignments, undesired, preferred):
  cost = 0
  constraints = defaultdict(dict)
  undesired_periods = list(filter(lambda val: val['Type'] == 'PeriodConstraint', undesired))
  undesired_periods = list(map(lambda x: x.get('Period'), undesired_periods))
  undesired_er = list(filter(lambda val: val['Type'] == 'EventRoomConstraint', undesired))
  preferred_er = list(filter(lambda val: val['Type'] == 'EventRoomConstraint', preferred))
  undesired_ep = list(filter(lambda val: val['Type'] == 'EventPeriodConstraint', undesired))
  preferred_ep= list(filter(lambda val: val['Type'] == 'EventPeriodConstraint', preferred))

  def fill_constraints(c, constraint_type, value):
    key = f"{c['Course']}:{c['Exam']}"
    if c.get('Part') != None: 
      key = f"{key}:{c['Part']}"
      if constraints[constraint_type].get(key, None) == None:
        constraints[constraint_type][key] = []
      constraints[constraint_type][key].append(c[value])
    else:
      if constraints[constraint_type].get(f"{key}:Written", None) == None:
        constraints[constraint_type][f"{key}:Written"] = []
      if constraints[constraint_type].get(f"{key}:Oral", None) == None:
        constraints[constraint_type][f"{key}:Oral"] = []
      constraints[constraint_type][f"{key}:Written"].append(c[value])
      constraints[constraint_type][f"{key}:Oral"].append(c[value])

  for c in undesired_er:
    fill_constraints(c, 'UndesiredEventRoomConstraint', 'Room')
  for c in preferred_er:
    fill_constraints(c, 'PreferredEventRoomConstraint', 'Room')
  for c in undesired_ep:
    fill_constraints(c, 'UndesiredEventPeriodConstraint', 'Period')
  for c in preferred_ep:
    fill_constraints(c, 'PreferredEventPeriodConstraint', 'Period')

  def match_event_to_constraint(event, contraint_type, match_value, equal = True):
    key = f"{event.course}:{event.exam}"
    if event.part != None: key = f"{key}:{event.part}"
    else: key = f"{key}:Written"
    value = constraints[contraint_type].get(key, None)
    return value != None and ((match_value in value and equal) or (match_value not in value and not equal))

  def undesired_er_match(event):
    return match_event_to_constraint(event, 'UndesiredEventRoomConstraint', event.room, True)

  def preferred_er_not_match(event):
    return match_event_to_constraint(event, 'PreferredEventRoomConstraint', event.room, False)

  def undesired_ep_match(event):
    return match_event_to_constraint(event, 'UndesiredEventPeriodConstraint', event.period, True)

  def preferred_ep_not_match(event):
    return match_event_to_constraint(event, 'PreferredEventPeriodConstraint', event.period, False)

  for assignment in assignments:
    for event in assignment.events:
      if undesired_er_match(event):
        cost += UNDESIRED_ROOM_WEIGHT
      if preferred_er_not_match(event):
        cost += INDIFFERENT_ROOM_WEIGHT
      if undesired_ep_match(event):
        cost += UNDESIRED_PERIOD_WEIGHT
      if preferred_ep_not_match(event):
        cost += INDIFFERENT_PERIOD_WEIGHT
      if event.period in undesired_periods:
        cost += UNDESIRED_PERIOD_WEIGHT
  return cost


# WRITTEN_ORAL_DISTANCE_WEIGHT
def written_oral_distance(assignments):
  cost = 0
  two_part_courses = list(filter(lambda val: val.events[0].course_metadata.get('WrittenOralSpecs', None), assignments))

  for assignment in two_part_courses:
    written_oral_specs = assignment.events[0].course_metadata.get('WrittenOralSpecs')
    for eventIndex in range(0, len(assignment.events), 2):
      distance = assignment.events[eventIndex + 1].period - assignment.events[eventIndex].period
      if distance < int(written_oral_specs['MinDistance']):
        cost += abs(written_oral_specs['MinDistance'] - distance) * WRITTEN_ORAL_DISTANCE_WEIGHT
      elif distance > int(written_oral_specs['MaxDistance']):
        cost += abs(distance - written_oral_specs['MaxDistance']) * WRITTEN_ORAL_DISTANCE_WEIGHT

  return cost


# SAME_COURSE_DISTANCE_WEIGHT
def same_course_distance(assignments):
  cost = 0
  repeated_courses = list(filter(lambda val: val.events[0].course_metadata.get('MultipleExams'), assignments))

  for assignment in repeated_courses:
    step = 2 if assignment.events[0].course_metadata.get('WrittenOralSpecs') else 1
    course_minimum_distance_between_exams = assignment.events[0].course_metadata.get('MinimumDistanceBetweenExams')
    for eventIndex in range(0, len(assignment.events) - step, step):
      distance_between_exams = assignment.events[eventIndex + step].period - assignment.events[eventIndex].period
      if int(distance_between_exams) < int(course_minimum_distance_between_exams):
        cost += abs(course_minimum_distance_between_exams - distance_between_exams) * SAME_COURSE_DISTANCE_WEIGHT

  return cost

# PRIMARY_SECONDARY_CONFLICT_WEIGHT
# SECONDARY_SECONDARY_CONFLICT_WEIGHT
def primary_secondary_conflict(solution):
  cost = 0

  visited_conflicts = defaultdict(dict)

  for assignment in solution.assignments:
    for event in assignment.events:
      period = event.period
      course = event.course_metadata
      course_name = course['Course']
      no_room_courses = solution.taken_period_room.get(period, {}).get('noRoom', [])
      period_courses = solution.taken_period_room.get(period, {}).values()

      conflict_courses = []
      conflict_courses.extend(period_courses)
      conflict_courses.extend(no_room_courses)
      conflict_courses = flatten(conflict_courses)

      conflicting_ps = list(set(list(set(conflict_courses) & set(course["PrimarySecondaryCourses"]))))
      conflicting_ss = list(set(list(set(conflict_courses) & set(course["SecondaryCourses"]))))
      primary_secondary_course_conflicts = len(conflicting_ps)
      secondary_course_conflicts = len(conflicting_ss)

      for conflict in conflicting_ps:
        if (visited_conflicts.get(f"{conflict}:{course_name}", False) == True): continue
        visited_conflicts[f"{course_name}:{conflict}"] = True
        cost += PRIMARY_SECONDARY_CONFLICT_WEIGHT

      for conflict in conflicting_ss:
        if (conflict in conflicting_ps or course_name in conflicting_ss): continue
        if (visited_conflicts.get(f"{conflict}:{course_name}", False) == True): continue
        visited_conflicts[f"{course_name}:{conflict}"] = True
        cost += SECONDARY_SECONDARY_CONFLICT_WEIGHT

  return cost

# PRIMARY_PRIMARY_DISTANCE_WEIGHT
# PRIMARY_SECONDARY_DISTANCE_WEIGHT
# SECONDARY_SECONDARY_DISTANCE_WEIGHT
def distance_constraints(solution):
  cost = 0

  visited = defaultdict(dict)
  visited_distances = defaultdict(dict)

  def is_first_exam(event):
    two_part = event.get('TwoPart')
    part = event.get('ExamType')
    return (two_part == True and part == "Written") or (two_part == None)

  for assignment in solution.assignments:
    for event in assignment.events:
      period = event.period
      course = event.course_metadata
      two_part_og = course.get('TwoPart')
      course_name = course['Course']
      min_pp_distance = course.get('PrimaryPrimaryDistance') or 2 * course['SlotsPerDay']
      primary_courses = course["PrimaryCourses"]
      visited[course_name] = True

      for pp_course in primary_courses:
        if (visited.get(pp_course, False) == True): continue
        course_id = solution.course_assignment_ids[pp_course]
        check_assignment = solution.assignments[course_id]
        for check_event in check_assignment.events:
          event_course = check_event.course_metadata
          is_allowed = is_first_exam(course) and is_first_exam(event_course)
          if is_allowed and abs(check_event.period - event.period) < min_pp_distance:
            visited_distances[f"{pp_course}:{course_name}"] = True
            cost += (PRIMARY_PRIMARY_DISTANCE_WEIGHT * (min_pp_distance - abs(check_event.period - event.period)))

      min_ps_distance = course.get('PrimarySecondaryDistance') or course['SlotsPerDay']
      primary_secondary_courses = course["PrimarySecondaryCourses"]

      for ps_course in (primary_secondary_courses):
        if (visited_distances.get(f"{ps_course}:{course_name}", False) == True): continue
        if (visited.get(ps_course, False) == True): continue
        course_id = solution.course_assignment_ids[ps_course]
        check_assignment = solution.assignments[course_id]
        for check_event in check_assignment.events:
          event_course = check_event.course_metadata
          is_allowed = is_first_exam(course) and is_first_exam(event_course)
          if is_allowed and abs(check_event.period - event.period) < min_ps_distance:
            cost += (PRIMARY_SECONDARY_DISTANCE_WEIGHT * (min_ps_distance - abs(check_event.period - event.period)))

      # min_ss_distance = course['SlotsPerDay']
      # secondary_courses = course["SecondaryCourses"]

      # for secondary_course in secondary_courses:
      #   course_id = solution.course_assignment_ids[secondary_course]
      #   check_assignment = solution.assignments[course_id]
      #   for check_event in check_assignment.events:
      #     if abs(event.period - check_event.period) < min_ss_distance:
      #       cost += SECONDARY_SECONDARY_DISTANCE_WEIGHT * abs(event.period - check_event.period)

  return cost

def evaluate(solution):
  assignments = solution.assignments
  constraints = solution.constraints
  undesired_constraints = list(filter(lambda val: val['Level'] == 'Undesired', constraints))
  preferred_constraints = list(filter(lambda val: val['Level'] == 'Preferred', constraints))

  cost = 0
  cost += room_and_period_costs(assignments, undesired_constraints, preferred_constraints)
  cost += written_oral_distance(assignments)
  cost += same_course_distance(assignments)
  cost += primary_secondary_conflict(solution)
  cost += distance_constraints(solution)

  return cost
