import json

class Solution:
    def __init__(self, instances):
        self.instances = instances
        self.cost = 0
        self.assignments = []
        self.course_assignment_ids = {}
        self.last_assignment_id = 0

    def solve(self):
        # To Do add possible RoomPeriodConstraint to the busy roomPeriodSets
        # To Do Take into account same day constraints
        # To do add EventRoomConstraint to a temporary memory set
        # To Do check MinimumDistanceBetweenExams
        # To Do check MaxDistance MinDistance for WrittenOral (soft)
        # To Do check PrimaryPrimaryDistance (soft)
        # To Do check if courses have the same teacher (cannot be assigned same period)
        # To Do check if courses are primary (cannot be assigned same period)
        # To Do calculate cost
        self.cost = 0
        self.assignments = []

        # dict(sorted(x.items(), key=lambda item: item[1]))
        courses = self.instances.copy()

        while len(courses) > 0:
            course = courses.pop(0)
            course_name = course['Course']

            exam_type = course['ExamType']
            exam_order = course['ExamOrder']
            period = course.get('PossiblePeriods')
            period = period[0] if len(period) > 0 else None
            room = course.get('PossibleRooms')
            room = room[0] if len(room) > 0 else None
            event = Event(exam_order, exam_type, period, room, course_name)
            self.add_event(course_name, event)

        return self.export()

    def add_event(self, course_name, event):
        if course_name not in self.course_assignment_ids.keys():
            assignment = Assignment(course_name)
            self.course_assignment_ids[course_name] = self.last_assignment_id
            self.assignments.append(assignment)
            self.last_assignment_id += 1
        else:
            assignment_id = self.course_assignment_ids[course_name]
            assignment = self.assignments[assignment_id]
            
        assignment.add_event(event)

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
    def __init__(self, exam, part, period, room, course):
        self.exam = exam
        self.part = part
        self.period = period
        self.room = room
        self.course = course

    def export(self):
        return {
            'Exam': self.exam,
            'Part': self.part,
            'Period': self.period,
            'Room': self.room,
            'Course': self.course
        }