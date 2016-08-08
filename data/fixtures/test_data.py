import datetime
import copy
import random

import factory.fuzzy

from acj import db
from six.moves import range
from acj.models import SystemRole, CourseRole, Criterion, Course, Comparison
from data.factories import CourseFactory, UserFactory, UserCourseFactory, AssignmentFactory, \
    AnswerFactory, CriterionFactory, ComparisonFactory, AssignmentCriterionFactory, \
    AssignmentCommentFactory, AnswerCommentFactory, ScoreFactory, ComparisonExampleFactory, \
    LTIConsumerFactory, LTIContextFactory, LTIResourceLinkFactory, \
    LTIUserFactory, LTIUserResourceLinkFactory
from data.fixtures import DefaultFixture

class BasicTestData:
    def __init__(self):
        self.default_criterion = Criterion.query.get(1)
        self.main_course = self.create_course()
        self.secondary_course = self.create_course()
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
        db.session.commit()

    def create_course(self):
        course = CourseFactory()
        db.session.commit()
        return course

    def create_criterion(self, user):
        citeria = CriterionFactory(user=user)
        db.session.commit()
        return citeria

    def create_instructor(self):
        return self.create_user(SystemRole.instructor)

    def create_normal_user(self):
        return self.create_user(SystemRole.student)

    def create_user(self, type):
        student_number = None
        if type == SystemRole.student:
            student_number = factory.fuzzy.FuzzyText(length=4)
        user = UserFactory(system_role=type, student_number=student_number)
        db.session.commit()
        return user

    def enrol_student(self, user, course):
        self.enrol_user(user, course, CourseRole.student)

    def enrol_instructor(self, user, course):
        self.enrol_user(user, course, CourseRole.instructor)

    def enrol_ta(self, user, course):
        self.enrol_user(user, course, CourseRole.teaching_assistant)

    def unenrol(self, user, course):
        self.enrol_user(user, course, CourseRole.dropped)

    def enrol_user(self, user, course, type):
        user_courses = UserCourseFactory(course=course, user=user,
                                            course_role=type)
        db.session.commit()
        return user_courses

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

    def get_default_criterion(self):
        return self.default_criterion

class LTITestData:
    def __init__(self):
        self.lti_consumer = LTIConsumerFactory()

        self.lti_consumers = [self.lti_consumer]
        self.lti_contexts = []
        self.lti_resource_links = []
        self.lti_users = []
        self.lti_user_resource_links = []

        db.session.commit()

    def get_consumer(self):
        return self.lti_consumer

    def get_context(self):
        return self.lti_context

    def get_resource_link(self):
        return self.lti_resource_link

    def generate_resource_link_id(self):
        lti_resource_link = LTIResourceLinkFactory.stub()

        return lti_resource_link.resource_link_id

    def generate_context_id(self):
        lti_context = LTIContextFactory.stub()

        return lti_context.context_id

    def generate_user_id(self):
        lti_user= LTIUserFactory.stub()

        return lti_user.user_id

    def create_resource_link(self, lti_consumer, lti_context=None, resource_link_id=None, acj_assignment=None):
        lti_resource_link = LTIResourceLinkFactory(
            lti_consumer=lti_consumer,
            acj_assignment=acj_assignment
        )
        if lti_context:
            lti_resource_link.lti_context = lti_context
        if resource_link_id:
            lti_resource_link.resource_link_id = resource_link_id

        self.lti_resource_links.append(lti_resource_link)

        db.session.commit()

        return lti_resource_link

    def create_context(self, lti_consumer, **kwargs):
        lti_context = LTIContextFactory(
            lti_consumer=lti_consumer,
            **kwargs
        )

        self.lti_contexts.append(lti_context)

        db.session.commit()

        return lti_context

    def create_user(self, lti_consumer, system_role=SystemRole.instructor, acj_user=None):
        lti_user = LTIUserFactory(
            lti_consumer=lti_consumer,
            system_role=system_role,
            acj_user=acj_user
        )
        self.lti_users.append(lti_user)

        db.session.commit()

        return lti_user

    def create_user_resource_link(self, lti_user, lti_resource_link, course_role=CourseRole.instructor):
        lti_user_resource_link = LTIUserResourceLinkFactory(
            lti_user=lti_user,
            lti_resource_link=lti_resource_link,
            course_role=course_role
        )
        self.lti_user_resource_links.append(lti_user_resource_link)

        db.session.commit()

        return lti_user_resource_link

