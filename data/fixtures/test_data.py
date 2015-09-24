import datetime
import copy
import random

import factory.fuzzy

from acj import db
from six.moves import range
from acj.models import UserTypesForSystem, UserTypesForCourse, Criteria
from data.factories import CoursesFactory, UsersFactory, CoursesAndUsersFactory, PostsFactory, PostsForQuestionsFactory, \
    PostsForAnswersFactory, CriteriaFactory, CriteriaAndCoursesFactory, AnswerPairingsFactory, JudgementsFactory, \
    PostsForJudgementsFactory, PostsForCommentsFactory, GroupsFactory, GroupsAndUsersFactory, \
    CriteriaAndPostsForQuestionsFactory, PostsForQuestionsAndPostsForCommentsFactory, \
    PostsForAnswersAndPostsForCommentsFactory, ScoreFactory, AnswerCommentFactory
from data.fixtures import DefaultFixture


class BasicTestData:
    def __init__(self):
        self.default_criteria = Criteria.query.first()
        self.main_course = self.create_course()
        self.secondary_course = self.create_course()
        self.main_course_default_criteria = self.add_criteria_course(self.default_criteria, self.main_course)
        self.secondary_course_default_criteria = self.add_criteria_course(self.default_criteria, self.secondary_course)
        self.authorized_instructor = self.create_instructor()
        self.authorized_ta = self.create_normal_user()
        self.authorized_student = self.create_normal_user()
        self.unauthorized_instructor = self.create_instructor()  # unauthorized to the main course
        self.unauthorized_student = self.create_normal_user()
        self.dropped_instructor = self.create_instructor()  # dropped from the main course
        self.enrol_instructor(self.authorized_instructor, self.main_course)
        self.enrol_ta(self.authorized_ta, self.main_course)
        self.enrol_student(self.authorized_student, self.main_course)
        self.enrol_instructor(self.unauthorized_instructor, self.secondary_course)
        self.enrol_student(self.unauthorized_student, self.secondary_course)
        self.unenrol(self.dropped_instructor, self.main_course)

    def create_course(self):
        course = CoursesFactory()
        db.session.commit()
        return course

    def add_criteria_course(self, criteria, course):
        course_criteria = CriteriaAndCoursesFactory(criteria_id=criteria.id, courses_id=course.id)
        db.session.commit()
        return course_criteria

    def create_instructor(self):
        return self.create_user(UserTypesForSystem.TYPE_INSTRUCTOR)

    def create_normal_user(self):
        return self.create_user(UserTypesForSystem.TYPE_NORMAL)

    def create_user(self, type):
        sys_type = UserTypesForSystem.query.filter_by(name=type).first()
        student_no = None
        if type == UserTypesForSystem.TYPE_NORMAL:
            student_no = factory.fuzzy.FuzzyText(length=4)
        user = UsersFactory(usertypesforsystem_id=sys_type.id, student_no=student_no)
        db.session.commit()
        return user

    def enrol_student(self, user, course):
        self.enrol_user(user, course, UserTypesForCourse.TYPE_STUDENT)

    def enrol_instructor(self, user, course):
        self.enrol_user(user, course, UserTypesForCourse.TYPE_INSTRUCTOR)

    def enrol_ta(self, user, course):
        self.enrol_user(user, course, UserTypesForCourse.TYPE_TA)

    def unenrol(self, user, course):
        self.enrol_user(user, course, UserTypesForCourse.TYPE_DROPPED)

    def enrol_user(self, user, course, type):
        course_type = UserTypesForCourse.query.filter_by(name=type).first()
        coursesandusers = CoursesAndUsersFactory(courses_id=course.id, users_id=user.id,
                                                 usertypesforcourse_id=course_type.id)
        db.session.commit()
        return coursesandusers

    def get_authorized_instructor(self):
        return self.authorized_instructor

    def get_authorized_ta(self):
        return self.authorized_ta

    def get_authorized_student(self):
        return self.authorized_student

    def get_course(self):
        return self.main_course

    def get_secondary_course(self):
        return self.secondary_course

    def get_unauthorized_instructor(self):
        return self.unauthorized_instructor

    def get_unauthorized_student(self):
        return self.unauthorized_student

    def get_dropped_instructor(self):
        return self.dropped_instructor

    def get_default_criteria(self):
        return self.default_criteria


