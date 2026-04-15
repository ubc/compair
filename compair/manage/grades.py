"""
    Recalculate Grades
"""

import click
from flask.cli import AppGroup
from compair.models import Course, Assignment

grades_cli = AppGroup('grades', help="Generate Grades")

@grades_cli.command('generate')
@click.option('--course-id', default=None)
@click.option('--all', 'all_courses', is_flag=True, default=False)
def generate(course_id, all_courses):
    courses = []
    if course_id != None:
        course = Course.query.get(course_id)
        if course and course.active:
            courses = [course]
        else:
            print("No course found with that ID")
            return
    elif all_courses:
        courses = Course.query.all()
    else:
        print("Please enter a course_id or use the all flag")
        return

    for course in courses:
        if course.active:
            print("Generating grades for course: " + course.name)
            for assignment in course.assignments:
                if assignment.active:
                    print("--- Generating grades for assignment: " + assignment.name)
                    assignment.calculate_grades()
            course.calculate_grades()
            print("")
    print("Done.")