class SimpleAssignmentTestData(BasicTestData):
    def __init__(self):
        BasicTestData.__init__(self)
        self.assignments = []
        self.criteria_by_assignments = {}
        self.assignments.append(self.create_assignment_in_answer_period(self.get_course(), \
                                                                    self.get_authorized_instructor()))
        self.assignments.append(self.create_assignment_in_answer_period(self.get_course(), \
                                                                    self.get_authorized_instructor()))
        db.session.commit()

    def create_assignment_in_comparison_period(self, course, author):
        answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
        answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
        return self.create_assignment(course, author, answer_start, answer_end)

    def create_assignment_in_answer_period(self, course, author):
        answer_start = datetime.datetime.now() - datetime.timedelta(days=1)
        answer_end = datetime.datetime.now() + datetime.timedelta(days=1)
        return self.create_assignment(course, author, answer_start, answer_end)

    def create_assignment(self, course, author, answer_start, answer_end):
        assignment = AssignmentFactory(
            course=course,
            user=author,
            answer_start=answer_start,
            answer_end=answer_end
        )
        disabled_criterion = CriterionFactory(user=author, default=False, active=False)
        AssignmentCriterionFactory(criterion=DefaultFixture.DEFAULT_CRITERION, assignment=assignment)
        AssignmentCriterionFactory(criterion=disabled_criterion, assignment=assignment, active=False)
        db.session.commit()
        self.criteria_by_assignments[assignment.id] = assignment.criteria[0]
        return assignment

    def get_assignments(self):
        return self.assignments


class AssignmentCommentsTestData(SimpleAssignmentTestData):
    def __init__(self):
        SimpleAssignmentTestData.__init__(self)
        self.student_ques_comment = self.create_assignment_comment(
            self.get_authorized_student(), self.get_course(), self.get_assignments()[0])
        self.instructor_ques_comment = self.create_assignment_comment(
            self.get_authorized_instructor(), self.get_course(), self.get_assignments()[1])

    def get_instructor_assignment_comment(self):
        return self.instructor_ques_comment

    def get_student_assignment_comment(self):
        return self.student_ques_comment

    def create_assignment_comment(self, user, course, assignment):
        assignment_comment = AssignmentCommentFactory(
            assignment=assignment,
            user=user
        )
        db.session.commit()
        return assignment_comment


class SimpleAnswersTestData(SimpleAssignmentTestData):
    def __init__(self, num_answer=2, num_draft_answers=1):
        SimpleAssignmentTestData.__init__(self)
        self.extra_student = []
        for _ in range(num_answer + num_draft_answers):
            student = self.create_normal_user()
            self.extra_student.append(student)
            self.enrol_student(student, self.get_course())
        self.answers = []
        self.draft_answers = []
        self.answersByassignment = {}
        for assignment in self.get_assignments():
            answers_for_assignment = []
            for i in range(num_answer):
                answer = self.create_answer(assignment, self.extra_student[i])
                answers_for_assignment.append(answer)
                self.answersByassignment[assignment.id] = answers_for_assignment
            self.answers += answers_for_assignment

            # add some draft answers to all assignments. generally these shouldn't be returned by the API
            # except for the answers API in some cases. hence they are stored outside of self.answers
            # and answersByassignment
            draft_answers_for_assignment = []
            for i in range(num_draft_answers):
                answer = self.create_answer(assignment, self.extra_student[num_answer+i], draft=True)
                draft_answers_for_assignment.append(answer)
            self.draft_answers += draft_answers_for_assignment
        db.session.commit()

    def create_answer(self, assignment, author, draft=False):
        answer = AnswerFactory(
            assignment=assignment,
            user=author,
            draft=draft
        )
        ScoreFactory(
            assignment=assignment,
            answer=answer,
            criterion=assignment.criteria[0]
        )
        db.session.commit()
        return answer

    def get_answers(self):
        return self.answers

    def get_answers_by_assignment(self):
        return self.answersByassignment

    def get_extra_student(self, index):
        return self.extra_student[index]


class AnswerCommentsTestData(SimpleAnswersTestData):
    def __init__(self):
        SimpleAnswersTestData.__init__(self)
        self.answer_comments_by_assignment = {}
        for assignment in self.get_assignments():
            comment_extra_student1 = self.create_answer_comment(self.get_extra_student(0),
                                                                self.answersByassignment[assignment.id][1])
            comment_extra_student2 = self.create_answer_comment(self.get_extra_student(1),
                                                                self.answersByassignment[assignment.id][0])
            draft_comment_extra_student2 = self.create_answer_comment(self.get_extra_student(1),
                                                                self.answersByassignment[assignment.id][0],
                                                                draft=True)
            self.answer_comments_by_assignment[assignment.id] = [
                comment_extra_student1, comment_extra_student2, draft_comment_extra_student2
            ]

    @staticmethod
    def create_answer_comment(user, answer, **kwargs):
        answer_comment = AnswerCommentFactory(
            user=user, answer=answer, **kwargs
        )
        db.session.commit()
        return answer_comment

    def get_non_draft_answer_comments_by_assignment(self, assignment):
        return [comment for comment in self.answer_comments_by_assignment[assignment.id] if not comment.draft]

    def get_answer_comments_by_assignment(self, assignment):
        return self.answer_comments_by_assignment[assignment.id]


