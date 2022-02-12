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
  undesired_periods = list(map(lambda x: x['Period'], undesired))
  preferred_periods = list(map(lambda x: x['Period'], undesired))

  print(undesired_periods)
  for assignment in assignments:
    for event in assignment.events:
      if event.period in undesired_periods:
        cost += UNDESIRED_PERIOD_WEIGHT
      if event.period not in preferred_periods:
        cost += INDIFFERENT_PERIOD_WEIGHT
  return cost

def ur_ir():
  return 0

def wod():
  return 0

def scd():
  return 0

def ppd():
  return 0

def psd():
  return 0

def psc():
  return 0

def ssc():
  return 0

def ssd():
  return 0

def validate(solution):
  assignments = solution.assignments
  constraints = solution.constraints
  undesired_constraints = list(filter(lambda val: val['Level'] == 'Undesired', constraints))
  preferred_constraints = list(filter(lambda val: val['Level'] == 'Preferred', constraints))

  # event_period_constraints = list(filter(lambda val: val['Type'] == 'EventPeriodConstraint', soft_constraints))
  # event_room_constraints = list(filter(lambda val: val['Type'] == 'EventRoomConstraint', soft_constraints))

  cost = 0
  cost += up_ip(assignments, undesired_constraints, preferred_constraints)

  return cost
