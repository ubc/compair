"""0.9.x database redesign

Revision ID: 36c9fd392e33
Revises: 48e3b9d1750b
Create Date: 2016-06-20 11:39:25.789216

"""

# revision identifiers, used by Alembic.
revision = '36c9fd392e33'
down_revision = '48e3b9d1750b'

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy_enum34 import EnumType
from sqlalchemy import exc
from compair.models import convention
from enum import Enum

class SystemRole(Enum):
    student = "Student"
    instructor = "Instructor"
    sys_admin = "System Administrator"

class CourseRole(Enum):
    dropped = "Dropped"
    instructor = "Instructor"
    teaching_assistant = "Teaching Assistant"
    student = "Student"

class AnswerCommentType(Enum):
    public = "Public"
    private = "Private"
    evaluation = "Evaluation"
    self_evaluation = "Self Evaluation"

def upgrade():
    def translate_system_role(usertypesforsystem_id):
        if usertypesforsystem_id == 1:
            return SystemRole.student
        elif usertypesforsystem_id == 2:
            return SystemRole.instructor
        elif usertypesforsystem_id == 3:
            return SystemRole.sys_admin

    def translate_course_role(usertypesforcourse_id):
        if usertypesforcourse_id == 1:
            return CourseRole.dropped
        elif usertypesforcourse_id == 2:
            return CourseRole.instructor
        elif usertypesforcourse_id == 3:
            return CourseRole.teaching_assistant
        elif usertypesforcourse_id == 4:
            return CourseRole.student

    def translate_answer_comment_type(evaluation, self_eval, comment_type):
        if self_eval:
            return AnswerCommentType.self_evaluation
        elif evaluation:
            return AnswerCommentType.evaluation
        elif comment_type:
            return AnswerCommentType.public
        else:
            return AnswerCommentType.private

    old_user_table = sa.table('Users',
        sa.column('id', sa.Integer), sa.Column('username', sa.String), sa.Column('_password', sa.String),
        sa.Column('usertypesforsystem_id', sa.Integer), sa.Column('email', sa.String),
        sa.Column('firstname', sa.String), sa.Column('lastname', sa.String), sa.Column('displayname', sa.String),
        sa.Column('lastonline', sa.DateTime), sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
        sa.Column('student_no', sa.String)
    )

    old_course_table = sa.table('Courses',
        sa.column('id', sa.Integer), sa.Column('name', sa.String), sa.Column('description', sa.Text),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    old_criterion_table = sa.table('Criteria',
        sa.column('id', sa.Integer), sa.Column('name', sa.String), sa.Column('description', sa.Text),
        sa.Column('users_id', sa.Integer), sa.Column('public', sa.Boolean), sa.Column('default', sa.Boolean),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    old_file_table = sa.table('FilesForPosts',
        sa.column('id', sa.Integer), sa.column('posts_id', sa.Integer), sa.column('author_id', sa.Integer),
        sa.Column('name', sa.String), sa.Column('alias', sa.String)
    )

    old_assignment_table = sa.table('Questions',
        sa.column('id', sa.Integer), sa.column('posts_id', sa.Integer), sa.column('title', sa.String),
        sa.Column('answer_start', sa.DATETIME), sa.Column('answer_end', sa.DATETIME),
        sa.Column('judge_start', sa.DATETIME), sa.Column('judge_end', sa.DATETIME),
        sa.Column('num_judgement_req', sa.Integer), sa.Column('can_reply', sa.Boolean),
        sa.Column('modified', sa.DateTime)
    )

    old_posts_table = sa.table('Posts',
        sa.column('id', sa.Integer), sa.column('users_id', sa.Integer), sa.column('courses_id', sa.String),
        sa.column('content', sa.Text),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    old_assignment_self_eval_table = sa.table('QuestionsAndSelfEvalTypes',
        sa.column('id', sa.Integer), sa.column('questions_id', sa.Integer), sa.column('selfevaltypes_id', sa.Integer)
    )

    old_user_course_table = sa.table('CoursesAndUsers',
        sa.column('id', sa.Integer), sa.column('courses_id', sa.Integer), sa.column('users_id', sa.Integer),
        sa.column('usertypesforcourse_id', sa.Integer),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    old_group_table = sa.table('Groups',
        sa.column('id', sa.Integer), sa.column('courses_id', sa.Integer),
        sa.column('name', sa.String), sa.column('active', sa.Boolean)
    )

    old_user_group_table = sa.table('GroupsAndUsers',
        sa.column('id', sa.Integer), sa.column('groups_id', sa.Integer),
        sa.column('users_id', sa.Integer), sa.column('active', sa.Boolean)
    )

    old_answer_table = sa.table('Answers',
        sa.column('id', sa.Integer), sa.column('posts_id', sa.Integer), sa.column('questions_id', sa.Integer),
        sa.column('flagged', sa.Boolean), sa.column('users_id_flagger', sa.Integer), sa.column('round', sa.Integer)
    )

    old_assignment_comment_table = sa.table('QuestionsAndComments',
        sa.column('id', sa.Integer), sa.column('questions_id', sa.Integer), sa.column('comments_id', sa.Integer)
    )

    old_comment_table = sa.table('Comments',
        sa.column('id', sa.Integer), sa.column('posts_id', sa.Integer)
    )

    old_assignment_criterion_table = sa.table('CriteriaAndQuestions',
        sa.column('id', sa.Integer), sa.column('criteria_id', sa.Integer),
        sa.column('questions_id', sa.Integer), sa.column('active', sa.Boolean)
    )

    old_answer_comment_table = sa.table('AnswersAndComments',
        sa.column('id', sa.Integer), sa.column('answers_id', sa.Integer), sa.column('comments_id', sa.Integer),
        sa.column('evaluation', sa.Boolean), sa.column('selfeval', sa.Boolean), sa.column('type', sa.Boolean),
    )

    old_comparison_table = sa.table('Judgements',
        sa.column('id', sa.Integer), sa.column('users_id', sa.Integer), sa.column('answerpairings_id', sa.Integer),
        sa.column('answers_id_winner', sa.Integer), sa.column('criteriaandquestions_id', sa.Integer),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    old_pair_table = sa.table('AnswerPairings',
        sa.column('id', sa.Integer), sa.column('questions_id', sa.Integer),
        sa.column('answers_id1', sa.Integer), sa.column('answers_id2', sa.Integer),
        sa.column('criteriaandquestions_id', sa.Integer),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    old_comparison_comment_table = sa.table('PostsForJudgements',
        sa.column('id', sa.Integer), sa.column('comments_id', sa.Integer),
        sa.column('judgements_id', sa.Integer), sa.column('selfeval', sa.Boolean)
    )

    old_score_table = sa.table('Scores',
        sa.column('id', sa.Integer), sa.column('answers_id', sa.Integer),
        sa.column('rounds', sa.Integer), sa.column('wins', sa.Integer),
        sa.column('score', sa.Float), sa.column('criteriaandquestions_id', sa.Integer)
    )
    ### commands auto generated by Alembic - please adjust! ###


    # STEP 1: Create new tables
    new_user_table = op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('_password', sa.String(length=255), nullable=False),
        sa.Column('system_role', EnumType(SystemRole), nullable=False),
        sa.Column('displayname', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('firstname', sa.String(length=255), nullable=True),
        sa.Column('lastname', sa.String(length=255), nullable=True),
        sa.Column('student_number', sa.String(length=50), nullable=True),
        sa.Column('last_online', sa.DateTime(), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_number'),
        sa.UniqueConstraint('username'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_user_system_role'), 'user', ['system_role'], unique=False)

    new_course_table = op.create_table(
        'course',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_course_active'), 'course', ['active'], unique=False)

    new_criterion_table = op.create_table(
        'criterion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('public', sa.Boolean(), nullable=False),
        sa.Column('default', sa.Boolean(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_criterion_active'), 'criterion', ['active'], unique=False)
    op.create_index(op.f('ix_criterion_default'), 'criterion', ['default'], unique=False)
    op.create_index(op.f('ix_criterion_public'), 'criterion', ['public'], unique=False)

    new_file_table = op.create_table(
        'file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_file_active'), 'file', ['active'], unique=False)

    new_assignment_table = op.create_table(
        'assignment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('answer_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('answer_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compare_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compare_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('number_of_comparisons', sa.Integer(), nullable=False),
        sa.Column('students_can_reply', sa.Boolean(), nullable=False),
        sa.Column('enable_self_evaluation', sa.Boolean(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['file_id'], ['file.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_assignment_active'), 'assignment', ['active'], unique=False)

    new_user_course_table = op.create_table(
        'user_course',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('course_role', EnumType(CourseRole), nullable=False),
        sa.Column('group_name', sa.String(length=255), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'user_id', name='_unique_user_and_course'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_user_course_course_role'), 'user_course', ['course_role'], unique=False)
    op.create_index(op.f('ix_user_course_group_name'), 'user_course', ['group_name'], unique=False)

    new_answer_table = op.create_table(
        'answer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('round', sa.Integer(), nullable=False),
        sa.Column('flagged', sa.Boolean(), nullable=False),
        sa.Column('flagger_user_id', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['file_id'], ['file.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['flagger_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_answer_active'), 'answer', ['active'], unique=False)

    new_assignment_comment_table = op.create_table(
        'assignment_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_assignment_comment_active'), 'assignment_comment', ['active'], unique=False)

    new_assignment_criterion_table = op.create_table(
        'assignment_criterion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('criterion_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['criterion_id'], ['criterion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'criterion_id', name='_unique_assignment_and_criterion'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_assignment_criterion_active'), 'assignment_criterion', ['active'], unique=False)

    new_answer_comment_table = op.create_table(
        'answer_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('answer_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('comment_type', EnumType(AnswerCommentType), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_answer_comment_active'), 'answer_comment', ['active'], unique=False)
    op.create_index(op.f('ix_answer_comment_comment_type'), 'answer_comment', ['comment_type'], unique=False)

    new_comparison_table = op.create_table(
        'comparison',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('criterion_id', sa.Integer(), nullable=False),
        sa.Column('answer1_id', sa.Integer(), nullable=False),
        sa.Column('answer2_id', sa.Integer(), nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('round_compared', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer1_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['answer2_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['criterion_id'], ['criterion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['winner_id'], ['answer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_comparison_completed'), 'comparison', ['completed'], unique=False)

    new_score_table = op.create_table(
        'score',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('answer_id', sa.Integer(), nullable=False),
        sa.Column('criterion_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('excepted_score', sa.Float(), nullable=False),
        sa.Column('rounds', sa.Integer(), nullable=False),
        sa.Column('wins', sa.Integer(), nullable=False),
        sa.Column('opponents', sa.Integer(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['answer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['criterion_id'], ['criterion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('answer_id', 'criterion_id', name='_unique_answer_and_criterion'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_score_score'), 'score', ['score'], unique=False)

    # STEP 2: Migrate data
    connection = op.get_bind()

    for user in connection.execute(old_user_table.select()):
        modified = user.modified if user.modified else datetime.utcnow()
        created = user.created if user.created else datetime.utcnow()

        connection.execute(
            new_user_table.insert().values(
                id=user.id, username=user.username, _password=user._password,
                system_role=translate_system_role(user.usertypesforsystem_id),
                displayname=user.displayname, email=user.email,
                firstname=user.firstname, lastname=user.lastname,
                student_number=user.student_no, last_online=user.lastonline,
                modified=modified, created=created
            )
        )

    for course in connection.execute(old_course_table.select()):
        connection.execute(
            new_course_table.insert().values(
                id=course.id, name=course.name, description=course.description,
                active=True,
                modified=course.modified, created=course.created
            )
        )

    for criterion in connection.execute(old_criterion_table.select()):
        connection.execute(
            new_criterion_table.insert().values(
                id=criterion.id, user_id=criterion.users_id,
                name=criterion.name, description=criterion.description,
                public=criterion.public, default=criterion.default,
                active=True,
                modified=criterion.modified, created=criterion.created
            )
        )

    for file in connection.execute(old_file_table.select()):
        connection.execute(
            new_file_table.insert().values(
                id=file.id, user_id=file.author_id, name=file.name, alias=file.alias,
                active=True,
                modified=datetime.utcnow(), created=datetime.utcnow()
            )
        )
    for assignment in connection.execute(old_assignment_table.select()):
        user_id = None
        course_id = None
        file_id = None
        description = None
        enable_self_evaluation = False
        created = datetime.utcnow()

        posts = connection.execute(old_posts_table.select().where(old_posts_table.c.id == assignment.posts_id))
        for post in posts:
            user_id = post.users_id
            course_id = post.courses_id
            description = post.content
            created = post.created

        files = connection.execute(old_file_table.select().where(old_file_table.c.posts_id == assignment.posts_id))
        for file in files:
            file_id = file.id

        self_eval_types = connection.execute(old_assignment_self_eval_table.select().where(
            old_assignment_self_eval_table.c.questions_id == assignment.id))
        for self_eval_type in self_eval_types:
            enable_self_evaluation = True


        connection.execute(
            new_assignment_table.insert().values(
                id=assignment.id, user_id=user_id, course_id=course_id,
                file_id=file_id, name=assignment.title, description=description,
                answer_start=assignment.answer_start, answer_end=assignment.answer_end,
                compare_start=assignment.judge_start, compare_end=assignment.judge_end,
                number_of_comparisons=assignment.num_judgement_req,
                students_can_reply=assignment.can_reply,
                enable_self_evaluation=enable_self_evaluation,
                active=True,
                modified=assignment.modified, created=created
            )
        )

    for user_course in connection.execute(old_user_course_table.select()):
        group_name = None
        group_ids = []
        modified = user_course.modified if user_course.modified else datetime.utcnow()
        created = user_course.created if user_course.created else datetime.utcnow()

        user_groups = connection.execute(old_user_group_table.select().where(sa.and_(
            old_user_group_table.c.users_id == user_course.users_id,
            old_user_group_table.c.active == True
        )))

        for user_group in user_groups:
            group_ids.append(user_group.groups_id)

        if len(group_ids) > 0:
            course_groups = connection.execute(old_group_table.select().where(sa.and_(
                old_group_table.c.courses_id == user_course.courses_id,
                old_group_table.c.active == True,
                old_group_table.c.id.in_(group_ids)
            )))

            for course_group in course_groups:
                group_name = course_group.name

        connection.execute(
            new_user_course_table.insert().values(
                id=user_course.id, user_id=user_course.users_id, course_id=user_course.courses_id,
                course_role=translate_course_role(user_course.usertypesforcourse_id),
                group_name=group_name,
                modified=modified, created=created
            )
        )

    for answer in connection.execute(old_answer_table.select()):
        user_id = None
        file_id = None
        content = None
        modified = datetime.utcnow()
        created = datetime.utcnow()

        posts = connection.execute(old_posts_table.select().where(old_posts_table.c.id == answer.posts_id))
        for post in posts:
            user_id = post.users_id
            content = post.content
            modified = post.modified
            created = post.created

        files = connection.execute(old_file_table.select().where(old_file_table.c.posts_id == answer.posts_id))
        for file in files:
            file_id = file.id

        connection.execute(
            new_answer_table.insert().values(
                id=answer.id, assignment_id=answer.questions_id, user_id=user_id,
                file_id=file_id, content=content, round=answer.round,
                flagged=answer.flagged, flagger_user_id=answer.users_id_flagger,
                active=True,
                modified=modified, created=created
            )
        )

    for assignment_comment in connection.execute(old_assignment_comment_table.select()):
        user_id = None
        content = None
        modified = datetime.utcnow()
        created = datetime.utcnow()

        comments = connection.execute(old_comment_table.select().where(
            old_comment_table.c.id == assignment_comment.comments_id))

        for comment in comments:
            posts = connection.execute(old_posts_table.select().where(old_posts_table.c.id == comment.posts_id))
            for post in posts:
                user_id = post.users_id
                content = post.content
                modified = post.modified
                created = post.created

        connection.execute(
            new_assignment_comment_table.insert().values(
                id=assignment_comment.id, assignment_id=assignment_comment.questions_id,
                user_id=user_id, content=content,
                active=True,
                modified=modified, created=created
            )
        )

    for assignment_criterion in connection.execute(old_assignment_criterion_table.select()):
        connection.execute(
            new_assignment_criterion_table.insert().values(
                id=assignment_criterion.id, assignment_id=assignment_criterion.questions_id,
                criterion_id=assignment_criterion.criteria_id, active=assignment_criterion.active,
                modified=datetime.utcnow(), created=datetime.utcnow()
            )
        )

    for answer_comment in connection.execute(old_answer_comment_table.select()):
        user_id = None
        content = None
        modified = datetime.utcnow()
        created = datetime.utcnow()

        comments = connection.execute(old_comment_table.select().where(
            old_comment_table.c.id == answer_comment.comments_id))

        for comment in comments:
            posts = connection.execute(old_posts_table.select().where(old_posts_table.c.id == comment.posts_id))
            for post in posts:
                user_id = post.users_id
                content = post.content
                modified = post.modified
                created = post.created

        connection.execute(
            new_answer_comment_table.insert().values(
                id=answer_comment.id, answer_id=answer_comment.answers_id,
                user_id=user_id, content=content,
                comment_type=translate_answer_comment_type(answer_comment.evaluation,
                    answer_comment.selfeval, answer_comment.type),
                active=True,
                modified=modified, created=created
            )
        )

    for comparison in connection.execute(old_comparison_table.select()):
        answer1_id = None
        answer2_id = None

        assignment_id = None
        criterion_id = None

        content = None
        modified = datetime.utcnow()
        created = datetime.utcnow()

        pairs = connection.execute(old_pair_table.select().where(
            old_pair_table.c.id == comparison.answerpairings_id))

        for pair in pairs:
            answer1_id = pair.answers_id1
            answer2_id = pair.answers_id2
            assignment_id = pair.questions_id

        assignment_criteria = connection.execute(old_assignment_criterion_table.select().where(
            old_assignment_criterion_table.c.id == comparison.criteriaandquestions_id))

        for assignment_criterion in assignment_criteria:
            criterion_id = assignment_criterion.criteria_id

        comparison_comments = connection.execute(old_comparison_comment_table.select().where(
            old_comparison_comment_table.c.judgements_id == comparison.id))

        for comparison_comment in comparison_comments:
            comments = connection.execute(old_comment_table.select().where(
                old_comment_table.c.id == comparison_comment.comments_id))

            for comment in comments:
                posts = connection.execute(old_posts_table.select().where(old_posts_table.c.id == comment.posts_id))
                for post in posts:
                    content = post.content
                    modified = post.modified
                    created = post.created

        connection.execute(
            new_comparison_table.insert().values(
                id=comparison.id, assignment_id=assignment_id,
                user_id=comparison.users_id, criterion_id=criterion_id,
                answer1_id=answer1_id, answer2_id=answer2_id,
                winner_id=comparison.answers_id_winner, round_compared=0,
                content=content, completed=True,
                modified=modified, created=created
            )
        )

    for score in connection.execute(old_score_table.select()):
        assignment_id = None
        criterion_id = None

        assignment_criteria = connection.execute(old_assignment_criterion_table.select().where(
            old_assignment_criterion_table.c.id == score.criteriaandquestions_id))

        for assignment_criterion in assignment_criteria:
            criterion_id = assignment_criterion.criteria_id
            assignment_id = assignment_criterion.questions_id

        connection.execute(
            new_score_table.insert().values(
                id=score.id, assignment_id=assignment_id,
                answer_id=score.answers_id, criterion_id=criterion_id,
                score=score.score, excepted_score=score.score, rounds=score.rounds,
                wins=score.wins, opponents=0,
                modified=datetime.utcnow(), created=datetime.utcnow()
            )
        )
    # STEP 3: Handle activity log
    try:
        # expected foreign key to follow naming conventions
        with op.batch_alter_table('Activities', naming_convention=convention) as batch_op:
            # drop the fk before altering the column
            batch_op.drop_constraint('fk_Activities_users_id_Users', 'foreignkey')
            batch_op.drop_constraint('fk_Activities_courses_id_Courses', 'foreignkey')
    except exc.InternalError:
        # if not, it is likely this name
        with op.batch_alter_table('Activities') as batch_op:
            # drop the fk before altering the column
            batch_op.drop_constraint('Activities_ibfk_1', 'foreignkey')
            batch_op.drop_constraint('Activities_ibfk_2', 'foreignkey')

    op.rename_table('Activities', 'activity_log')

    with op.batch_alter_table('activity_log', naming_convention=convention) as batch_op:
        # alter columns
        batch_op.alter_column('users_id', new_column_name='user_id', nullable=True, existing_type=sa.Integer)
        batch_op.alter_column('courses_id', new_column_name='course_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('activity_log', naming_convention=convention) as batch_op:
        # create the fk
        batch_op.create_foreign_key('fk_activity_log_user_id_user', 'user', ['user_id'], ['id'], ondelete="SET NULL")
        batch_op.create_foreign_key('fk_activity_log_course_id_course', 'course', ['course_id'], ['id'], ondelete="SET NULL")

    # STEP 4: Drop old tables
    op.drop_table('CriteriaAndCourses')
    op.drop_table('LTIInfo')
    op.drop_table('AnswersAndComments')
    op.drop_table('QuestionsAndComments')
    op.drop_table('Tags')
    op.drop_table('PostsForJudgements')
    op.drop_table('CoursesAndUsers')
    op.drop_table('FilesForPosts')
    op.drop_table('Scores')
    op.drop_table('QuestionsAndSelfEvalTypes')
    op.drop_table('GroupsAndUsers')
    op.drop_table('Groups')
    op.drop_table('SelfEvalTypes')
    op.drop_table('Comments')
    op.drop_table('Judgements')
    op.drop_table('AnswerPairings')
    op.drop_table('CriteriaAndQuestions')
    op.drop_table('Answers')
    op.drop_table('Criteria')
    op.drop_table('Questions')
    op.drop_table('Posts')
    op.drop_table('Courses')
    op.drop_table('UserTypesForCourse')
    op.drop_table('Users')
    op.drop_table('UserTypesForSystem')
    ### end Alembic commands ###


def downgrade():
    def translate_system_role(system_role):
        if system_role == SystemRole.student:
            return 1
        elif system_role == SystemRole.instructor:
            return 2
        elif system_role == SystemRole.sys_admin:
            return 3

    def translate_course_role(course_role):
        if course_role == CourseRole.dropped:
            return 1
        elif course_role == CourseRole.instructor:
            return 2
        elif course_role == CourseRole.teaching_assistant:
            return 3
        elif course_role == CourseRole.student:
            return 4

    def answer_comment_self_eval(answer_comment_type):
        return answer_comment_type == AnswerCommentType.self_evaluation

    def answer_comment_evaluation(answer_comment_type):
        return answer_comment_type == AnswerCommentType.evaluation

    def answer_comment_type(answer_comment_type):
        return answer_comment_type == AnswerCommentType.public

    new_user_table = sa.table('user',
        sa.column('id', sa.Integer), sa.Column('username', sa.String), sa.Column('_password', sa.String),
        sa.Column('system_role', EnumType(SystemRole)), sa.Column('email', sa.String),
        sa.Column('firstname', sa.String), sa.Column('lastname', sa.String), sa.Column('displayname', sa.String),
        sa.Column('last_online', sa.DateTime), sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
        sa.Column('student_number', sa.String)
    )

    new_course_table = sa.table('course',
        sa.column('id', sa.Integer), sa.Column('name', sa.String), sa.Column('description', sa.Text),
        sa.Column('active', sa.Boolean),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    new_criterion_table = sa.table('criterion',
        sa.column('id', sa.Integer), sa.Column('user_id', sa.Integer),
        sa.Column('name', sa.String), sa.Column('description', sa.Text),
        sa.Column('public', sa.Boolean), sa.Column('default', sa.Boolean),
        sa.Column('active', sa.Boolean),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    new_file_table = sa.table('file',
        sa.column('id', sa.Integer), sa.column('user_id', sa.Integer),
        sa.Column('name', sa.String), sa.Column('alias', sa.String),
        sa.Column('active', sa.Boolean)
    )

    new_assignment_table = sa.table('assignment',
        sa.column('id', sa.Integer), sa.column('user_id', sa.Integer), sa.column('course_id', sa.Integer),
        sa.column('file_id', sa.Integer), sa.column('name', sa.String), sa.column('description', sa.Text),
        sa.Column('answer_start', sa.DATETIME), sa.Column('answer_end', sa.DATETIME),
        sa.Column('compare_start', sa.DATETIME), sa.Column('compare_end', sa.DATETIME),
        sa.Column('number_of_comparisons', sa.Integer), sa.Column('students_can_reply', sa.Boolean),
        sa.Column('enable_self_evaluation', sa.Boolean),
        sa.Column('active', sa.Boolean),
        sa.Column('created', sa.DateTime), sa.Column('modified', sa.DateTime)
    )

    new_user_course_table = sa.table('user_course',
        sa.column('id', sa.Integer), sa.column('course_id', sa.Integer), sa.column('user_id', sa.Integer),
        sa.column('course_role', EnumType(CourseRole)), sa.column('group_name', sa.String),
        sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime)
    )

    new_answer_table = sa.table('answer',
        sa.column('id', sa.Integer), sa.column('user_id', sa.Integer), sa.column('assignment_id', sa.Integer),
        sa.column('file_id', sa.Integer), sa.column('content', sa.Text),
        sa.column('flagged', sa.Boolean), sa.column('flagger_user_id', sa.Integer), sa.column('round', sa.Integer),
        sa.Column('active', sa.Boolean),
        sa.Column('created', sa.DateTime), sa.Column('modified', sa.DateTime)
    )

    new_assignment_comment_table = sa.table('assignment_comment',
        sa.column('id', sa.Integer), sa.column('assignment_id', sa.Integer),
        sa.column('user_id', sa.Integer), sa.column('content', sa.Text),
        sa.Column('active', sa.Boolean),
        sa.Column('created', sa.DateTime), sa.Column('modified', sa.DateTime)
    )

    new_assignment_criterion_table = sa.table('assignment_criterion',
        sa.column('id', sa.Integer), sa.column('criterion_id', sa.Integer), sa.column('assignment_id', sa.Integer),
        sa.Column('active', sa.Boolean),
        sa.Column('created', sa.DateTime), sa.Column('modified', sa.DateTime)
    )

    new_answer_comment_table = sa.table('answer_comment',
        sa.column('id', sa.Integer), sa.column('answer_id', sa.Integer), sa.column('comment_type', EnumType(AnswerCommentType)),
        sa.column('user_id', sa.Integer), sa.column('content', sa.Text),
        sa.Column('active', sa.Boolean),
        sa.Column('created', sa.DateTime), sa.Column('modified', sa.DateTime)
    )

    new_comparison_table = sa.table('comparison',
        sa.column('id', sa.Integer), sa.column('assignment_id', sa.Integer), sa.column('criterion_id', sa.Integer),
        sa.column('answer1_id', sa.Integer), sa.column('answer2_id', sa.Integer), sa.column('winner_id', sa.Integer),
        sa.column('round_compared', sa.Integer), sa.column('completed', sa.Boolean),
        sa.column('user_id', sa.Integer), sa.column('content', sa.Text),
        sa.Column('created', sa.DateTime), sa.Column('modified', sa.DateTime)
    )

    new_score_table = sa.table('score',
        sa.column('id', sa.Integer), sa.column('assignment_id', sa.Integer),
        sa.column('answer_id', sa.Integer), sa.column('criterion_id', sa.Integer),
        sa.column('score', sa.Float), sa.column('rounds', sa.Integer), sa.column('wins', sa.Integer),
        sa.Column('created', sa.DateTime), sa.Column('modified', sa.DateTime)
    )
    ### commands auto generated by Alembic - please adjust! ###

    # STEP 1: Create old tables
    old_user_system_types = op.create_table(
        'UserTypesForSystem',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_user_table = op.create_table(
        'Users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('_password', sa.String(length=255), nullable=False),
        sa.Column('usertypesforsystem_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('firstname', sa.String(length=255), nullable=True),
        sa.Column('lastname', sa.String(length=255), nullable=True),
        sa.Column('displayname', sa.String(length=255), nullable=False),
        sa.Column('lastonline', sa.DateTime(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('student_no', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['usertypesforsystem_id'], ['UserTypesForSystem.id'], name='Users_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_user_course_type_table = op.create_table(
        'UserTypesForCourse',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_course_table = op.create_table(
        'Courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('available', sa.Boolean(), nullable=False),
        sa.Column('enable_student_create_questions', sa.Boolean(), nullable=False),
        sa.Column('enable_student_create_tags', sa.Boolean(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_posts_table = op.create_table(
        'Posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('users_id', sa.Integer(), nullable=False),
        sa.Column('courses_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], name='Posts_ibfk_2', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['users_id'], ['Users.id'], name='Posts_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_assignment_table = op.create_table(
        'Questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('posts_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('answer_start', sa.DateTime(), nullable=True),
        sa.Column('answer_end', sa.DateTime(), nullable=True),
        sa.Column('judge_start', sa.DateTime(), nullable=True),
        sa.Column('judge_end', sa.DateTime(), nullable=True),
        sa.Column('num_judgement_req', sa.Integer(), nullable=False),
        sa.Column('can_reply', sa.Boolean(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['posts_id'], ['Posts.id'], name='Questions_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_criteria_table = op.create_table(
        'Criteria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('users_id', sa.Integer(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('public', sa.Boolean(), nullable=False),
        sa.Column('default', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['users_id'], ['Users.id'], name='Criteria_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_answer_table = op.create_table(
        'Answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('posts_id', sa.Integer(), nullable=False),
        sa.Column('questions_id', sa.Integer(), nullable=True),
        sa.Column('flagged', sa.Boolean(), nullable=False),
        sa.Column('users_id_flagger', sa.Integer(), nullable=True),
        sa.Column('round', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['posts_id'], ['Posts.id'], name='Answers_ibfk_1', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['questions_id'], ['Questions.id'], name='fk_Answers_questions_id_Questions', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['users_id_flagger'], ['Users.id'], name='Answers_ibfk_3', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_assignment_criteria_table = op.create_table(
        'CriteriaAndQuestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=False),
        sa.Column('questions_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['criteria_id'], ['Criteria.id'], name='fk_CriteriaAndQuestions_criteria_id_Criteria', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['questions_id'], ['Questions.id'], name='fk_CriteriaAndQuestions_questions_id_Questions', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_pair_table = op.create_table(
        'AnswerPairings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('questions_id', sa.Integer(), nullable=True),
        sa.Column('answers_id1', sa.Integer(), nullable=True),
        sa.Column('answers_id2', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('criteriaandquestions_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['answers_id1'], ['Answers.id'], name='fk_AnswerPairings_answers_id1_Answers', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['answers_id2'], ['Answers.id'], name='fk_AnswerPairings_answers_id2_Answers', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criteriaandquestions_id'], ['CriteriaAndQuestions.id'], name='fk_AnswerPairings_criteriaandquestions_id_CriteriaAndQuestions', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['questions_id'], ['Questions.id'], name='fk_AnswerPairings_questions_id_Questions', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_comparisons_table = op.create_table(
        'Judgements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('users_id', sa.Integer(), nullable=False),
        sa.Column('answerpairings_id', sa.Integer(), nullable=False),
        sa.Column('answers_id_winner', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('criteriaandquestions_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['answerpairings_id'], ['AnswerPairings.id'], name='Judgements_ibfk_2', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['answers_id_winner'], ['Answers.id'], name='fk_Judgements_answers_id_winner_Answers', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criteriaandquestions_id'], ['CriteriaAndQuestions.id'], name='fk_Judgements_criteriaandquestions_id_CriteriaAndQuestions', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['users_id'], ['Users.id'], name='Judgements_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_comments_table = op.create_table(
        'Comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('posts_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['posts_id'], ['Posts.id'], name='Comments_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_self_eval_types_table = op.create_table(
        'SelfEvalTypes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_group_table = op.create_table(
        'Groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('courses_id', sa.Integer(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], name='Groups_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_user_group_table = op.create_table(
        'GroupsAndUsers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('groups_id', sa.Integer(), nullable=False),
        sa.Column('users_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['groups_id'], ['Groups.id'], name='GroupsAndUsers_ibfk_2', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['users_id'], ['Users.id'], name='GroupsAndUsers_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_assignment_self_eval_types = op.create_table(
        'QuestionsAndSelfEvalTypes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('questions_id', sa.Integer(), nullable=False),
        sa.Column('selfevaltypes_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['questions_id'], ['Questions.id'], name='fk_QuestionsAndSelfEvalTypes_questions_id_Questions', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selfevaltypes_id'], ['SelfEvalTypes.id'], name='fk_QuestionsAndSelfEvalTypes_selfevaltypes_id_SelfEvalTypes', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_score_table = op.create_table(
        'Scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('answers_id', sa.Integer(), nullable=False),
        sa.Column('rounds', sa.Integer(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('criteriaandquestions_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['answers_id'], ['Answers.id'], name='fk_Scores_answers_id_Answers', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criteriaandquestions_id'], ['CriteriaAndQuestions.id'], name='fk_Scores_criteriaandquestions_id_CriteriaAndQuestions', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_file_table = op.create_table(
        'FilesForPosts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('posts_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['Users.id'], name='FilesForPosts_ibfk_2', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['posts_id'], ['Posts.id'], name='FilesForPosts_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_user_courses_table = op.create_table(
        'CoursesAndUsers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('courses_id', sa.Integer(), nullable=False),
        sa.Column('users_id', sa.Integer(), nullable=False),
        sa.Column('usertypesforcourse_id', sa.Integer(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], name='CoursesAndUsers_ibfk_1'),
        sa.ForeignKeyConstraint(['users_id'], ['Users.id'], name='CoursesAndUsers_ibfk_2'),
        sa.ForeignKeyConstraint(['usertypesforcourse_id'], ['UserTypesForCourse.id'], name='CoursesAndUsers_ibfk_3', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_comparisons_comment_table =  op.create_table(
        'PostsForJudgements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comments_id', sa.Integer(), nullable=True),
        sa.Column('judgements_id', sa.Integer(), nullable=False),
        sa.Column('selfeval', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['comments_id'], ['Comments.id'], name='fk_PostsForJudgements_comments_id_Comments', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['judgements_id'], ['Judgements.id'], name='PostsForJudgements_ibfk_2', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    op.create_table(
        'Tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('courses_id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], name='Tags_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_assignment_comment_table = op.create_table(
        'QuestionsAndComments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('questions_id', sa.Integer(), nullable=True),
        sa.Column('comments_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['comments_id'], ['Comments.id'], name='fk_QuestionsAndComments_comments_id_Comments', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['questions_id'], ['Questions.id'], name='fk_PostsForQuestionsAndPostsForComments_questions_id_Questions', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_answer_comment_table = op.create_table(
        'AnswersAndComments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('answers_id', sa.Integer(), nullable=True),
        sa.Column('comments_id', sa.Integer(), nullable=True),
        sa.Column('evaluation', sa.Boolean(), nullable=False),
        sa.Column('selfeval', sa.Boolean(), nullable=False),
        sa.Column('type', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['answers_id'], ['Answers.id'], name='fk_AnswersAndComments_answers_id_Answers', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['comments_id'], ['Comments.id'], name='fk_AnswersAndComments_comments_id_Comments', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    op.create_table(
        'LTIInfo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('LTIid', sa.String(length=100), nullable=True),
        sa.Column('LTIURL', sa.String(length=100), nullable=True),
        sa.Column('courses_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], name='LTIInfo_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )

    old_course_criteria_table = op.create_table(
        'CriteriaAndCourses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=False),
        sa.Column('courses_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['courses_id'], ['Courses.id'], name='CriteriaAndCourses_ibfk_2', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criteria_id'], ['Criteria.id'], name='CriteriaAndCourses_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8_unicode_ci',
        mysql_default_charset='utf8',
        mysql_engine='InnoDB'
    )
    # STEP 2: Migrate data
    connection = op.get_bind()

    def create_comment(users_id, courses_id, content, modified=datetime.utcnow(), created=datetime.utcnow()):
        posts_id = create_post(users_id, courses_id, content, modified, created)
        result = connection.execute(
            old_comments_table.insert().values(
                posts_id=posts_id
            )
        )
        return result.lastrowid

    def create_post(users_id, courses_id, content, modified=datetime.utcnow(), created=datetime.utcnow()):
        result = connection.execute(
            old_posts_table.insert().values(
                users_id=users_id, courses_id=courses_id, content=content,
                modified=modified, created=created
            )
        )
        return result.lastrowid

    def create_file_for_post(file_id, posts_id):
        files = connection.execute(new_file_table.select().where(new_file_table.c.id == file_id))
        for file in files:
            connection.execute(
                old_file_table.insert().values(
                    id=file_id, posts_id=posts_id,
                    author_id=file.user_id,
                    name=file.name, alias=file.alias
                )
            )

    def find_or_create_pair(questions_id, answers_id1, answers_id2, criteriaandquestions_id):
        pairs = connection.execute(old_pair_table.select().where(sa.and_(
            old_pair_table.c.questions_id == questions_id,
            old_pair_table.c.answers_id1 == answers_id1,
            old_pair_table.c.answers_id2 == answers_id2,
            old_pair_table.c.criteriaandquestions_id == criteriaandquestions_id
        )))

        for pair in pairs:
            return pair.id


        result = connection.execute(
            old_pair_table.insert().values(
                questions_id=questions_id, answers_id1=answers_id1,
                answers_id2=answers_id2, criteriaandquestions_id=criteriaandquestions_id,
                modified=datetime.utcnow(), created=datetime.utcnow()
            )
        )
        return result.lastrowid

    op.bulk_insert(old_user_system_types,
        [
            {'id':1, 'name':'Student'},
            {'id':2, 'name':'Instructor'},
            {'id':3, 'name':'System Administrator'}
        ]
    )

    op.bulk_insert(old_user_course_type_table,
        [
            {'id':1, 'name':'Dropped'},
            {'id':2, 'name':'Instructor'},
            {'id':3, 'name':'Teaching Assistant'},
            {'id':4, 'name':'Student'}
        ]
    )

    op.bulk_insert(old_self_eval_types_table,
        [
            {'id':1, 'name':'No Comparison with Another Answer'}
        ]
    )

    for user in connection.execute(new_user_table.select()):
        connection.execute(
            old_user_table.insert().values(
                id=user.id, username=user.username, _password=user._password,
                usertypesforsystem_id=translate_system_role(user.system_role),
                displayname=user.displayname, email=user.email,
                firstname=user.firstname, lastname=user.lastname,
                student_no=user.student_number, lastonline=user.last_online,
                modified=user.modified, created=user.created
            )
        )

    for course in connection.execute(new_course_table.select().where(new_course_table.c.active == True)):
        connection.execute(
            old_course_table.insert().values(
                id=course.id, name=course.name, description=course.description,
                available=True,
                enable_student_create_tags=False,
                enable_student_create_questions=False,
                modified=course.modified, created=course.created
            )
        )

    for criterion in connection.execute(new_criterion_table.select().where(new_criterion_table.c.active == True)):
        connection.execute(
            old_criteria_table.insert().values(
                id=criterion.id, users_id=criterion.user_id,
                name=criterion.name, description=criterion.description,
                public=criterion.public, default=criterion.default,
                modified=criterion.modified, created=criterion.created
            )
        )

    for assignment in connection.execute(new_assignment_table.select().where(new_assignment_table.c.active == True)):
        posts_id = create_post(assignment.user_id, assignment.course_id, assignment.description,
            assignment.modified, assignment.created)

        if assignment.file_id:
            create_file_for_post(assignment.file_id, posts_id)

        result = connection.execute(
            old_assignment_table.insert().values(
                id=assignment.id, posts_id=posts_id, title=assignment.name,
                answer_start=assignment.answer_start, answer_end=assignment.answer_end,
                judge_start=assignment.compare_start, judge_end=assignment.compare_end,
                num_judgement_req=assignment.number_of_comparisons,
                can_reply=assignment.students_can_reply,
                modified=assignment.modified
            )
        )

        if assignment.enable_self_evaluation:
            connection.execute(
                old_assignment_self_eval_types.insert().values(
                    questions_id=result.lastrowid, selfevaltypes_id=1
                )
            )

    # course_groups[courseId] = dictionary objects with name and list of users in the group
    course_groups = {}

    for user_course in connection.execute(new_user_course_table.select()):

        if user_course.group_name:
            group_dictionary = course_groups.setdefault(user_course.course_id, {})
            course_group = group_dictionary.setdefault(user_course.group_name, set())
            course_group.add(user_course.user_id)

        connection.execute(
            old_user_courses_table.insert().values(
                id=user_course.id, users_id=user_course.user_id, courses_id=user_course.course_id,
                usertypesforcourse_id=translate_course_role(user_course.course_role),
                modified=user_course.modified, created=user_course.created
            )
        )

    for course_id, group_dictionary in course_groups.items():
        for group_name, user_set in group_dictionary.items():
            result = connection.execute(
                old_group_table.insert().values(
                    name=group_name, active=True, courses_id=course_id,
                    modified=datetime.utcnow(), created=datetime.utcnow()
                )
            )
            group_id = result.lastrowid

            for user_id in user_set:
                connection.execute(
                    old_user_group_table.insert().values(
                        groups_id=group_id, active=True, users_id=user_id,
                        modified=datetime.utcnow(), created=datetime.utcnow()
                    )
                )

    for answer in connection.execute(new_answer_table.select().where(new_answer_table.c.active == True)):
        course_id = None

        assignments = connection.execute(new_assignment_table.select().where(new_assignment_table.c.id == answer.assignment_id))
        for assignment in assignments:
            course_id = assignment.course_id

        posts_id = create_post(answer.user_id, course_id, answer.content,
            answer.modified, answer.created)

        if answer.file_id:
            create_file_for_post(answer.file_id, posts_id)

        connection.execute(
            old_answer_table.insert().values(
                id=answer.id, posts_id=posts_id, questions_id=answer.assignment_id,
                round=answer.round,
                flagged=answer.flagged, users_id_flagger=answer.flagger_user_id
            )
        )

    for assignment_comment in connection.execute(new_assignment_comment_table.select().where(new_assignment_comment_table.c.active == True)):
        course_id = None

        assignments = connection.execute(new_assignment_table.select().where(new_assignment_table.c.id == assignment_comment.assignment_id))
        for assignment in assignments:
            course_id = assignment.course_id

        comments_id = create_comment(assignment_comment.user_id, course_id, assignment_comment.content,
            assignment_comment.modified, assignment_comment.created)

        connection.execute(
            old_assignment_comment_table.insert().values(
                id=assignment_comment.id, questions_id=assignment_comment.assignment_id,
                comments_id=comments_id
            )
        )


    course_criteria = {}
    assignment_criteria = {}

    for assignment_criterion in connection.execute(new_assignment_criterion_table.select().where(new_assignment_criterion_table.c.active == True)):
        course_id = None

        assignments = connection.execute(new_assignment_table.select().where(new_assignment_table.c.id == assignment_criterion.assignment_id))
        for assignment in assignments:
            course_id = assignment.course_id

        if course_id:
            course_criteria.setdefault(course_id, set())
            course_criteria[course_id].add(assignment_criterion.criterion_id)


        criteria = assignment_criteria.setdefault(assignment_criterion.assignment_id, {})
        criteria.setdefault(assignment_criterion.criterion_id, assignment_criterion.id)

        connection.execute(
            old_assignment_criteria_table.insert().values(
                id=assignment_criterion.id, questions_id=assignment_criterion.assignment_id,
                criteria_id=assignment_criterion.criterion_id, active=assignment_criterion.active
            )
        )

    for course_id, criteria_set in course_criteria.items():
        for criterion_id in criteria_set:
            connection.execute(
                old_course_criteria_table.insert().values(
                    criteria_id=criterion_id, courses_id=course_id, active=True
                )
            )

    for answer_comment in connection.execute(new_answer_comment_table.select().where(new_answer_comment_table.c.active == True)):
        course_id = None
        assignment_id = None

        answers = connection.execute(new_answer_table.select().where(new_answer_table.c.id == answer_comment.answer_id))
        for answer in answers:
            assignment_id = answer.assignment_id

        assignments = connection.execute(new_assignment_table.select().where(new_assignment_table.c.id == assignment_id))
        for assignment in assignments:
            course_id = assignment.course_id

        comments_id = create_comment(answer_comment.user_id, course_id, answer_comment.content,
            answer_comment.modified, answer_comment.created)

        connection.execute(
            old_answer_comment_table.insert().values(
                id=answer_comment.id, answers_id=answer_comment.answer_id,
                comments_id=comments_id,
                evaluation=answer_comment_evaluation(answer_comment.comment_type),
                selfeval=answer_comment_self_eval(answer_comment.comment_type),
                type=answer_comment_type(answer_comment.comment_type)
            )
        )

    for comparison in connection.execute(new_comparison_table.select()):
        criteriaandquestions_id = assignment_criteria[comparison.assignment_id][comparison.criterion_id]

        pair_id = find_or_create_pair(comparison.assignment_id, comparison.answer1_id, comparison.answer2_id,
            criteriaandquestions_id)

        course_id = None

        assignments = connection.execute(new_assignment_table.select().where(new_assignment_table.c.id == assignment_criterion.assignment_id))
        for assignment in assignments:
            course_id = assignment.course_id

        comments_id = create_comment(comparison.user_id, course_id, comparison.content,
            comparison.modified, comparison.created)

        result = connection.execute(
            old_comparisons_table.insert().values(
                id=comparison.id,
                users_id=comparison.user_id, answerpairings_id=pair_id,
                criteriaandquestions_id=criteriaandquestions_id,
                answers_id_winner=comparison.winner_id,
                modified=comparison.modified, created=comparison.created
            )
        )

        comparison_id = result.lastrowid

        connection.execute(
            old_comparisons_comment_table.insert().values(
                comments_id=comments_id, judgements_id=comparison_id,
                selfeval=False
            )
        )


    for score in connection.execute(new_score_table.select()):
        criteriaandquestions_id = assignment_criteria[score.assignment_id][score.criterion_id]

        connection.execute(
            old_score_table.insert().values(
                id=score.id, answers_id=score.answer_id,
                criteriaandquestions_id=criteriaandquestions_id,
                score=score.score, rounds=score.rounds,
                wins=score.wins
            )
        )


    # STEP 3: Handle activilty log
    with op.batch_alter_table('activity_log', naming_convention=convention) as batch_op:
        # drop the fk before altering the column
        batch_op.drop_constraint('fk_activity_log_user_id_user', 'foreignkey')
        batch_op.drop_constraint('fk_activity_log_course_id_course', 'foreignkey')

        # alter columns
        batch_op.alter_column('user_id', new_column_name='users_id', nullable=True, existing_type=sa.Integer)
        batch_op.alter_column('course_id', new_column_name='courses_id', nullable=True, existing_type=sa.Integer)

    with op.batch_alter_table('activity_log', naming_convention=convention) as batch_op:
        # recreate the fk
        batch_op.create_foreign_key('fk_activity_log_users_id_Users', 'Users', ['users_id'], ['id'], ondelete="SET NULL")
        batch_op.create_foreign_key('fk_activity_log_courses_id_Courses', 'Courses', ['courses_id'], ['id'], ondelete="SET NULL")

    op.rename_table('activity_log', 'Activities')


    # STEP 4: Drop new tables
    op.drop_table('score')
    op.drop_table('comparison')
    op.drop_table('answer_comment')
    op.drop_table('assignment_criterion')
    op.drop_table('assignment_comment')
    op.drop_table('answer')
    op.drop_table('user_course')
    op.drop_table('assignment')
    op.drop_table('file')
    op.drop_table('criterion')
    op.drop_table('course')
    op.drop_table('user')
    ### end Alembic commands ###
