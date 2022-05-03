import datetime
import copy
import random

import factory.fuzzy

from compair import db
from six.moves import range
from compair.models import SystemRole, CourseRole, Course, \
    Comparison, ThirdPartyType, AnswerCommentType, WinningAnswer, \
    UserCourse
from data.factories import CourseFactory, UserFactory, UserCourseFactory, AssignmentFactory, \
    AnswerFactory, CriterionFactory, ComparisonFactory, ComparisonCriterionFactory, \
    AnswerCommentFactory, AnswerScoreFactory, AnswerCriterionScoreFactory, \
    ComparisonExampleFactory, AssignmentCriterionFactory, FileFactory, \
    LTIConsumerFactory, LTIContextFactory, LTIResourceLinkFactory, \
    LTIUserFactory, LTIUserResourceLinkFactory, ThirdPartyUserFactory, \
    GroupFactory
from data.fixtures import DefaultFixture

class BasicTestData:
    def __init__(self):
        self.users = [DefaultFixture.ROOT_USER]
        self.default_criterion = DefaultFixture.DEFAULT_CRITERION
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

    def create_file(self, user):
        db_file = FileFactory(user=user)
        db.session.commit()
        return db_file

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
        self.users.append(user)
        return user

    def enrol_student(self, user, course, group=None):
        self.enrol_user(user, course, CourseRole.student, group)

    def enrol_instructor(self, user, course, group=None):
        self.enrol_user(user, course, CourseRole.instructor, group)

    def enrol_ta(self, user, course, group=None):
        self.enrol_user(user, course, CourseRole.teaching_assistant, group)

    def unenrol(self, user, course, group=None):
        self.enrol_user(user, course, CourseRole.dropped, group)

    def enrol_user(self, user, course, course_role, group=None):
        user_courses = UserCourseFactory(
            course=course,
            user=user,
            group=group,
            course_role=course_role
        )
        db.session.commit()
        return user_courses

    def create_group(self, course, **kwargs):
        group = GroupFactory(
            course=course,
            **kwargs
        )
        db.session.commit()
        return group

    def change_group(self, course, user, group):
        user_course = UserCourse.query \
            .filter_by(
                course_id=course.id,
                user_id=user.id
            ) \
            .one()
        user_course.group = group
        db.session.commit()

        return user_course

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

    def setup_student_user_resource_links(self, student, course, assignment=None):
        self.lti_consumer.lis_outcome_service_url = "TestUrl.com"
        lti_context = self.create_context(
            self.lti_consumer,
            compair_course_id=course.id
        )
        lti_user_student = self.create_user(self.lti_consumer, SystemRole.student, student)

        lti_resource_link1 = self.create_resource_link(self.lti_consumer, lti_context=lti_context)
        lti_user_resource_link1 = self.create_user_resource_link(lti_user_student, lti_resource_link1, CourseRole.student)
        lti_user_resource_link1.lis_result_sourcedid = "SomeUniqueSourcedId" + str(len(self.lti_user_resource_links))

        if assignment:
            lti_resource_link2 = self.create_resource_link(self.lti_consumer, lti_context=lti_context, compair_assignment=assignment)
            lti_user_resource_link2 = self.create_user_resource_link(lti_user_student, lti_resource_link2, CourseRole.student)
            lti_user_resource_link2.lis_result_sourcedid = "SomeUniqueSourcedId" + str(len(self.lti_user_resource_links))

        db.session.commit()

        if assignment:
            return (lti_user_resource_link1, lti_user_resource_link2)
        else:
            return lti_user_resource_link1

    def get_consumer(self):
        return self.lti_consumer

    def generate_resource_link_id(self):
        lti_resource_link = LTIResourceLinkFactory.stub()

        return lti_resource_link.resource_link_id

    def generate_context_id(self):
        lti_context = LTIContextFactory.stub()

        return lti_context.context_id

    def generate_user_id(self):
        lti_user = LTIUserFactory.stub()

        return lti_user.user_id

    def create_consumer(self, **kwargs):
        lti_consumer = LTIConsumerFactory(**kwargs)

        self.lti_consumers.append(lti_consumer)

        db.session.commit()

        return lti_consumer

    def create_resource_link(self, lti_consumer, lti_context=None, resource_link_id=None, compair_assignment=None):
        lti_resource_link = LTIResourceLinkFactory(
            lti_consumer=lti_consumer,
            compair_assignment=compair_assignment
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

    def create_user(self, lti_consumer, system_role=SystemRole.instructor, compair_user=None):
        lti_user = LTIUserFactory(
            lti_consumer=lti_consumer,
            system_role=system_role,
            compair_user=compair_user
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

class ThirdPartyAuthTestData:
    def __init__(self):
        self.third_party_users = []

    def create_cas_user_auth(self, type):
        student_number = None
        if type == SystemRole.student:
            student_number = factory.fuzzy.FuzzyText(length=4)
        user = UserFactory(
            system_role=type,
            student_number=student_number,
            username=None,
            password=None
        )
        third_party_user = self.create_third_party_user(
            user=user, third_party_type=ThirdPartyType.cas)
        db.session.commit()
        return third_party_user

    def create_saml_user_auth(self, type):
        student_number = None
        if type == SystemRole.student:
            student_number = factory.fuzzy.FuzzyText(length=4)
        user = UserFactory(
            system_role=type,
            student_number=student_number,
            username=None,
            password=None
        )
        third_party_user = self.create_third_party_user(
            user=user, third_party_type=ThirdPartyType.saml)
        db.session.commit()
        return third_party_user

    def create_third_party_user(self, **kwargs):
        third_party_user = ThirdPartyUserFactory(
            **kwargs
        )

        self.third_party_users.append(third_party_user)

        db.session.commit()

        return third_party_user

class SimpleAssignmentTestData(BasicTestData):
    def __init__(self):
        BasicTestData.__init__(self)
        self.assignments = []
        self.criteria_by_assignments = {}
        self.assignments.append(self.create_assignment_in_answer_period(
            self.get_course(), self.get_authorized_instructor()
        ))
        self.assignments.append(self.create_assignment_in_comparison_period(
            self.get_course(), self.get_authorized_instructor()
        ))
        self.assignments.append(self.create_assignment_in_answer_period(
            self.get_course(), self.get_authorized_instructor(), enable_group_answers=True
        ))
        self.assignments.append(self.create_assignment_in_comparison_period(
            self.get_course(), self.get_authorized_instructor(), enable_group_answers=True
        ))

        db.session.commit()

    def create_assignment_in_comparison_period(self, course, author, **kwargs):
        answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
        answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
        return self.create_assignment(course, author, answer_start, answer_end, **kwargs)

    def create_assignment_in_answer_period(self, course, author, **kwargs):
        answer_start = datetime.datetime.now() - datetime.timedelta(days=1)
        answer_end = datetime.datetime.now() + datetime.timedelta(days=1)
        return self.create_assignment(course, author, answer_start, answer_end, **kwargs)

    def create_assignment(self, course, author, answer_start, answer_end, **kwargs):
        assignment = AssignmentFactory(
            course=course,
            user=author,
            answer_start=answer_start,
            answer_end=answer_end,
            **kwargs
        )
        disabled_criterion = CriterionFactory(user=author, default=False, active=False)
        AssignmentCriterionFactory(criterion=DefaultFixture.DEFAULT_CRITERION, assignment=assignment)
        AssignmentCriterionFactory(criterion=disabled_criterion, assignment=assignment, active=False)
        db.session.commit()
        self.criteria_by_assignments[assignment.id] = assignment.criteria[0]
        return assignment

    def get_assignments(self):
        return self.assignments

class SimpleAnswersTestData(SimpleAssignmentTestData):
    def __init__(self, num_answer=2, num_draft_answers=1):
        SimpleAssignmentTestData.__init__(self)
        self.extra_student = []
        self.groups = []
        for _ in range(num_answer + num_draft_answers):
            student = self.create_normal_user()
            self.extra_student.append(student)
            group = self.create_group(self.get_course())
            self.groups.append(group)
            self.enrol_student(student, self.get_course(), group)
        self.answers = []
        self.draft_answers = []
        self.answers_by_assignment = {}
        for assignment in self.get_assignments():
            answers_for_assignment = []
            for i in range(num_answer):
                if assignment.enable_group_answers:
                    answer = self.create_group_answer(assignment, self.groups[i])
                else:
                    answer = self.create_answer(assignment, self.extra_student[i])
                answers_for_assignment.append(answer)
                self.answers_by_assignment[assignment.id] = answers_for_assignment
            self.answers += answers_for_assignment

            # add some draft answers to all assignments. generally these shouldn't be returned by the API
            # except for the answers API in some cases. hence they are stored outside of self.answers
            # and answers_by_assignment
            draft_answers_for_assignment = []
            for i in range(num_draft_answers):
                if assignment.enable_group_answers:
                    answer = self.create_group_answer(assignment, self.groups[num_answer+i], draft=True)
                else:
                    answer = self.create_answer(assignment, self.extra_student[num_answer+i], draft=True)
                draft_answers_for_assignment.append(answer)
            self.draft_answers += draft_answers_for_assignment
        db.session.commit()

        for assignment in self.get_assignments():
            assignment.calculate_grades()
        self.get_course().calculate_grades()

    def create_answer(self, assignment, user, draft=False, with_score=True):
        answer = AnswerFactory(
            assignment=assignment,
            user=user,
            group=None,
            draft=draft
        )
        if with_score:
            AnswerScoreFactory(
                assignment=assignment,
                answer=answer
            )
            for criterion in assignment.criteria:
                AnswerCriterionScoreFactory(
                    assignment=assignment,
                    answer=answer,
                    criterion=criterion
                )
        db.session.commit()
        return answer

    def get_groups(self):
        return self.groups

    def create_group_answer(self, assignment, group, draft=False, with_score=True):
        answer = AnswerFactory(
            assignment=assignment,
            group=group,
            user=None,
            draft=draft
        )
        if with_score:
            AnswerScoreFactory(
                assignment=assignment,
                answer=answer
            )
            for criterion in assignment.criteria:
                AnswerCriterionScoreFactory(
                    assignment=assignment,
                    answer=answer,
                    criterion=criterion
                )
        db.session.commit()
        return answer

    def create_answer_comment(self, answer, author, comment_type, draft=False):
        answer_comment = AnswerCommentFactory(
            answer=answer,
            user=author,
            comment_type=comment_type,
            draft=draft
        )
        db.session.commit()
        return answer_comment

    def get_answers(self):
        return self.answers

    def get_answers_by_assignment(self):
        return self.answers_by_assignment

    def get_extra_student(self, index):
        return self.extra_student[index]


class AnswerCommentsTestData(SimpleAnswersTestData):
    def __init__(self):
        SimpleAnswersTestData.__init__(self)
        self.answer_comments_by_assignment = {}
        for assignment in self.get_assignments():
            comment_extra_student1 = self.create_answer_comment(
                self.get_extra_student(0), self.answers_by_assignment[assignment.id][1])
            comment_extra_student2 = self.create_answer_comment(
                self.get_extra_student(1), self.answers_by_assignment[assignment.id][0])
            draft_comment_extra_student2 = self.create_answer_comment(
                self.get_extra_student(1), self.answers_by_assignment[assignment.id][0], draft=True)
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

        self.authorized_student_group = self.create_group(self.main_course)
        self.groups.append(self.authorized_student_group)
        self.change_group(self.main_course, self.authorized_student, self.authorized_student_group)

        self.secondary_authorized_student_group = self.create_group(self.main_course)
        self.groups.append(self.secondary_authorized_student_group)
        self.change_group(self.main_course, self.secondary_authorized_student, self.secondary_authorized_student_group)

        for assignment in self.get_assignments():
            # make sure we're allowed to compare existing assignments
            self.set_assignment_to_comparison_period(assignment)

            if assignment.enable_group_answers:
                answer = self.create_group_answer(assignment, self.secondary_authorized_student_group)
                self.answers.append(answer)
                self.student_answers.append(answer)

                answer = self.create_group_answer(assignment, self.authorized_student_group)
                self.answers.append(answer)
                self.student_answers.append(answer)
            else:
                answer = self.create_answer(assignment, self.secondary_authorized_student)
                self.answers.append(answer)
                self.student_answers.append(answer)

                answer = self.create_answer(assignment, self.get_authorized_student())
                self.answers.append(answer)
                self.student_answers.append(answer)

            # add a TA and Instructor answer - not comparable
            answer = self.create_answer(assignment, self.get_authorized_ta())
            answer.comparable = False
            self.answers.append(answer)
            answer = self.create_answer(assignment, self.get_authorized_instructor())
            answer.comparable = False
            self.answers.append(answer)

            # add a TA and Instructor answer - comparable
            answer = self.create_answer(assignment, self.get_authorized_ta())
            answer.comparable = True
            self.answers.append(answer)
            answer = self.create_answer(assignment, self.get_authorized_instructor())
            answer.comparable = True
            self.answers.append(answer)

            # add a comparison example
            answer1 = self.create_answer(assignment, self.get_authorized_ta())
            answer2 = self.create_answer(assignment, self.get_authorized_instructor())
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

    def get_comparable_answers(self):
        return [answer for answer in self.answers if answer.comparable]

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
        self.root_user = DefaultFixture.ROOT_USER
        self.default_criterion = DefaultFixture.DEFAULT_CRITERION
        self.course = self.assignment = None
        self.instructor = self.ta = None
        self.students = []
        self.dropped_students = []
        self.assignments = []
        self.comparison_examples = []
        self.answers = []
        self.dropped_answers = []
        self.removed_answers = []
        self.draft_answers = []
        self.non_comparable_answers =[]
        self.groups = []
        self.unauthorized_instructor = UserFactory(system_role=SystemRole.instructor)
        self.unauthorized_student = UserFactory(system_role=SystemRole.student)
        self.dropped_instructor = UserFactory(system_role=SystemRole.instructor)
        self.draft_student = None
        self.draft_group = None
        self.answer_comments = []
        self.comparisons = []
        self.self_evaluations = []
        db.session.commit()

    def add_course(self, num_students=5, num_assignments=1, num_group_assignments=0,
            num_additional_criteria=0, num_groups=0, num_answers='#', num_group_answers='#',
            with_comments=False, with_draft_student=False, with_comparisons=False, with_self_eval=False,
            num_non_comparable_ans=1):
        self.course = CourseFactory()
        self.instructor = UserFactory(system_role=SystemRole.instructor)
        self.enrol_user(self.instructor, self.course, CourseRole.instructor)
        self.ta = UserFactory(system_role=SystemRole.student)
        self.dropped_instructor = UserFactory(system_role=SystemRole.instructor)
        self.enrol_user(self.dropped_instructor, self.course, CourseRole.dropped)
        self.enrol_user(self.ta, self.course, CourseRole.teaching_assistant)

        self.add_students(num_students, num_groups)

        if num_assignments:
            self.add_assignments(
                num_assignments,
                num_additional_criteria=num_additional_criteria,
                with_self_eval=with_self_eval
            )

        if num_group_assignments:
            self.add_assignments(
                num_group_assignments,
                num_additional_criteria=num_additional_criteria,
                with_self_eval=with_self_eval,
                with_group_answers=True
            )

        # create a shortcut for first assignment as it is frequently used
        self.assignment = self.assignments[0]

        self.add_answers(num_answers, num_group_answers, with_comments=with_comments)
        self.add_non_comparable_answers(num_non_comparable_ans)

        if with_comparisons:
            self.add_comparisons(with_comments=with_comments, with_self_eval=with_self_eval)

        if with_draft_student:
            self.draft_student = UserFactory(system_role=SystemRole.student)
            db.session.add(self.draft_student)
            db.session.commit()
            self.draft_group = self.add_group(self.course)
            self.students.append(self.draft_student)
            self.enrol_user(self.draft_student, self.course, CourseRole.student, self.draft_group)
            for assignment in self.assignments:
                answer = AnswerFactory(
                    assignment=assignment,
                    draft=True,
                    submission_date=None
                )
                if assignment.enable_group_answers:
                    answer.group = self.draft_group
                    answer.user = None
                else:
                    answer.user = self.draft_student
                    answer.group = None
                self.draft_answers.append(answer)
            db.session.add_all(self.draft_answers)
            db.session.commit()

        for assignment in self.assignments:
            assignment.calculate_grades()
        self.course.calculate_grades()

        return self

    def add_answers(self, num_answers='#', num_group_answers='#', with_scores=True, with_comments=False):
        if num_answers == '#':
            num_answers = len(self.students)
        if num_group_answers == '#':
            num_group_answers = len(self.groups)

        for assignment in self.assignments:
            if not assignment.active:
                continue

            if assignment.enable_group_answers:
                # add a scored removed answer for every group
                # make sure system handles this properly
                for group in self.groups:
                    if not group.active:
                        continue

                    answer = AnswerFactory(
                        assignment=assignment,
                        group=group,
                        user=None,
                        active=False
                    )
                    AnswerScoreFactory(
                        assignment=assignment,
                        answer=answer,
                        score=random.random() * 5
                    )
                    for criterion in assignment.criteria:
                        AnswerCriterionScoreFactory(
                            assignment=assignment,
                            answer=answer,
                            criterion=criterion,
                            score=random.random() * 5
                        )
                    self.removed_answers.append(answer)

                for i in range(num_group_answers):
                    group = self.groups[i % len(self.groups)]
                    answer = AnswerFactory(
                        assignment=assignment,
                        group=group,
                        user=None,
                    )
                    # half of the answers have scores if with_scores is enabled
                    if with_scores and i < num_group_answers/2:
                        AnswerScoreFactory(
                            assignment=assignment,
                            answer=answer,
                            score=random.random() * 5
                        )
                        for criterion in assignment.criteria:
                            AnswerCriterionScoreFactory(
                                assignment=assignment,
                                answer=answer,
                                criterion=criterion,
                                score=random.random() * 5
                            )

                    if with_comments:
                        user_courses = UserCourse.query \
                            .filter_by(course_id=assignment.course_id, group_id=group.id) \
                            .all()
                        group_user_ids = [user_course.user_id for user_course in user_courses]
                        other_group_students = [s for s in self.students if not s.id in group_user_ids]
                        # half of the answers have a public comment
                        if i < num_group_answers/2:
                            random.shuffle(other_group_students)
                            answer_comment = AnswerCommentFactory(
                                user=other_group_students[0],
                                answer=answer,
                                comment_type=AnswerCommentType.public
                            )
                            self.answer_comments.append(answer_comment)

                        # half of the answers have a private comment
                        # (middle half so there is partial overlap with public comments)
                        if num_group_answers/4 < i and i < (num_group_answers * 3)/4:
                            random.shuffle(other_group_students)
                            answer_comment = AnswerCommentFactory(
                                user=other_group_students[0],
                                answer=answer,
                                comment_type=AnswerCommentType.private
                            )
                            self.answer_comments.append(answer_comment)

                    self.answers.append(answer)

                for dropped_student in self.dropped_students:
                    answer = AnswerFactory(
                        assignment=assignment,
                        user=dropped_student,
                        group=None,
                    )
                    self.dropped_answers.append(answer)
            else:
                # add a scored removed answer for every student
                # make sure system handles this properly
                for student in self.students:
                    answer = AnswerFactory(
                        assignment=assignment,
                        user=student,
                        group=None,
                        active=False,
                    )
                    AnswerScoreFactory(
                        assignment=assignment,
                        answer=answer,
                        score=random.random() * 5
                    )
                    for criterion in assignment.criteria:
                        AnswerCriterionScoreFactory(
                            assignment=assignment,
                            answer=answer,
                            criterion=criterion,
                            score=random.random() * 5
                        )
                    self.removed_answers.append(answer)

                for i in range(num_answers):
                    student = self.students[i % len(self.students)]
                    answer = AnswerFactory(
                        assignment=assignment,
                        user=student,
                        group=None
                    )
                    # half of the answers have scores if with_scores is enabled
                    if with_scores and i < num_answers/2:
                        AnswerScoreFactory(
                            assignment=assignment,
                            answer=answer,
                            score=random.random() * 5
                        )
                        for criterion in assignment.criteria:
                            AnswerCriterionScoreFactory(
                                assignment=assignment,
                                answer=answer,
                                criterion=criterion,
                                score=random.random() * 5
                            )

                    if with_comments:
                        other_students = [s for s in self.students if s.id != student.id]
                        # half of the answers has a public comment
                        if i < num_answers/2:
                            random.shuffle(other_students)
                            answer_comment = AnswerCommentFactory(
                                user=other_students[0],
                                answer=answer,
                                comment_type=AnswerCommentType.public
                            )
                            self.answer_comments.append(answer_comment)

                        # half of the answers has a private comment
                        # (middle half so there is partial overlap with public comments)
                        if num_answers/4 < i and i < (num_answers * 3)/4:
                            random.shuffle(other_students)
                            answer_comment = AnswerCommentFactory(
                                user=other_students[0],
                                answer=answer,
                                comment_type=AnswerCommentType.private
                            )
                            self.answer_comments.append(answer_comment)

                    self.answers.append(answer)

                for dropped_student in self.dropped_students:
                    answer = AnswerFactory(
                        assignment=assignment,
                        user=dropped_student,
                        group=None
                    )
                    self.dropped_answers.append(answer)

        db.session.commit()

        return self

    def add_non_comparable_answers(self, num_non_comparable_ans):
        for assignment in self.assignments:
            for i in range(num_non_comparable_ans):
                answer = AnswerFactory(
                    assignment=assignment,
                    user=self.instructor,
                    group=None,
                    comparable=False)
                self.answers.append(answer)
                self.non_comparable_answers.append(answer)
        db.session.commit()

    def add_comparisons(self, with_comments=False, with_self_eval=False):
        for assignment in self.assignments:
            for student in self.students:
                self.add_comparisons_for_user(assignment, student, with_comments=with_comments, with_self_eval=with_self_eval)
        return self

    def add_comparisons_for_user(self, assignment, student, with_comments=False, with_self_eval=False):
        answers = set()
        for i in range(assignment.total_comparisons_required):
            comparison = Comparison.create_new_comparison(assignment.id, student.id, False)
            comparison.completed = True
            comparison.winner = WinningAnswer.answer1 if comparison.answer1_id < comparison.answer2_id else WinningAnswer.answer2
            for comparison_criterion in comparison.comparison_criteria:
                comparison_criterion.winner = comparison.winner
            db.session.add(comparison)
            db.session.commit()
            self.comparisons.append(comparison)

        if with_comments:
            for answer in answers:
                answer_comment = AnswerCommentFactory(
                    user=student,
                    answer=answer,
                    comment_type=AnswerCommentType.evaluation
                )
                self.answer_comments.append(answer_comment)
            db.session.commit()

        if with_self_eval:
            student_answer = next(
                answer for answer in self.answers if answer.user_id == student.id and answer.assignment_id == assignment.id
            )
            if student_answer:
                self_evaluation = AnswerCommentFactory(
                    user=student,
                    answer=student_answer,
                    comment_type=AnswerCommentType.self_evaluation
                )
                self.self_evaluations.append(self_evaluation)
                db.session.commit()

        return self

    def add_answer(self, assignment, user, draft=False):
        answer = AnswerFactory(
            assignment=assignment,
            user=user,
            group=None,
            draft=draft
        )
        if (draft):
            answer.submission_date=None

        db.session.commit()
        self.answers.append(answer)
        return self

    def add_group_answer(self, assignment, group, draft=False):
        answer = AnswerFactory(
            assignment=assignment,
            group=group,
            user=None,
            draft=draft
        )
        if (draft):
            answer.submission_date=None

        db.session.commit()
        self.answers.append(answer)
        return self

    def add_assignments(self, num_assignments=1, num_group_assignments=0, num_additional_criteria=0,
                        is_answer_period_end=False,  with_self_eval=False, with_group_answers=False):
        for _ in range(num_assignments):
            answer_end = datetime.datetime.now() - datetime.timedelta(
                days=2) if is_answer_period_end else datetime.datetime.now() + datetime.timedelta(days=7)
            assignment = AssignmentFactory(course=self.course, answer_end=answer_end)

            if with_self_eval:
                assignment.enable_self_evaluation = True

            if with_group_answers:
                assignment.enable_group_answers = True

            # default criterion
            AssignmentCriterionFactory(criterion=DefaultFixture.DEFAULT_CRITERION, assignment=assignment, position=0)

            # disabled criterion
            disabled_criterion = CriterionFactory(user=self.instructor, default=False, active=False)
            AssignmentCriterionFactory(criterion=disabled_criterion, assignment=assignment, active=False, position=1)

            # additional criterion
            for i in range(num_additional_criteria):
                criterion = CriterionFactory(user=self.instructor, default=False)
                AssignmentCriterionFactory(criterion=criterion, assignment=assignment, position=i+2)

            db.session.commit()

            # need to reorder after update
            assignment.assignment_criteria.reorder()

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
            student_per_group = int(len(self.students) / num_groups) if num_groups != 0 else 0
            for idx in range(num_groups):
                group = self.add_group(self.course)
                # slice student list and enroll them into groups
                group_students = students[idx * student_per_group:min((idx + 1) * student_per_group, len(students))]
                for student in group_students:
                    self.enrol_user(student, self.course, CourseRole.student, group)
        else:
            for student in students:
                self.enrol_user(student, self.course, CourseRole.student)

        # add dropped student in group
        dropped_student = UserFactory(system_role=SystemRole.student)
        dropped_group = self.add_group(self.course)
        self.enrol_user(dropped_student, self.course, CourseRole.dropped, dropped_group)
        self.dropped_students.append(dropped_student)

        return self

    def enrol_user(self, user, course, course_role, group=None):
        user_course = UserCourseFactory(
            course=course, user=user,
            course_role=course_role, group=group)
        db.session.commit()
        return user_course

    def change_user_group(self, course, user, group):
        user_course = UserCourse.query \
            .filter_by(
                course_id=course.id,
                user_id=user.id
            ) \
            .one()
        user_course.group = group
        db.session.commit()

        return user_course

    def add_file(self, user, **kwargs):
        db_file = FileFactory(user=user, **kwargs)
        db.session.commit()
        return db_file

    def add_group(self, course, **kwargs):
        group = GroupFactory(course=course, **kwargs)
        self.groups.append(group)
        db.session.commit()
        return group

    def _get_assignment_group_member_answers(self, assignment, group):
        user_ids = [uc.user_id for uc in group.user_courses if uc.course_role != CourseRole.dropped]
        return [a for a in self.answers if a.user_id in user_ids and a.assignment_id == assignment.id and a.active]

    def _get_assignment_group_answers(self, assignment, group):
        return [a for a in self.answers if a.group_id == group.id and a.assignment_id == assignment.id and a.active]

    def get_assignment_answers_for_group(self, assignment, group):
        return self._get_assignment_group_answers(assignment, group) + \
            self._get_assignment_group_member_answers(assignment, group)