class CriterionTestData(SimpleAnswersTestData):
    def __init__(self):
        SimpleAnswersTestData.__init__(self)
        self.criterion = CriterionFactory(user=self.get_authorized_instructor())
        # criterion created by another instructor
        self.secondary_criterion = CriterionFactory(user=self.get_unauthorized_instructor())
        # second criterion
        self.criterion2 = CriterionFactory(user=self.get_authorized_instructor())
        db.session.commit()

    def get_criterion(self):
        return self.criterion

    def get_criterion2(self):
        return self.criterion2

    def get_secondary_criterion(self):
        return self.secondary_criterion

    def get_inactive_criterion_course(self):
        return self.inactive_criterion_course

    def get_criteria_by_assignment(self, assignment):
        return self.criteria_by_assignments[assignment.id]


class ComparisonTestData(CriterionTestData):
    def __init__(self):
        CriterionTestData.__init__(self)
        self.secondary_authorized_student = self.create_normal_user()
        self.enrol_student(self.secondary_authorized_student, self.get_course())
        self.authorized_student_with_no_answers = self.create_normal_user()
        self.enrol_student(self.authorized_student_with_no_answers, self.get_course())
        self.student_answers = copy.copy(self.answers)
        self.comparisons_examples = []
        for assignment in self.get_assignments():
            # make sure we're allowed to compare existing assignments
            self.set_assignment_to_comparison_period(assignment)
            answer = self.create_answer(assignment, self.secondary_authorized_student)
            self.answers.append(answer)
            self.student_answers.append(answer)
            self.answers.append(answer)
            answer = self.create_answer(assignment, self.get_authorized_student())
            self.answers.append(answer)
            self.student_answers.append(answer)
            # add a TA and Instructor answer
            answer = self.create_answer(assignment, self.get_authorized_ta())
            self.answers.append(answer)
            answer = self.create_answer(assignment, self.get_authorized_instructor())
            self.answers.append(answer)
            # add a comparison example
            answer1 = self.create_answer(assignment, self.get_authorized_ta())
            self.answers.append(answer)
            answer2 = self.create_answer(assignment, self.get_authorized_instructor())
            self.answers.append(answer)
            comparison_example = self.create_comparison_example(assignment, answer1, answer2)
            self.comparisons_examples.append(comparison_example)
        self.answer_period_assignment = self.create_assignment_in_answer_period(
            self.get_course(), self.get_authorized_ta())
        self.assignments.append(self.answer_period_assignment)
        db.session.commit()

    def create_comparison_example(self, assignment, answer1, answer2):
        answer1.practice = True
        answer2.practice = True
        comparison_example = ComparisonExampleFactory(
            assignment=assignment,
            answer1=answer1,
            answer2=answer2
        )
        db.session.commit()
        return comparison_example

    def get_student_answers(self):
        return self.student_answers

    def get_assignment_in_answer_period(self):
        return self.answer_period_assignment

    def get_secondary_authorized_student(self):
        return self.secondary_authorized_student

    def get_authorized_student_with_no_answers(self):
        '''
        This user is required to make sure that the same answers don't show up in a pair. MUST keep
        make sure that this user does not submit any answers.
        '''
        return self.authorized_student_with_no_answers

    def set_assignment_to_comparison_period(self, assignment):
        assignment.answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
        assignment.answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
        db.session.add(assignment)
        db.session.commit()
        return assignment