class SimpleQuestionsTestData(BasicTestData):
    def __init__(self):
        BasicTestData.__init__(self)
        self.questions = []
        self.criteria_by_questions = {}
        self.questions.append(self.create_question_in_answer_period(self.get_course(), \
                                                                    self.get_authorized_instructor()))
        self.questions.append(self.create_question_in_answer_period(self.get_course(), \
                                                                    self.get_authorized_instructor()))

    def create_question_in_judgement_period(self, course, author):
        answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
        answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
        return self.create_question(course, author, answer_start, answer_end)

    def create_question_in_answer_period(self, course, author):
        answer_start = datetime.datetime.now() - datetime.timedelta(days=1)
        answer_end = datetime.datetime.now() + datetime.timedelta(days=1)
        return self.create_question(course, author, answer_start, answer_end)

    def create_question(self, course, author, answer_start, answer_end):
        post = PostsFactory(courses_id=course.id, users_id=author.id)
        question = PostsForQuestionsFactory(post=post, answer_start=answer_start, answer_end=answer_end)
        CriteriaAndPostsForQuestionsFactory(criterion=DefaultFixture.DEFAULT_CRITERIA, question=question)
        db.session.commit()
        self.criteria_by_questions[question.id] = question.criteria[0]
        return question

    def get_questions(self):
        return self.questions


class QuestionCommentsTestData(SimpleQuestionsTestData):
    def __init__(self):
        SimpleQuestionsTestData.__init__(self)
        self.student_ques_comment = self.create_question_comment(
            self.get_authorized_student(), self.get_course(), self.get_questions()[0])
        self.instructor_ques_comment = self.create_question_comment(
            self.get_authorized_instructor(), self.get_course(), self.get_questions()[1])

    def get_instructor_ques_comment(self):
        return self.instructor_ques_comment

    def get_student_ques_comment(self):
        return self.student_ques_comment

    def create_question_comment(self, user, course, question):
        post = PostsFactory(user=user, course=course)
        comment = PostsForCommentsFactory(post=post)
        PostsForQuestionsAndPostsForCommentsFactory(
            postsforquestions=question, postsforcomments=comment)
        db.session.commit()
        return comment


class SimpleAnswersTestData(SimpleQuestionsTestData):
    def __init__(self, num_answer=2):
        SimpleQuestionsTestData.__init__(self)
        self.extra_student = []
        for _ in range(num_answer):
            student = self.create_normal_user()
            self.extra_student.append(student)
            self.enrol_student(student, self.get_course())
        self.answers = []
        self.answersByQuestion = {}
        for question in self.get_questions():
            answers_for_question = []
            for i in range(num_answer):
                answer = self.create_answer(question, self.extra_student[i])
                answers_for_question.append(answer)
                self.answersByQuestion[question.id] = answers_for_question
            self.answers += answers_for_question

    def create_answer(self, question, author):
        post = PostsFactory(courses_id=question.post.courses_id, users_id=author.id)
        answer = PostsForAnswersFactory(questions_id=question.id, post=post)
        ScoreFactory(answer=answer, criteriaandquestions_id=question.criteria[0].id)
        db.session.commit()
        return answer

    def get_answers(self):
        return self.answers

    def get_answers_by_question(self):
        return self.answersByQuestion

    def get_extra_student(self, index):
        return self.extra_student[index]


class AnswerCommentsTestData(SimpleAnswersTestData):
    def __init__(self):
        SimpleAnswersTestData.__init__(self)
        self.answer_comments_by_question = {}
        for question in self.get_questions():
            comment_extra_student1 = self.create_answer_comment(self.get_extra_student(0),
                                                                self.get_course(),
                                                                self.answersByQuestion[question.id][1])
            comment_extra_student2 = self.create_answer_comment(self.get_extra_student(1),
                                                                self.get_course(),
                                                                self.answersByQuestion[question.id][0])
            self.answer_comments_by_question[question.id] = [comment_extra_student1, comment_extra_student2]

    @staticmethod
    def create_answer_comment(user, course, answer, **kwargs):
        answer_comment_factory = AnswerCommentFactory(user=user, course=course, answer=answer, **kwargs)
        db.session.commit()
        return answer_comment_factory.answer_comment

    def get_answer_comments_by_question(self, question):
        return self.answer_comments_by_question[question.id]


class CriteriaTestData(SimpleAnswersTestData):
    def __init__(self):
        SimpleAnswersTestData.__init__(self)
        # inactive course criteria
        self.criteria = CriteriaFactory(user=self.get_authorized_instructor())
        # criteria created by another instructor
        self.secondary_criteria = CriteriaFactory(user=self.get_unauthorized_instructor())
        # second criteria
        self.criteria2 = CriteriaFactory(user=self.get_authorized_instructor())
        db.session.commit()
        self.inactive_criteria_course = self.add_inactive_criteria_course(self.criteria, self.get_course())

    def add_inactive_criteria_course(self, criteria, course):
        criteria_course = CriteriaAndCoursesFactory(courses_id=course.id, criteria_id=criteria.id, active=False)
        db.session.commit()
        return criteria_course

    def get_criteria(self):
        return self.criteria

    def get_criteria2(self):
        return self.criteria2

    def get_secondary_criteria(self):
        return self.secondary_criteria

    def get_inactive_criteria_course(self):
        return self.inactive_criteria_course

    def get_criteria_by_question(self, question):
        return self.criteria_by_questions[question.id]


