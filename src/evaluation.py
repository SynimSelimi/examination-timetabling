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
  undesired_periods = list(map(lambda x: x.get('Period'), undesired))
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

def wod():
  return 0

def scd():
  return 0

def ppd():
  return 0

def psd():
  return 0

# PRIMARY_SECONDARY_CONFLICT_WEIGHT
# SECONDARY_SECONDARY_CONFLICT_WEIGHT
def primary_secondary_conflict(solution):
  cost = 0

  for assignment in solution.assignments:
    for event in assignment.events:
      period = event.period
      course = event.course_metadata
      no_room_courses = solution.taken_period_room.get(period, {}).get('noRoom', [])
      period_course = solution.taken_period_room.get(period, {}).values()

      conflict_courses = []
      conflict_courses.extend(period_course)
      conflict_courses.extend(no_room_courses)
      conflict_courses = flatten(conflict_courses)

      primary_secondary_course_conflicts = len(set(list(set(conflict_courses).intersection(course["PrimarySecondaryCourses"]))))
      secondary_course_conflicts = len(set(list(set(conflict_courses).intersection(course["SecondaryCourses"]))))

      temp_ps_cost = 0
      temp_ss_cost = 0
      if primary_secondary_course_conflicts != 0:
        temp_ps_cost = PRIMARY_SECONDARY_CONFLICT_WEIGHT * primary_secondary_course_conflicts
      if secondary_course_conflicts != 0:
        temp_ss_cost = SECONDARY_SECONDARY_CONFLICT_WEIGHT * secondary_course_conflicts

      cost += max(temp_ps_cost, temp_ss_cost)
  return cost

# PRIMARY_PRIMARY_DISTANCE_WEIGHT
# PRIMARY_SECONDARY_DISTANCE_WEIGHT
# SECONDARY_SECONDARY_DISTANCE_WEIGHT
def distance_constraints(solution):
  cost = 0

  for assignment in solution.assignments:
    for event in assignment.events:
      period = event.period
      course = event.course_metadata
      name = course['Course']
      min_pp_distance = course.get('PrimaryPrimaryDistance') or 2 * course['SlotsPerDay']
      primary_courses = course["PrimaryCourses"]

      for pp_course in primary_courses:
        course_id = solution.course_assignment_ids[pp_course]
        check_assignment = solution.assignments[course_id]
        for check_event in check_assignment.events:
          if abs(event.period - check_event.period) < min_pp_distance:
            cost += PRIMARY_PRIMARY_DISTANCE_WEIGHT * abs(event.period - check_event.period)

      min_ps_distance = course.get('PrimarySecondaryDistance') or course['SlotsPerDay']
      primary_secondary_courses = course["PrimarySecondaryCourses"]

      for ps_course in primary_secondary_courses:
        course_id = solution.course_assignment_ids[ps_course]
        check_assignment = solution.assignments[course_id]
        for check_event in check_assignment.events:
          if abs(event.period - check_event.period) < min_ps_distance:
            cost += PRIMARY_SECONDARY_DISTANCE_WEIGHT * abs(event.period - check_event.period)

      min_ss_distance = course['SlotsPerDay']
      secondary_courses = course["SecondaryCourses"]

      for secondary_course in secondary_courses:
        course_id = solution.course_assignment_ids[secondary_course]
        check_assignment = solution.assignments[course_id]
        for check_event in check_assignment.events:
          if abs(event.period - check_event.period) < min_ss_distance:
            cost += SECONDARY_SECONDARY_DISTANCE_WEIGHT * abs(event.period - check_event.period)

  return cost

def evaluate(solution):
  assignments = solution.assignments
  constraints = solution.constraints
  undesired_constraints = list(filter(lambda val: val['Level'] == 'Undesired', constraints))
  preferred_constraints = list(filter(lambda val: val['Level'] == 'Preferred', constraints))

  cost = 0
  cost += room_and_period_costs(assignments, undesired_constraints, preferred_constraints)
  cost += primary_secondary_conflict(solution)
  cost += distance_constraints(solution)

  return cost
