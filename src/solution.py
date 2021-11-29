import json

class Solution:
    def __init__(self, instances):
        self.instances = instances
        self.cost = 0
        self.assignments = []

    def solve(self):
        # To Do add possible RoomPeriodConstraint to the busy roomPeriodSets
        # To Do Take into account same day constraints
        # To do add EventRoomConstraint to a temporary memory set
        # To Do check MinimumDistanceBetweenExams
        # To Do check MaxDistance MinDistance for WrittenOral (soft)
        # To Do check PrimaryPrimaryDistance
        # To Do check if courses have the same teacher (cannot be assigned same period)
        # To Do check if courses are primary (cannot be assigned same period)
        # To Do calculate cost
        self.cost = 0
        self.assignments = []

        for instance in self.instances:
            # To Do group by course and add events per course
            course = instance['Course']
            assignment = Assignment(course)
            event = Event(0, 'Oral', 26, '306')
            assignment.add_event(event)
            self.add_assignment(assignment)

        return self.export()

    def add_assignment(self, assignment):
        self.assignments.append(assignment)

    def export(self):
        assignments = []
        for assignment in self.assignments:
            assignments.append(assignment.export())

        return {
            'Assignments': assignments,
            'Cost': self.cost
        }

    def import_data(self, data):
        pass

class Assignment:
    def __init__(self, course):
        self.course = course
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def export(self):
        export_events = []
        for event in self.events:
            export_event = event.export()
            export_events.append(export_event)

        return {
            'Course': self.course,
            'Events': export_events
        }

class Event:
    def __init__(self, exam, part, period, room):
        self.exam = exam
        self.part = part
        self.period = period
        self.room = room

    def export(self):
        return {
            'Exam': self.exam,
            'Part': self.part,
            'Period': self.period,
            'Room': self.room
        }