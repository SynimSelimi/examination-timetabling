class Solution:
    def __init__(self, instances):
        self.instances = instances
        self.assignments = []

    def solve(self):
        return self.instances

    def add_assignment(self, assignment):
        self.assignments.append(assignment)

    def export_data(self):
        return {}

    def import_data(self, data):
        return Solution()

class Assignment:
    def __init__(self, course):
        self.course = course
        self.events = []

class Event:
    def __init__(self, exam, part, period, room):
        self.exam = exam
        self.part = part
        self.period = period
        self.room = room