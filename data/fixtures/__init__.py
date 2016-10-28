"""
    Fixture package, also contain default seed data to be populated
"""
from datetime import datetime, timedelta
import random

from compair.models import SystemRole, CourseRole, Criterion
from data.factories import UserFactory, CriterionFactory, \
    CourseFactory, UserCourseFactory, AssignmentFactory, AnswerFactory, \
    AssignmentCriterionFactory


class DefaultFixture(object):
    ROOT_USER = None
    DEFAULT_CRITERION = None

    def __init__(self):
        DefaultFixture.ROOT_USER = UserFactory(
            username='root',
            password='password',
            displayname='root',
            system_role=SystemRole.sys_admin
        )

        DefaultFixture.DEFAULT_CRITERION = CriterionFactory(
            name="Which is better?",
            description="<p>Choose the response that you think is the better of the two.</p>",
            public=True,
            user=DefaultFixture.ROOT_USER
        )


class SampleDataFixture(object):
    COURSE_NAMES = ["CDEF102", "BCDE101", "ABCD100", "DEFG103", "EFGH104"]
    INSTRUCTOR_NAMES = ["instructor1"]
    class_size = range(8)
    STUDENT_NAMES = ["student" + str(n) for n in class_size]

    def __init__(self):
        # initialize with default values in cases of DefaultFixture being unavailable
        DEFAULT_CRITERION = DefaultFixture.DEFAULT_CRITERION if DefaultFixture.DEFAULT_CRITERION else \
            Criterion.query.filter_by(name="Which is better?").first()

        # create courses
        self.courses = []
        for course_name in self.COURSE_NAMES:
            course = CourseFactory(name=course_name, description=course_name + " Course Description")
            self.courses.append(course)
        # create instructors
        for instructor_name in self.INSTRUCTOR_NAMES:
            self.instructor = UserFactory(username=instructor_name,
                                           system_role=SystemRole.instructor)
        # create students
        self.students = []
        for student_name in self.STUDENT_NAMES:
            student = UserFactory(username=student_name,
                                   system_role=SystemRole.student)
            self.students.append(student)
        # enrol students and instructor in half of the courses, also create assignments and answers
        skip = True
        generator = TechnobabbleGenerator()
        content = "This is some place holder content for this assignment. Yay!"
        for course in self.courses:
            skip = not skip
            if skip:
                continue
            # enrol instructor
            UserCourseFactory(user=self.instructor, course=course,
                              course_role=CourseRole.instructor)
            # enrol students
            for student in self.students:
                UserCourseFactory(user=student, course=course,
                                  course_role=CourseRole.student)

            # create 5 assignments by the instructor
            for i in range(5):
                minutes = random.randint(0, 59)
                created = datetime.utcnow() - timedelta(days=1, minutes=minutes)
                assignment = AssignmentFactory(course=course,
                    user=self.instructor, content=content, created=created,
                    name=generator.get_assignment())
                # insert default criterion into assignment
                AssignmentCriterionFactory(criterion=DEFAULT_CRITERION, assignment=assignment)
                # create answers by each student for this assignment
                for student in self.students:
                    minutes = random.randint(0, 59)
                    created = datetime.utcnow() - timedelta(minutes=minutes)
                    AnswerFactory(course=course,
                        user=student, content=generator.get_answer(),
                        created=created, assignment=assignment)


class TechnobabbleGenerator:
    ADVERBS = ['How', 'When', 'Where', 'To what extent', 'For what',
               'By which means', 'How much', 'How frequent']
    AUXVERBS = ['do', 'can', 'must', 'could', 'might', 'should', 'will', 'would',
                'may', 'did']
    SUBJECTS = ['you', 'I', 'we', 'they']
    MAINVERBS = ['remodulate', 'recalibrate', 'polarize', 'reverse', 'reconciliate',
                 'divert power to', 'reconfigure', 'reticulate', 'nullify', 'counteract',
                 'restart']
    ADJECTIVES = ['ion', 'neutrino', 'space-time', 'antimatter', 'tachyon',
                  'heisenberg', 'hadronic', 'positronic', 'gluonic', 'positronic',
                  'chronometric', 'temporal', 'multiversal', 'electromagnetic', 'quantum',
                  'photonic', 'oscillating', 'baryonic', 'plasmic', 'zero-point',
                  'navigational', 'inertial', 'electroplasmic']
    OBJECTS = ['splines', 'shield emitter', 'gravity generator', 'compensator',
               'warp harmonic', 'databanks network', 'particle fountain', 'pulse coupling',
               'phase discriminator', 'phenomenon', 'power module', 'sensory array',
               'distortion', 'collectors', 'dampeners', 'conduit', 'event horizon',
               'singularity']

    # assignments take the form of:
    # adverb, auxiliary verb, subject, main verb, adjective, object
    def get_assignment(self):
        sentence = random.choice(self.ADVERBS) + " " + random.choice(self.AUXVERBS) + " " + \
                   random.choice(self.SUBJECTS) + " " + random.choice(self.MAINVERBS) + " the " + \
                   random.choice(self.ADJECTIVES) + " " + random.choice(self.OBJECTS) + "?"
        return sentence

    # Answers take the form of: mainverb, adjective, object
    def get_answer(self):
        sentence = "You need to " + random.choice(self.MAINVERBS) + " the " + \
                   random.choice(self.ADJECTIVES) + " " + random.choice(self.OBJECTS) + "."
        return sentence
