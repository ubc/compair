"""
    Fixture package, also contain default seed data to be populated
"""
from datetime import datetime, timedelta
import random

from acj.models import UserTypesForCourse, UserTypesForSystem, SelfEvaluationTypes, Criteria
from data.fixtures.factories import UsersFactory, UserTypesForCourseFactory, UserTypesForSystemFactory, CriteriaFactory, \
    CoursesFactory, CoursesAndUsersFactory, PostsFactory, PostsForQuestionsFactory, PostsForAnswersFactory, \
    CriteriaAndCoursesFactory, AnswerPairingsFactory, JudgementsFactory, PostsForJudgementsFactory, \
    PostsForCommentsFactory, GroupsFactory, GroupsAndUsersFactory, CriteriaAndPostsForQuestionsFactory, \
    SelfEvaluationTypesFactory, PostsForQuestionsAndPostsForCommentsFactory, \
    PostsForAnswersAndPostsForCommentsFactory


class DefaultFixture(object):
    COURSE_ROLE_DROP = None
    COURSE_ROLE_INSTRUCTOR = None
    COURSE_ROLE_TA = None
    COURSE_ROLE_STUDENT = None

    SYS_ROLE_NORMAL = None
    SYS_ROLE_INSTRUCTOR = None
    SYS_ROLE_ADMIN = None
    ROOT_USER = None

    DEFAULT_CRITERIA = None
    TYPE_COMPARE_NO = None

    def __init__(self):
        DefaultFixture.COURSE_ROLE_DROP = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_DROPPED)
        DefaultFixture.COURSE_ROLE_INSTRUCTOR = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_INSTRUCTOR)
        DefaultFixture.COURSE_ROLE_TA = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_TA)
        DefaultFixture.COURSE_ROLE_STUDENT = UserTypesForCourseFactory(name=UserTypesForCourse.TYPE_STUDENT)

        DefaultFixture.SYS_ROLE_NORMAL = UserTypesForSystemFactory(name=UserTypesForSystem.TYPE_NORMAL)
        DefaultFixture.SYS_ROLE_INSTRUCTOR = UserTypesForSystemFactory(name=UserTypesForSystem.TYPE_INSTRUCTOR)
        DefaultFixture.SYS_ROLE_ADMIN = UserTypesForSystemFactory(name=UserTypesForSystem.TYPE_SYSADMIN)
        DefaultFixture.ROOT_USER = UsersFactory(
            username='root', password='password', displayname='root',
            usertypeforsystem=DefaultFixture.SYS_ROLE_ADMIN)

        name = "Which is better?"
        description = "<p>Choose the response that you think is the better of the two.</p>"
        public = True
        DefaultFixture.DEFAULT_CRITERIA = CriteriaFactory(name=name, description=description, public=public,
                                                          user=DefaultFixture.ROOT_USER)

        DefaultFixture.TYPE_COMPARE_NO = SelfEvaluationTypesFactory(name=SelfEvaluationTypes.TYPE_COMPARE_NO)


class SampleDataFixture(object):
    COURSE_NAMES = ["CDEF102", "BCDE101", "ABCD100", "DEFG103", "EFGH104"]
    INSTRUCTOR_NAMES = ["instructor1"]
    class_size = range(8)
    STUDENT_NAMES = ["student" + str(n) for n in class_size]

    def __init__(self):
        # initialize with default values in cases of DefaultFixture being unavailable
        DEFAULT_CRITERIA = DefaultFixture.DEFAULT_CRITERIA if DefaultFixture.DEFAULT_CRITERIA else \
            Criteria.query.filter_by(name="Which is better?").first()

        SYS_ROLE_INSTRUCTOR = DefaultFixture.SYS_ROLE_INSTRUCTOR if DefaultFixture.SYS_ROLE_INSTRUCTOR else \
            UserTypesForSystem.query.filter_by(name=UserTypesForSystem.TYPE_INSTRUCTOR).first()
        SYS_ROLE_NORMAL = DefaultFixture.SYS_ROLE_NORMAL if DefaultFixture.SYS_ROLE_NORMAL else \
            UserTypesForSystem.query.filter_by(name=UserTypesForSystem.TYPE_NORMAL).first()

        COURSE_ROLE_INSTRUCTOR = DefaultFixture.COURSE_ROLE_INSTRUCTOR if DefaultFixture.COURSE_ROLE_INSTRUCTOR else \
            UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_INSTRUCTOR).first()
        COURSE_ROLE_STUDENT = DefaultFixture.COURSE_ROLE_STUDENT if DefaultFixture.COURSE_ROLE_STUDENT else \
            UserTypesForCourse.query.filter_by(name=UserTypesForCourse.TYPE_STUDENT).first()

        # create courses
        self.courses = []
        for course_name in self.COURSE_NAMES:
            course = CoursesFactory(name=course_name, description=course_name + " Course Description")
            self.courses.append(course)
        # insert default criteria into each course
        for course in self.courses:
            CriteriaAndCoursesFactory(criterion=DEFAULT_CRITERIA, course=course)
        # create instructors
        for instructor_name in self.INSTRUCTOR_NAMES:
            self.instructor = UsersFactory(username=instructor_name,
                                           usertypeforsystem=SYS_ROLE_INSTRUCTOR)
        # create students
        self.students = []
        for student_name in self.STUDENT_NAMES:
            student = UsersFactory(username=student_name,
                                   usertypeforsystem=SYS_ROLE_NORMAL)
            self.students.append(student)
        # enrol students and instructor in half of the courses, also create questions and answers
        skip = True
        generator = TechnobabbleGenerator()
        content = "This is some place holder content for this question. Yay!"
        for course in self.courses:
            skip = not skip
            if skip:
                continue
            # enrol instructor
            CoursesAndUsersFactory(user=self.instructor, course=course,
                                   usertypeforcourse=COURSE_ROLE_INSTRUCTOR)
            # enrol students
            for student in self.students:
                CoursesAndUsersFactory(user=student, course=course,
                                       usertypeforcourse=COURSE_ROLE_STUDENT)
            # create 5 questions by the instructor
            for i in range(5):
                minutes = random.randint(0, 59)
                created = datetime.utcnow() - timedelta(days=1, minutes=minutes)
                post = PostsFactory(course=course, user=self.instructor,
                                    content=content, created=created)
                postforquestion = PostsForQuestionsFactory(post=post, title=generator.get_question())
                # insert default criteria into question
                CriteriaAndPostsForQuestionsFactory(criterion=DEFAULT_CRITERIA, question=postforquestion)
                # create answers by each student for this question
                for student in self.students:
                    minutes = random.randint(0, 59)
                    created = datetime.utcnow() - timedelta(minutes=minutes)
                    post = PostsFactory(course=course, user=student, content=generator.get_answer(),
                                        created=created)
                    PostsForAnswersFactory(post=post, question=postforquestion)


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

    # Questions take the form of:
    # adverb, auxiliary verb, subject, main verb, adjective, object
    def get_question(self):
        sentence = random.choice(self.ADVERBS) + " " + random.choice(self.AUXVERBS) + " " + \
                   random.choice(self.SUBJECTS) + " " + random.choice(self.MAINVERBS) + " the " + \
                   random.choice(self.ADJECTIVES) + " " + random.choice(self.OBJECTS) + "?"
        return sentence

    # Answers take the form of: mainverb, adjective, object
    def get_answer(self):
        sentence = "You need to " + random.choice(self.MAINVERBS) + " the " + \
                   random.choice(self.ADJECTIVES) + " " + random.choice(self.OBJECTS) + "."
        return sentence