class JudgmentsTestData(CriteriaTestData):
    def __init__(self):
        CriteriaTestData.__init__(self)
        self.secondary_authorized_student = self.create_normal_user()
        self.enrol_student(self.secondary_authorized_student, self.get_course())
        self.authorized_student_with_no_answers = self.create_normal_user()
        self.enrol_student(self.authorized_student_with_no_answers, self.get_course())
        self.student_answers = copy.copy(self.answers)
        for question in self.get_questions():
            # make sure we're allowed to judge existing questions
            self.set_question_to_judgement_period(question)
            answer = self.create_answer(question, self.secondary_authorized_student)
            self.answers.append(answer)
            self.student_answers.append(answer)
            self.answers.append(answer)
            answer = self.create_answer(question, self.get_authorized_student())
            self.answers.append(answer)
            self.student_answers.append(answer)
            # add a TA and Instructor answer
            answer = self.create_answer(question, self.get_authorized_ta())
            self.answers.append(answer)
            answer = self.create_answer(question, self.get_authorized_instructor())
            self.answers.append(answer)
        self.answer_period_question = self.create_question_in_answer_period(
            self.get_course(), self.get_authorized_ta())
        self.questions.append(self.answer_period_question)

    def get_student_answers(self):
        return self.student_answers

    def get_question_in_answer_period(self):
        return self.answer_period_question

    def get_secondary_authorized_student(self):
        return self.secondary_authorized_student

    def get_authorized_student_with_no_answers(self):
        '''
        This user is required to make sure that the same answers don't show up in a pair. MUST keep
        make sure that this user does not submit any answers.
        '''
        return self.authorized_student_with_no_answers

    def set_question_to_judgement_period(self, question):
        question.answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
        question.answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
        db.session.add(question)
        db.session.commit()
        return question


class JudgementCommentsTestData(JudgmentsTestData):
    def __init__(self):
        JudgmentsTestData.__init__(self)
        # create & enrol extra student to do the judging
        self.judging_student = self.create_normal_user()
        self.enrol_student(self.judging_student, self.get_course())

        # generate pairs
        self.answer_pair1 = self.create_answer_pair(self.get_questions()[0])
        self.answer_pair2 = self.create_answer_pair(self.get_questions()[1])

        self.judge_1 = self.create_judgement(self.judging_student, self.answer_pair1,
                                             self.get_criteria_by_question(self.get_questions()[0]),
                                             self.get_answers_by_question()[self.get_questions()[0].id][0])
        self.judge_2 = self.create_judgement(self.judging_student, self.answer_pair2,
                                             self.get_criteria_by_question(self.get_questions()[1]),
                                             self.get_answers_by_question()[self.get_questions()[1].id][0])

        self.judge_comment = self.create_judge_comment(self.judge_1)

        self.feedback = {}
        self.feedback[self.judge_1.answerpairing.answers_id1] = \
            self.create_judge_feedback(self.judge_1.answerpairing.answers_id1)
        self.feedback[self.judge_1.answerpairing.answers_id2] = \
            self.create_judge_feedback(self.judge_1.answerpairing.answers_id2)

    def get_judge_feedback(self):
        return self.feedback

    def get_judge_comment(self):
        return self.judge_comment

    def get_judge_2(self):
        return self.judge_2

    def get_judging_student(self):
        return self.judging_student

    def create_answer_pair(self, question):
        # creates an answer pair with the first two answers for the question
        answers = self.get_answers_by_question()[question.id]
        answer_pair = AnswerPairingsFactory(questions_id=question.id, answers_id1=answers[0].id,
                                            answers_id2=answers[1].id)
        db.session.commit()
        return answer_pair

    def create_judgement(self, user, answerpairing, question_criterion, answer):
        judgement = JudgementsFactory(user=user, answerpairing=answerpairing,
                                      question_criterion=question_criterion, answer_winner=answer)
        db.session.commit()
        return judgement

    def create_judge_comment(self, judgement):
        comment_content = factory.fuzzy.FuzzyText(length=12)
        comment = self.create_comment(self.judging_student, self.get_course(), comment_content)
        judge_comment = PostsForJudgementsFactory(postsforcomments=comment, judgement=judgement)
        db.session.commit()
        return judge_comment

    def create_judge_feedback(self, answer):
        feedback_content = factory.fuzzy.FuzzyText(length=12)
        comment = self.create_comment(self.judging_student, self.get_course(), feedback_content)
        feedback = PostsForAnswersAndPostsForCommentsFactory(postsforcomments=comment,
                                                             answers_id=answer, evaluation=True)
        db.session.commit()
        return feedback

    def create_comment(self, user, course, content):
        post = PostsFactory(user=user, course=course, content=content)
        db.session.commit()
        postforcomment = PostsForCommentsFactory(post=post)
        db.session.commit()
        return postforcomment


