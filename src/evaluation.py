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

# UNDESIRED_PERIOD_WEIGHT = 10
# INDIFFERENT_PERIOD_WEIGHT = 2
def up_ip(assignments, undesired, preferred):
  cost = 0
  undesired_periods = list(filter(lambda val: val['Type'] == 'PeriodConstraint', undesired))
  undesired_periods = list(map(lambda x: x.get('Period'), undesired))

  for assignment in assignments:
    for event in assignment.events:
      if event.period in undesired_periods:
        cost += UNDESIRED_PERIOD_WEIGHT
      else:
        cost += INDIFFERENT_PERIOD_WEIGHT
  return cost

# UNDESIRED_ROOM_WEIGHT = 5
# INDIFFERENT_ROOM_WEIGHT = 1
def ur_ir(assignments, undesired, preferred):
  cost = 0
  undesired_er = list(filter(lambda val: val['Type'] == 'EventRoomConstraint', undesired))
  undesired_ep = list(filter(lambda val: val['Type'] == 'EventPeriodConstraint', preferred))
  preferred_ep= list(filter(lambda val: val['Type'] == 'EventPeriodConstraint', preferred))

  def undesired_er_match(event, undesired_er):
    return event.room == undesired_er['Room'] and \
      event.exam == undesired_er['Exam'] and \
      event.course == undesired_er['Course'] and \
      (undesired_er.get('Part') == None or event.part == undesired_er['Part'])

  def undesired_ep_match(event, undesired_er):
    return event.period == undesired_er['Period'] and \
      event.exam == undesired_er['Exam'] and \
      event.course == undesired_er['Course'] and \
      (undesired_er.get('Part') == None or event.part == undesired_er['Part'])

  def preferred_ep_not_match(event, preferred_ep):
    return event.period != undesired_er['Period'] and \
      event.exam == undesired_er['Exam'] and \
      event.course == undesired_er['Course'] and \
      (undesired_er.get('Part') == None or event.part == undesired_er['Part'])

  for assignment in assignments:
    for event in assignment.events:
      if undesired_er_match(event, undesired_er):
        cost += UNDESIRED_ROOM_WEIGHT
      if undesired_ep_match(event, undesired_ep):
        cost += UNDESIRED_PERIOD_WEIGHT
      if preferred_ep_not_match(event, preferred_ep):
        cost += INDIFFERENT_ROOM_WEIGHT
  return cost

def wod():
  return 0

def scd():
  return 0

def ppd():
  return 0

def psd():
  return 0

# PRIMARY_SECONDARY_CONFLICT_WEIGHT = 5
def psc():
  return 0

# SECONDARY_SECONDARY_CONFLICT_WEIGHT = 1
def ssc():
  return 0

# SECONDARY_SECONDARY_DISTANCE_WEIGHT = 1
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
  cost += ur_ir(assignments, undesired_constraints, preferred_constraints)

  return cost