class TestFixture:
    def __init__(self):
        self.default_criterion = Criterion.query.get(1)
        self.course = self.assignment = None
        self.instructor = self.ta = None
        self.students = []
        self.assignments = []
        self.comparison_examples = []
        self.answers = []
        self.draft_answers = []
        self.groups = []
        self.unauthorized_instructor = UserFactory(system_role=SystemRole.instructor)
        self.unauthorized_student = UserFactory(system_role=SystemRole.student)
        self.dropped_instructor = UserFactory(system_role=SystemRole.instructor)
        self.draft_student = None
        db.session.commit()

    def add_course(self, num_students=5, num_assignments=1, num_groups=0, num_answers='#', with_draft_student=False, with_comparisons=False):
        self.course = CourseFactory()
        self.instructor = UserFactory(system_role=SystemRole.instructor)
        self.enrol_user(self.instructor, self.course, CourseRole.instructor)
        self.ta = UserFactory(system_role=SystemRole.student)
        self.dropped_instructor = UserFactory(system_role=SystemRole.instructor)
        self.enrol_user(self.dropped_instructor, self.course, CourseRole.dropped)
        self.enrol_user(self.ta, self.course, CourseRole.teaching_assistant)

        self.add_students(num_students, num_groups)

        self.add_assignments(num_assignments)
        # create a shortcut for first assignment as it is frequently used
        self.assignment = self.assignments[0]

        self.add_answers(num_answers)

        if with_comparisons:
            self.add_comparisons()

        if with_draft_student:
            self.add_students(1)
            self.draft_student = self.students[-1]
            self.add_draft_answers([self.draft_student])

        return self

    def add_answers(self, num_answers):
        if num_answers == '#':
            num_answers = len(self.students) * len(self.assignments)
        if len(self.students) * len(self.assignments) < num_answers:
            raise ValueError(
                "Number of answers({}) must be equal or smaller than number of students({}) "
                "multiple by number of assignments({})".format(num_answers, len(self.students), len(self.assignments))
            )
        for i in range(num_answers):
            for assignment in self.assignments:
                answer = AnswerFactory(
                    assignment=assignment,
                    user=self.students[i % len(self.students)]
                )
                # half of the answers have scores
                if i < num_answers/2:
                    ScoreFactory(
                        assignment=assignment,
                        answer=answer,
                        criterion=assignment.criteria[0],
                        score=random.random() * 5
                    )
                db.session.commit()
                self.answers.append(answer)

        return self

    def add_comparisons(self):
        for assignment in self.assignments:
            for student in self.students:
                for i in range(assignment.total_comparisons_required):
                    comparisons = Comparison.create_new_comparison_set(assignment.id, student.id)
                    for comparison in comparisons:
                        comparison.completed = True
                        comparison.winner_id = min([comparisons[0].answer1_id, comparisons[0].answer2_id])
                        db.session.add(comparison)
                    db.session.commit()

        return self

    def add_answer(self, assignment, user):
        answer = AnswerFactory(
            assignment=assignment,
            user=user
        )
        db.session.commit()
        self.answers.append(answer)
        return self

    def add_draft_answers(self, students):
        for student in students:
            for assignment in self.assignments:
                answer = AnswerFactory(
                    assignment=assignment,
                    user=student,
                    draft=True
                )
                db.session.commit()
                self.draft_answers.append(answer)

        return self

    def add_assignments(self, num_assignments=1, is_answer_period_end=False):
        for _ in range(num_assignments):
            answer_end = datetime.datetime.now() - datetime.timedelta(
                days=2) if is_answer_period_end else datetime.datetime.now() + datetime.timedelta(days=7)
            assignment = AssignmentFactory(course=self.course, answer_end=answer_end)
            AssignmentCriterionFactory(criterion=DefaultFixture.DEFAULT_CRITERION, assignment=assignment)
            disabled_criterion = CriterionFactory(user=self.instructor, default=False, active=False)
            AssignmentCriterionFactory(criterion=disabled_criterion, assignment=assignment, active=False)
            self.assignments.append(assignment)
        db.session.commit()

        return self

    def add_comparison_example(self, assignment, user):
        self.add_answer(assignment, user)
        self.add_answer(assignment, user)

        comparison_example = ComparisonExampleFactory(
            assignment=assignment,
            answer1=self.answers[-2],
            answer2=self.answers[-1]
        )
        self.comparison_examples.append(comparison_example)
        db.session.commit()
        return self

    def add_students(self, num_students, num_groups=0):
        students = []
        for _ in range(num_students):
            student = UserFactory(system_role=SystemRole.student)
            students.append(student)
        self.students += students

        if num_groups > 0:
            student_per_group = int(len(self.students) / num_groups) if num_groups is not 0 else 0
            for idx in range(num_groups):
                group_name = "Group" + str(idx)
                self.groups.append(group_name)
                # slice student list and enroll them into groups
                group_students = self.students[idx * student_per_group:min((idx + 1) * student_per_group, len(self.students))]
                for student in group_students:
                    self.enrol_user(student, self.course, CourseRole.student, group_name)
        else:
            for student in students:
                self.enrol_user(student, self.course, CourseRole.student)

        return self

    def enrol_user(self, user, course, type, group_name=None):
        user_courses = UserCourseFactory(course=course, user=user,
                                            course_role=type, group_name=group_name)
        db.session.commit()
        return user_courses