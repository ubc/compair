"""
    Recalculate Grades
"""

from flask_script import Manager
from acj.models import Course, Assignment

manager = Manager(usage="Generate Grades")

@manager.command
def generate(course_id=None, all=False):
    courses = []
    if course_id != None:
        course = Course.query.get(course_id)
        if course:
            courses = [course]
        else:
            print("No course found with that ID")
            return
    elif all:
        courses = Course.query.all()
    else:
        print("Please enter a course_id or use the all flag")
        return

    for course in courses:
        print("Generating grades for course: " + course.name)
        for assignment in course.assignments:
            print("--- Generating grades for assignment: " + assignment.name)
            assignment.calculate_grades()
        course.calculate_grades()
        print("")
    print("Done.")