class GroupsTestData(BasicTestData):
    def __init__(self):
        BasicTestData.__init__(self)
        self.active_group = self.create_group(self.get_course())
        self.inactive_group = self.create_group(self.get_course(), False)
        self.unauthorized_group = self.create_group(self.get_secondary_course())
        self.active_member = self.enrol_group(self.active_group, self.get_authorized_student())
        self.inactive_member = self.enrol_group(self.active_group, self.get_authorized_ta(), False)

    def get_active_group(self):
        return self.active_group

    def get_inactive_group(self):
        return self.inactive_group

    def get_unauthorized_group(self):
        return self.unauthorized_group

    def get_active_member(self):
        return self.active_member

    def get_inactive_member(self):
        return self.inactive_member

    def create_group(self, course, active=True):
        group = GroupsFactory(course=course, active=active)
        db.session.commit()
        return group

    def enrol_group(self, group, user, active=True):
        member = GroupsAndUsersFactory(group=group, user=user, active=active)
        db.session.commit()
        return member


class TestFixture:
    def __init__(self):
        self.course = self.question = None
        self.instructor = self.ta = None
        self.students = []
        self.questions = []
        self.answers = []
        self.groups = []
        self.unauthorized_instructor = UsersFactory(usertypeforsystem=DefaultFixture.SYS_ROLE_INSTRUCTOR)
        self.unauthorized_student = UsersFactory(usertypeforsystem=DefaultFixture.SYS_ROLE_NORMAL)

    def add_course(self, num_students=5, num_questions=1, num_groups=0, num_answers='#'):
        self.course = CoursesFactory()
        self.instructor = UsersFactory(usertypeforsystem=DefaultFixture.SYS_ROLE_INSTRUCTOR)
        self.course.enroll(self.instructor, UserTypesForCourse.TYPE_INSTRUCTOR)
        self.ta = UsersFactory(usertypeforsystem=DefaultFixture.SYS_ROLE_NORMAL)
        self.course.enroll(self.ta, UserTypesForCourse.TYPE_TA)

        self.add_students(num_students)

        self.add_questions(num_questions)
        # create a shortcut for first question as it is frequently used
        self.question = self.questions[0]

        self.add_groups(num_groups)

        self.add_answers(num_answers)

        return self

    def add_answers(self, num_answers):
        if num_answers == '#':
            num_answers = len(self.students) * len(self.questions)
        if len(self.students) * len(self.questions) < num_answers:
            raise ValueError(
                "Number of answers({}) must be equal or smaller than number of students({}) "
                "multiple by number of questions({})".format(num_answers, len(self.students), len(self.questions))
            )
        for i in range(num_answers):
            for question in self.questions:
                post = PostsFactory(course=self.course, user=self.students[i % len(self.students)])
                answer = PostsForAnswersFactory(question=question, post=post)
                # half of the answers have scores
                if i < num_answers/2:
                    ScoreFactory(answer=answer, criteriaandquestions_id=question.criteria[0].id, score=random.random() * 5)
                self.answers.append(answer)

        return self

    def add_groups(self, num_groups):
        student_per_group = int(len(self.students) / num_groups) if num_groups is not 0 else 0
        for idx in range(num_groups):
            group = GroupsFactory(course=self.course)
            self.groups.append(group)
            db.session.commit()
            # slice student list and enroll them into groups
            group.enroll(self.students[idx * student_per_group:min((idx + 1) * student_per_group, len(self.students))])

        return self

    def add_questions(self, num_questions=1, is_answer_period_end=False):
        for _ in range(num_questions):
            post = PostsFactory(course=self.course)
            answer_end = datetime.datetime.now() - datetime.timedelta(
                days=2) if is_answer_period_end else datetime.datetime.now() + datetime.timedelta(days=7)
            question = PostsForQuestionsFactory(post=post, answer_end=answer_end)
            CriteriaAndPostsForQuestionsFactory(criterion=DefaultFixture.DEFAULT_CRITERIA, question=question)
            self.questions.append(question)
        db.session.commit()

        return self

    def add_students(self, num_students):
        students = []
        for _ in range(num_students):
            student = UsersFactory(usertypeforsystem=DefaultFixture.SYS_ROLE_NORMAL)
            students.append(student)
        self.students += students
        self.course.enroll(students)

        return self
