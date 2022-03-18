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

def up_ip(assignments, undesired, preferred):
  cost = 0
  undesired_periods = list(filter(lambda val: val['Type'] == 'PeriodConstraint', undesired))
  preferred_periods = list(filter(lambda val: val['Type'] == 'PeriodConstraint', preferred))
  undesired_periods = list(map(lambda x: x.get('Period'), undesired))
  preferred_periods = list(map(lambda x: x.get('Period'), undesired))

  for assignment in assignments:
    for event in assignment.events:
      if event.period in undesired_periods:
        cost += UNDESIRED_PERIOD_WEIGHT
      if event.period not in preferred_periods:
        cost += INDIFFERENT_PERIOD_WEIGHT
  return cost

def ur_ir():
  return 0

def wod(assignments):
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

def scd(assignments):
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

def ppd(solution):
  cost = 0
  primary_primary_distance = solution.primary_primary_distance
  for assignment in solution.assignments:
    for event in assignment.events:
      course = event.course_metadata
      primary_courses = course["PrimaryCourses"]

      for primary_course in primary_courses:
        course_id = solution.course_assignment_ids[primary_course]
        check_assignment = solution.assignments[course_id]
        for check_event in check_assignment.events:
          if abs(event.period - check_event.period) < primary_primary_distance:
            cost += PRIMARY_PRIMARY_DISTANCE_WEIGHT
  return cost

def psd():
  return 0

def psc():
  return 0

def ssc():
  return 0

def ssd():
  return 0

def evaluate(solution):
  assignments = solution.assignments
  constraints = solution.constraints
  undesired_constraints = list(filter(lambda val: val['Level'] == 'Undesired', constraints))
  preferred_constraints = list(filter(lambda val: val['Level'] == 'Preferred', constraints))

  # event_period_constraints = list(filter(lambda val: val['Type'] == 'EventPeriodConstraint', soft_constraints))
  # event_room_constraints = list(filter(lambda val: val['Type'] == 'EventRoomConstraint', soft_constraints))

  cost = 0
  cost += up_ip(assignments, undesired_constraints, preferred_constraints)
  cost += wod(assignments)
  cost += scd(assignments)
  cost += ppd(solution)

  return cost
