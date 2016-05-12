# Template for creating a new table. Note, the first 3 are taken care of by
# the default_table_args defined in database.py.
# * If MySQL, table engine must be InnoDB, for native foreign key support.
# * The default character set must be utf8, cause utf8 everywhere makes
#   text encodings much easier to deal with.
# * Collation is using the slightly slower utf8_unicode_ci due to it's better
#   conformance to human expectations for sorting.
# * There must always be a primary key id field.
# * creation_time and modification_time fields are self updating, they're nice
#   to have for troubleshooting, but not all tables need them.
# * Additional fields given are meant for reference only.
# * Foreign keys must be named in the format of <tablename>_id for
#   consistency.
# * 'ON DELETE CASCADE' is the preferred resolution method so that we don't
#   have to worry about database consistency as much.
# * Junction tables names must be the two table's names, connected by
#   "And".
# * Some tables might have subcategories, use the word "For" to indicated the
#   subcategory, e.g.: we have a "Posts" table for all posts and a
#   "PostsForQuestions" table for posts that are meant to be questions

import hashlib
import datetime
import time
import math
import warnings

import dateutil.parser
from flask import current_app
import pytz
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import synonym, load_only, column_property, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from flask.ext.login import UserMixin

import acj.algorithms
from acj.algorithms.comparison_pair import ComparisonPair
from acj.algorithms.comparison_result import ComparisonResult

# User types at the course level
from .core import db
from acj import security

# All tables should have this set of options enabled to make porting easier.
# In case we have to move to MariaDB instead of MySQL, e.g.: InnoDB in MySQL
# is replaced by XtraDB.

default_table_args = {
    'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB',
    'mysql_collate': 'utf8_unicode_ci'}

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db.metadata.naming_convention = convention

#################################################
# Users
#################################################


class UserTypesForCourse(db.Model):
    __tablename__ = "UserTypesForCourse"
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)

    # constants for the user types
    TYPE_DROPPED = "Dropped"
    TYPE_STUDENT = "Student"
    TYPE_TA = "Teaching Assistant"
    TYPE_INSTRUCTOR = "Instructor"


# User types at the system level
class UserTypesForSystem(db.Model):
    __tablename__ = "UserTypesForSystem"
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)

    TYPE_NORMAL = "Student"
    TYPE_INSTRUCTOR = "Instructor"
    TYPE_SYSADMIN = "System Administrator"


def hash_password(password, is_admin=False):
    category = None
    if is_admin:
        # enables more rounds for admin passwords
        category = "admin"
    pwd_context = getattr(security, current_app.config['PASSLIB_CONTEXT'])
    return pwd_context.encrypt(password, category=category)


# This could be used for token based authentication
# def verify_auth_token(token):
#     s = Serializer(current_app.config['SECRET_KEY'])
#     try:
#         data = s.loads(token)
#     except SignatureExpired:
#         return None  # valid token, but expired
#     except BadSignature:
#         return None  # invalid token
#
#     if 'id' not in data:
#         return None
#
#     return data['id']


# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    student_no = db.Column(db.String(50), unique=True, nullable=True)
    _password = db.Column(db.String(255), unique=False, nullable=False)

    # Apparently, enabling the equivalent of ON DELETE CASCADE requires
    # the ondelete option in the foreign key and the cascade + passive_deletes
    # option in db.relationship().
    usertypesforsystem_id = db.Column(
        db.Integer,
        db.ForeignKey('UserTypesForSystem.id', ondelete="CASCADE"),
        nullable=False)
    usertypeforsystem = db.relationship("UserTypesForSystem", innerjoin=True)

    email = db.Column(db.String(254))  # email addresses are max 254 characters, no
    # idea if the unicode encoding of email addr
    # changes this.
    firstname = db.Column(db.String(255))
    lastname = db.Column(db.String(255))
    displayname = db.Column(db.String(255))
    lastonline = db.Column(db.DateTime)
    # Note that MySQL before 5.6.5 doesn't allow more than one auto init/update
    # column for timestamps! Auto init/update after 5.6.5 allows multiple
    # columns and can be applied to the db.DateTime field as well. This means that
    # 'modified' can be counted on to be auto init/updated for manual
    # (non-SQLAlchemy) database operations while 'created' will not.
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)
    coursesandusers = db.relationship("CoursesAndUsers")
    groups = db.relationship(
        "GroupsAndUsers",
        primaryjoin="and_(Users.id==GroupsAndUsers.users_id, GroupsAndUsers.active)")
    # groups = association_proxy('user_groups', 'name')

    system_role = association_proxy('usertypeforsystem', 'name')

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = hash_password(password)

    password = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password)

    @hybrid_property
    def fullname(self):
        if self.firstname and self.lastname:
            return '%s %s' % (self.firstname, self.lastname)
        elif self.firstname:  # only first name provided
            return self.firstname
        elif self.lastname:  # only last name provided
            return self.lastname
        else:
            return None

    # According to gravatar's hash specs
    # 	1.Trim leading and trailing whitespace from an email address
    # 	2.Force all characters to lower-case
    # 	3.md5 hash the final string
    # Defaults to a hash of the user's username if no email is available
    @hybrid_property
    def avatar(self):
        hash_input = self.username
        if self.email:
            hash_input = self.email
        m = hashlib.md5()
        m.update(hash_input.strip().lower().encode('utf-8'))
        return m.hexdigest()

    def verify_password(self, password):
        pwd_context = getattr(security, current_app.config['PASSLIB_CONTEXT'])
        return pwd_context.verify(password, self.password)

    def update_lastonline(self):
        self.lastonline = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def generate_session_token(self):
        """
        Generate a session token that identifies the user login session. Since the flask
        wll generate the same session _id for the same IP and browser agent combination,
        it is hard to distinguish the users by session from the activity log
        """
        key = str(self.id) + str(time.time())
        return hashlib.md5(key.encode('UTF-8')).hexdigest()

    # This could be used for token based authentication
    # def generate_auth_token(self, expiration=60):
    #     s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    #     return s.dumps({'id': self.id})

    @hybrid_property
    def course_role(self):
        if len(self.coursesandusers) > 1:
            raise InvalidAttributeException(
                'Invalid course_role attribute status for user %s. '
                'CoursesAndUsers are not populated within a course' % self.username)
        elif len(self.coursesandusers) == 0:
            return 'Not Enrolled'
        else:
            return self.coursesandusers[0].usertypeforcourse.name

    @hybrid_property
    def group_id(self):
        """
        we only have one group per user-course. So we return single group_id
        :return: group id or 0 if there is no group
        """
        return self.groups[0].groups_id if len(self.groups) else 0

    @hybrid_property
    def group_name(self):
        """
        we only have one group per user-course. So we return single group name
        :return: group name or None if there is no group
        """
        return self.groups[0].group.name if len(self.groups) else None

    def __repr__(self):
        if self.username:
            return self.username
        else:
            return "User"

    def has_complete_judgment_for_question(self, question_id):
        """
        check if user has completed the required judgements
        :param question_id: the id of the question to check aginst
        :return: boolean
        """
        question = PostsForQuestions.query. \
            with_entities(PostsForQuestions.num_judgement_req, PostsForQuestions.criteria_count). \
            get(question_id)

        judgement_count = PostsForJudgements.query. \
            join(PostsForJudgements.postsforcomments). \
            join(PostsForComments.post). \
            filter_by(users_id=self.id).count()

        return judgement_count >= question.num_judgement_req * question.criteria_count

    def get_course_role(self, course_id):
        """ Return user's course role by course id """
        for course in self.coursesandusers:
            if course.courses_id == course_id:
                return course.usertypeforcourse.name

        return None


class InvalidAttributeException(Exception):
    pass

# # create a default root user with sysadmin role
# @event.listens_for(Users.__table__, "after_create", propagate=True)
# def populate_users(target, connection, **kw):
# 	sysadmintype = UserTypesForSystem.query.filter(
# 		UserTypesForSystem.name == UserTypesForSystem.TYPE_SYSADMIN).first()
# 	user = Users(username="root", displayname="root")
# 	user.set_password("password", True)
# 	user.usertypeforsystem = sysadmintype
# 	db_session.add(user)
# 	db_session.commit()


#################################################
# Courses and Enrolment
#################################################

class Courses(db.Model):
    __tablename__ = 'Courses'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    available = db.Column(db.Boolean(name='available'), default=True, nullable=False)
    coursesandusers = db.relationship("CoursesAndUsers", lazy="dynamic")
    criteriaandcourses = db.relationship(
        "CriteriaAndCourses",
        primaryjoin="and_(Courses.id==CriteriaAndCourses.courses_id, CriteriaAndCourses.active)")
    # allow students to make question posts
    enable_student_create_questions = db.Column(
        db.Boolean(name='enable_student_create_questions'), default=False,
        nullable=False)
    enable_student_create_tags = db.Column(
        db.Boolean(name='enable_student_create_tags'), default=False, nullable=False)
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)

    @classmethod
    def get_by_user(cls, user_id, inactive=False, fields=None):
        query = cls.query.join(CoursesAndUsers).filter_by(users_id=user_id)

        if not inactive:
            query = query.join(UserTypesForCourse).filter(
                UserTypesForCourse.name.notlike(UserTypesForCourse.TYPE_DROPPED))

        if fields:
            query = query.options(load_only(*fields))

        return query.order_by(cls.name).all()

    @classmethod
    def exists_or_404(cls, course_id):
        return cls.query.options(load_only('id')).get_or_404(course_id)

    def enroll(self, users, role=UserTypesForCourse.TYPE_STUDENT):
        if not isinstance(users, list):
            users = [users]

        user_role = UserTypesForCourse.query.filter_by(name=role).one()
        if not user_role:
            raise InvalidAttributeException('Invalid user role %s'.format(role))

        associations = []
        for user in users:
            associations.append(
                CoursesAndUsers(users_id=user.id, courses_id=self.id, usertypesforcourse_id=user_role.id)
            )

        db.session.bulk_save_objects(associations)


# A "junction table" in sqlalchemy is called a many-to-many pattern. Such a
# table can be automatically created by sqlalchemy from db.relationship
# definitions along. But if additional fields are needed, then we can
# explicitly define such a table using the "association object" pattern.
# For determining a course's users, we're using the association object approach
# since we need to declare the user's role in the course.
class CoursesAndUsers(db.Model):
    __tablename__ = 'CoursesAndUsers'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    courses_id = db.Column(db.Integer, db.ForeignKey("Courses.id"), nullable=False)
    course = db.relationship("Courses")
    users_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    user = db.relationship("Users")
    usertypesforcourse_id = db.Column(
        db.Integer,
        db.ForeignKey('UserTypesForCourse.id', ondelete="CASCADE"),
        nullable=False)
    usertypeforcourse = db.relationship("UserTypesForCourse")

    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)
    __table_args__ = (
        # prevent duplicate user in courses
        db.UniqueConstraint('courses_id', 'users_id', name='_unique_user_and_course'),
        default_table_args
    )

    @hybrid_property
    def groups(self):
        groups = self.user.groups
        return [group for group in groups if group.courses_id == self.courses_id]


#################################################
# Groups
#################################################

class Groups(db.Model):
    __tablename__ = 'Groups'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(name='active'), default=True, nullable=False)
    courses_id = db.Column(
        db.Integer,
        db.ForeignKey("Courses.id", ondelete="CASCADE"),
        nullable=False)
    course = db.relationship("Courses")
    members = db.relationship("GroupsAndUsers")
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)

    def enroll(self, users):
        if not isinstance(users, list):
            users = [users]

        associations = []
        for user in users:
            associations.append(
                GroupsAndUsers(users_id=user.id, groups_id=self.id)
            )

        db.session.bulk_save_objects(associations)


class GroupsAndUsers(db.Model):
    __tablename__ = 'GroupsAndUsers'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    groups_id = db.Column(
        db.Integer,
        db.ForeignKey("Groups.id", ondelete="CASCADE"),
        nullable=False)
    group = db.relationship("Groups")
    users_id = db.Column(
        db.Integer,
        db.ForeignKey("Users.id", ondelete="CASCADE"),
        nullable=False)
    user = db.relationship("Users")
    active = db.Column(db.Boolean(name='active'), default=True, nullable=False)
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)

    @hybrid_property
    def courses_id(self):
        return self.group.courses_id

    @hybrid_property
    def groups_name(self):
        return self.group.name

    __table_args__ = (
        # prevent duplicate user in groups
        db.UniqueConstraint('groups_id', 'users_id', name='_unique_group_and_user'),
        default_table_args
    )


#################################################
# Tags for Posts, each course has their own set of tags
#################################################

class Tags(db.Model):
    __tablename__ = 'Tags'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)
    courses_id = db.Column(
        db.Integer,
        db.ForeignKey('Courses.id', ondelete="CASCADE"),
        nullable=False)
    course = db.relationship("Courses")
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)


#################################################
# Posts - content postings made by users
#################################################

class Posts(db.Model):
    __tablename__ = 'Posts'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    users_id = db.Column(
        db.Integer,
        db.ForeignKey('Users.id', ondelete="CASCADE"),
        nullable=False)
    user = db.relationship("Users", innerjoin=True)
    courses_id = db.Column(
        db.Integer,
        db.ForeignKey('Courses.id', ondelete="CASCADE"),
        nullable=False)
    course = db.relationship("Courses")
    content = db.Column(db.Text)
    files = db.relationship("FilesForPosts", cascade="delete")
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)
    user_avatar = association_proxy('user', 'avatar')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')


#################################################
# Judgements - User's judgements on the answers
#################################################

class Judgements(db.Model):
    __tablename__ = 'Judgements'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True)
    users_id = db.Column(
        db.Integer,
        db.ForeignKey('Users.id', ondelete="CASCADE"),
        nullable=False)
    user = db.relationship("Users")
    answerpairings_id = db.Column(
        db.Integer,
        db.ForeignKey('AnswerPairings.id', ondelete="CASCADE"),
        nullable=False)
    answerpairing = db.relationship("AnswerPairings")
    criteriaandquestions_id = db.Column(
        db.Integer,
        db.ForeignKey('CriteriaAndQuestions.id', ondelete="CASCADE"),
        nullable=False)
    question_criterion = db.relationship("CriteriaAndPostsForQuestions")
    answers_id_winner = db.Column(
        db.Integer,
        db.ForeignKey('Answers.id', ondelete="CASCADE"),
        nullable=False)
    answer_winner = db.relationship("PostsForAnswers")
    comment = db.relationship("PostsForJudgements", uselist=False, backref="judgement")
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)

    @hybrid_property
    def courses_id(self):
        return self.question_criterion.question.post.courses_id

    @classmethod
    def create_judgement(cls, params, answer_pair, user_id):
        judgements = []
        criteria = []
        for judgement_params in params['judgements']:
            criteria.append(judgement_params['question_criterion_id'])
            # need this or hybrid property for courses_id won't work when it checks permissions
            question_criterion = CriteriaAndPostsForQuestions.query. \
                get(judgement_params['question_criterion_id'])
            judgement = Judgements(
                answerpairing=answer_pair, users_id=user_id,
                question_criterion=question_criterion,
                answers_id_winner=judgement_params['answer_id_winner'])
            db.session.add(judgement)
            db.session.commit()
            judgements.append(judgement)

        # increment evaluation count for the answers in the evaluated answer pair
        answers = PostsForAnswers.query. \
            filter(PostsForAnswers.id.in_([answer_pair.answer1.id, answer_pair.answer2.id])).all()
        for ans in answers:
            # use sqlalchemy(sql) increase counter
            ans.round = PostsForAnswers.round + 1
            db.session.add(ans)
        db.session.commit()

        return judgements

    @classmethod
    def calculate_scores(cls, question_id):
        # get all judgements for this question and only load the data we need
        judgements = Judgements.query . \
            options(load_only('answers_id_winner', 'criteriaandquestions_id')) . \
            options(contains_eager(Judgements.answerpairing).load_only('answers_id1', 'answers_id2')) . \
            join(AnswerPairings). \
            filter(AnswerPairings.questions_id == question_id).all()
        question_criteria = CriteriaAndPostsForQuestions.query. \
            with_entities(CriteriaAndPostsForQuestions.id) . \
            filter_by(questions_id=question_id, active=True).all()
        
        criteria_comparison_results = {}
        answer_ids = set()
        for question_criterion in question_criteria:
            comparison_pairs = []
            for judgement in judgements:
                if judgement.criteriaandquestions_id != question_criterion.id:
                    continue
                answers_id1 = judgement.answerpairing.answers_id1
                answers_id2 = judgement.answerpairing.answers_id2
                answer_ids.add(answers_id1)
                answer_ids.add(answers_id2)
                winner = judgement.answers_id_winner
                comparison_pairs.append(
                    ComparisonPair(answers_id1, answers_id2, winning_key=winner)
                )
            
            criteria_comparison_results[question_criterion.id] = acj.algorithms. \
                calculate_scores(comparison_pairs, "acj", current_app.logger)
            
        # load existing scores
        scores = Scores.query.filter(Scores.answers_id.in_(answer_ids)). \
            order_by(Scores.answers_id, Scores.criteriaandquestions_id).all()

        updated_scores = update_scores(scores, criteria_comparison_results)
        db.session.add_all(updated_scores)
        db.session.commit()


def update_scores(scores, criteria_comparison_results):
    new_scores = []
    for question_criterion_id, criteria_comparison_result in criteria_comparison_results.items():
        for answer_id, comparison_results in criteria_comparison_result.items():
            score = None
            for s in scores:
                if s.answers_id == answer_id and s.criteriaandquestions_id == question_criterion_id:
                    score = s
            if not score:
                score = Scores(answers_id=answer_id, criteriaandquestions_id=question_criterion_id)
                new_scores.append(score)
            
            score.rounds = comparison_results.total_rounds
            score.score = comparison_results.score
            score.wins = comparison_results.total_wins
    
    return scores + new_scores
    


class AnswerPairings(db.Model):
    __tablename__ = 'AnswerPairings'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True)
    questions_id = db.Column(
        db.Integer,
        db.ForeignKey('Questions.id', ondelete="CASCADE"),
        nullable=False)
    # question = db.relationship("PostsForQuestions")
    answers_id1 = db.Column(
        db.Integer,
        db.ForeignKey('Answers.id', ondelete="CASCADE"),
        nullable=False)
    answer1 = db.relationship("PostsForAnswers", foreign_keys=[answers_id1])
    answers_id2 = db.Column(
        db.Integer,
        db.ForeignKey('Answers.id', ondelete="CASCADE"),
        nullable=False)
    answer2 = db.relationship("PostsForAnswers", foreign_keys=[answers_id2])
    judgements = db.relationship("Judgements", cascade="delete")
    criteriaandquestions_id = db.Column(
        db.Integer,
        db.ForeignKey('CriteriaAndQuestions.id', ondelete="CASCADE"),
        nullable=True)
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime, default=datetime.datetime.utcnow,
        nullable=False)

    @hybrid_property
    def answer1_win(self):
        return len([j for j in self.judgements if j.answers_id_winner == self.answers_id1])

    @hybrid_property
    def answer2_win(self):
        return len([j for j in self.judgements if j.answers_id_winner == self.answers_id2])


class PostsForAnswersAndPostsForComments(db.Model):
    __tablename__ = 'AnswersAndComments'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    answers_id = db.Column(
        db.Integer,
        db.ForeignKey('Answers.id', ondelete="CASCADE"),
        nullable=False)
    postsforanswers = db.relationship("PostsForAnswers")
    comments_id = db.Column(
        db.Integer,
        db.ForeignKey('Comments.id', ondelete="CASCADE"),
        nullable=False)
    postsforcomments = db.relationship("PostsForComments")
    evaluation = db.Column(db.Boolean(name='evaluation'), default=False, nullable=False)
    selfeval = db.Column(db.Boolean(name='selfeval'), default=False, nullable=False)
    type = db.Column(db.SmallInteger, default=0, nullable=False)

    @hybrid_property
    def courses_id(self):
        """ for backward compat """
        warnings.warn("Deprecated. Use course_id instead!", DeprecationWarning, stacklevel=2)
        return self.postsforcomments.post.courses_id

    @hybrid_property
    def users_id(self):
        """ for backward compat """
        warnings.warn("Deprecated. Use user_id instead!", DeprecationWarning, stacklevel=2)
        return self.user_id

    # those association proxies should be removed after a refactor to hide those association tables
    course_id = association_proxy('postsforcomments', 'course_id')
    content = association_proxy('postsforcomments', 'content')
    files = association_proxy('postsforcomments', 'files')
    created = association_proxy('postsforcomments', 'created')
    user_id = association_proxy('postsforcomments', 'user_id')
    user_avatar = association_proxy('postsforcomments', 'user_avatar')
    user_displayname = association_proxy('postsforcomments', 'user_displayname')
    user_fullname = association_proxy('postsforcomments', 'user_fullname')


class PostsForAnswers(db.Model):
    __tablename__ = 'Answers'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    posts_id = db.Column(
        db.Integer,
        db.ForeignKey('Posts.id', ondelete="CASCADE"),
        nullable=False)
    post = db.relationship("Posts", cascade="delete")
    questions_id = db.Column(
        db.Integer,
        db.ForeignKey('Questions.id', ondelete="CASCADE"),
        nullable=False)
    question = db.relationship("PostsForQuestions")
    comments = db.relationship("PostsForAnswersAndPostsForComments", cascade="delete")
    scores = db.relationship("Scores", cascade="delete", order_by='Scores.criteriaandquestions_id')
    # flagged for instructor review as inappropriate or incomplete
    flagged = db.Column(db.Boolean(name='flagged'), default=False, nullable=False)
    users_id_flagger = db.Column(
        db.Integer,
        db.ForeignKey('Users.id', ondelete="CASCADE"))
    flagger = db.relationship("Users")
    round = db.Column(db.Integer, default=0, nullable=False)

    course_id = association_proxy('post', 'courses_id')
    content = association_proxy('post', 'content')
    files = association_proxy('post', 'files')
    created = association_proxy('post', 'created')
    user_id = association_proxy('post', 'users_id')
    user_avatar = association_proxy('post', 'user_avatar')
    user_displayname = association_proxy('post', 'user_displayname')
    user_fullname = association_proxy('post', 'user_fullname')

    comments_count = column_property(
        select([func.count(PostsForAnswersAndPostsForComments.id)]).
        where(PostsForAnswersAndPostsForComments.answers_id == id),
        deferred=True,
        group='counts'
    )

    private_comments_count = column_property(
        select([func.count(PostsForAnswersAndPostsForComments.id)]).
        where(and_(
            PostsForAnswersAndPostsForComments.answers_id == id,
            or_(PostsForAnswersAndPostsForComments.evaluation != 0,
                PostsForAnswersAndPostsForComments.selfeval != 0,
                PostsForAnswersAndPostsForComments.type == 0)
        )),
        deferred=True,
        group='counts'
    )

    selfeval_count = column_property(
        select([func.count(PostsForAnswersAndPostsForComments.id)]).
        where(PostsForAnswersAndPostsForComments.selfeval != 0),
        deferred=True,
        group='counts'
    )

    @hybrid_property
    def courses_id(self):
        return self.course_id

    @hybrid_property
    def users_id(self):
        return self.user_id

    @hybrid_property
    def public_comments_count(self):
        return self.comments_count - self.private_comments_count


class PostsForComments(db.Model):
    __tablename__ = 'Comments'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    posts_id = db.Column(
        db.Integer,
        db.ForeignKey('Posts.id', ondelete="CASCADE"),
        nullable=False)
    post = db.relationship("Posts")
    answer_assoc = db.relationship("PostsForAnswersAndPostsForComments", uselist=False, cascade='all')

    course_id = association_proxy('post', 'courses_id')
    content = association_proxy('post', 'content')
    files = association_proxy('post', 'files')
    created = association_proxy('post', 'created')
    user_id = association_proxy('post', 'users_id')
    user_avatar = association_proxy('post', 'user_avatar')
    user_displayname = association_proxy('post', 'user_displayname')
    user_fullname = association_proxy('post', 'user_fullname')

    # used by answer comments only
    answer_id = association_proxy('answer_assoc', 'answers_id')
    evaluation = association_proxy('answer_assoc', 'evaluation')
    selfeval = association_proxy('answer_assoc', 'selfeval')
    type = association_proxy('answer_assoc', 'type')


class PostsForQuestionsAndPostsForComments(db.Model):
    __tablename__ = 'QuestionsAndComments'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    questions_id = db.Column(
        db.Integer,
        db.ForeignKey('Questions.id', ondelete="CASCADE"),
        nullable=False)
    postsforquestions = db.relationship("PostsForQuestions")
    comments_id = db.Column(
        db.Integer,
        db.ForeignKey('Comments.id', ondelete="CASCADE"),
        nullable=False)
    postsforcomments = db.relationship("PostsForComments")

    @hybrid_property
    def courses_id(self):
        return self.postsforcomments.post.courses_id

    @hybrid_property
    def users_id(self):
        return self.postsforcomments.post.user.id

    @hybrid_property
    def content(self):
        return self.postsforcomments.post.content


class FilesForPosts(db.Model):
    __tablename__ = 'FilesForPosts'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    posts_id = db.Column(
        db.Integer,
        db.ForeignKey('Posts.id', ondelete="CASCADE"),
        nullable=False)
    post = db.relationship("Posts")
    author_id = db.Column(
        db.Integer,
        db.ForeignKey('Users.id', ondelete="CASCADE"),
        nullable=False)
    author = db.relationship("Users")
    name = db.Column(db.String(255), nullable=False)
    alias = db.Column(db.String(255), nullable=False)


class SelfEvaluationTypes(db.Model):
    __tablename__ = 'SelfEvalTypes'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)

    # constants for the self-evaluation types
    TYPE_COMPARE_NO = "No Comparison with Another Answer"
# TYPE_COMPARE_SIMILAR_ANSWER = "Comparison to a Similarly Scored Answer"
# TYPE_COMPARE_HIGHER_ANSWER = "Comparison to a Higher Scored Answer"


class PostsForQuestionsAndSelfEvaluationTypes(db.Model):
    __tablename__ = 'QuestionsAndSelfEvalTypes'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    questions_id = db.Column(
        db.Integer,
        db.ForeignKey('Questions.id', ondelete="CASCADE"),
        nullable=False)
    selfevaltypes_id = db.Column(
        db.Integer,
        db.ForeignKey('SelfEvalTypes.id', ondelete="CASCADE"),
        nullable=False)
    type = db.relationship("SelfEvaluationTypes")


# each question can have different criteria
class CriteriaAndPostsForQuestions(db.Model):
    __tablename__ = 'CriteriaAndQuestions'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    criteria_id = db.Column(
        db.Integer,
        db.ForeignKey('Criteria.id', ondelete="CASCADE"),
        nullable=False)
    criterion = db.relationship("Criteria")
    questions_id = db.Column(
        db.Integer,
        db.ForeignKey('Questions.id', ondelete="CASCADE"),
        nullable=False)
    question = db.relationship("PostsForQuestions")
    active = db.Column(db.Boolean(name='active'), default=True, nullable=False)
    judgements = db.relationship("Judgements")
    scores = db.relationship("Scores")

    judgement_count = column_property(
        select([func.count(Judgements.id)]).
        where(Judgements.criteriaandquestions_id == id)
    )

    @hybrid_property
    def courses_id(self):
        return self.question.courses_id

    @hybrid_property
    def max_score(self):
        scores = [s.score for s in self.scores]
        return max(scores)


#################################################
# Criteria - What users should judge answers by
#################################################

class Criteria(db.Model):
    __tablename__ = 'Criteria'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    # user who made this criteria
    users_id = db.Column(
        db.Integer,
        db.ForeignKey('Users.id', ondelete="CASCADE"),
        nullable=False)
    user = db.relationship("Users")
    public = db.Column(db.Boolean(name='public'), default=False, nullable=False)
    default = db.Column(db.Boolean(name='default'), default=True, nullable=False)
    question_criteria = db.relationship("CriteriaAndPostsForQuestions")
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)
    created = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False)

    judgement_count = column_property(
        select([func.count(CriteriaAndPostsForQuestions.id)]).
        where(CriteriaAndPostsForQuestions.criteria_id == id)
    )

    @hybrid_property
    def judged(self):
        # return sum(c.judgement_count for c in self.question_criteria) > 0
        return self.judgement_count > 0


#################################################
# Scores - The calculated score of the answer
#################################################

class Scores(db.Model):
    __tablename__ = 'Scores'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    criteriaandquestions_id = db.Column(
        db.Integer,
        db.ForeignKey('CriteriaAndQuestions.id', ondelete="CASCADE"),
        nullable=False)
    question_criterion = db.relationship("CriteriaAndPostsForQuestions")
    answers_id = db.Column(
        db.Integer,
        db.ForeignKey('Answers.id', ondelete="CASCADE"),
        nullable=False)
    answer = db.relationship("PostsForAnswers")
    # number of times this answer has been judged
    rounds = db.Column(db.Integer, default=0)
    # number of times this answer has been picked as the better one
    wins = db.Column(db.Integer, default=0)
    # calculated score based on all previous judgements
    score = db.Column(db.Float, default=0)

    @classmethod
    def __declare_last__(cls):
        s_alias = cls.__table__.alias()
        cls.normalized_score = column_property(
            select([cls.score/func.max(s_alias.c.score)*100]).
            where(s_alias.c.criteriaandquestions_id == cls.criteriaandquestions_id)
        )

    __table_args__ = (
        db.UniqueConstraint('answers_id', 'criteriaandquestions_id', name='_unique_user_and_course'),
        default_table_args
    )


# TODO: this model could be merged into Judgements (one to one relationship)
class PostsForJudgements(db.Model):
    __tablename__ = 'PostsForJudgements'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    comments_id = db.Column(
        db.Integer,
        db.ForeignKey('Comments.id', ondelete="CASCADE"),
        nullable=False)
    postsforcomments = db.relationship("PostsForComments")
    judgements_id = db.Column(
        db.Integer,
        db.ForeignKey('Judgements.id', ondelete="CASCADE"),
        nullable=False)
    # judgement = db.relationship("Judgements")
    selfeval = db.Column(db.Boolean(name='selfeval'), default=False, nullable=False)

    course_id = association_proxy('postsforcomments', 'course_id')
    content = association_proxy('postsforcomments', 'content')
    files = association_proxy('postsforcomments', 'files')
    created = association_proxy('postsforcomments', 'created')
    user_id = association_proxy('postsforcomments', 'user_id')
    user_avatar = association_proxy('postsforcomments', 'user_avatar')
    user_displayname = association_proxy('postsforcomments', 'user_displayname')
    user_fullname = association_proxy('postsforcomments', 'user_fullname')

    @hybrid_property
    def courses_id(self):
        return self.postsforcomments.post.courses_id


class PostsForQuestions(db.Model):
    __tablename__ = 'Questions'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    posts_id = db.Column(
        db.Integer,
        db.ForeignKey('Posts.id', ondelete="CASCADE"),
        nullable=False)
    post = db.relationship("Posts", cascade="delete")
    title = db.Column(db.String(255))
    _answers = db.relationship("PostsForAnswers", cascade="delete")
    comments = db.relationship("PostsForQuestionsAndPostsForComments", cascade="delete", lazy="dynamic")
    criteria = db.relationship(
        "CriteriaAndPostsForQuestions", cascade="delete",
        primaryjoin="and_(PostsForQuestions.id==CriteriaAndPostsForQuestions.questions_id, "
                    "CriteriaAndPostsForQuestions.active)",
        order_by="CriteriaAndPostsForQuestions.id")
    answerpairing = db.relationship("AnswerPairings", cascade="delete", backref="question")
    answer_start = db.Column(db.DateTime(timezone=True))
    answer_end = db.Column(db.DateTime(timezone=True))
    judge_start = db.Column(db.DateTime(timezone=True), nullable=True)
    judge_end = db.Column(db.DateTime(timezone=True), nullable=True)
    num_judgement_req = db.Column(db.Integer, nullable=False)
    can_reply = db.Column(db.Boolean(name='can_reply'), default=False, nullable=False)
    selfevaltype = db.relationship("PostsForQuestionsAndSelfEvaluationTypes", cascade="delete")
    modified = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False)

    answers_count = column_property(
        select([func.count(PostsForAnswers.id)]).
        where(PostsForAnswers.questions_id == id),
        deferred=True,
        group="counts"
    )

    comments_count = column_property(
        select([func.count(PostsForQuestionsAndPostsForComments.id)]).
        where(PostsForQuestionsAndPostsForComments.questions_id == id),
        deferred=True,
        group="counts"
    )

    criteria_count = column_property(
        select([func.count(CriteriaAndPostsForQuestions.id)]).
        where(and_(CriteriaAndPostsForQuestions.questions_id == id, CriteriaAndPostsForQuestions.active)),
        deferred=True,
        group="counts"
    )

    judged = column_property(
        select([func.count(AnswerPairings.id) > 0]).
        where(AnswerPairings.questions_id == id),
        deferred=True,
        group="counts"
    )

    judgement_count = column_property(
        select([func.count(Judgements.id)]).
        where(and_(
            Judgements.criteriaandquestions_id == CriteriaAndPostsForQuestions.id,
            CriteriaAndPostsForQuestions.questions_id == id)),
        deferred=True,
        group="counts"
    )

    _selfeval_count = column_property(
        select([func.count(PostsForAnswersAndPostsForComments.id)]).
        where(and_(
            PostsForAnswersAndPostsForComments.selfeval,
            PostsForAnswersAndPostsForComments.answers_id == PostsForAnswers.id,
            PostsForAnswers.questions_id == id)),
        deferred=True,
        group="counts"
    )

    @hybrid_property
    def courses_id(self):
        return self.post.courses_id

    @hybrid_property
    def answers(self):
        return sorted(self._answers, key=lambda answer: answer.post.created, reverse=True)

    @hybrid_property
    def available(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        return answer_start <= now

    @hybrid_property
    def answer_period(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        return answer_start <= now < answer_end

    @hybrid_property
    def answer_grace(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        grace = self.answer_end.replace(tzinfo=pytz.utc) + datetime.timedelta(seconds=60)  # add 60 seconds
        answer_start = self.answer_start.replace(tzinfo=pytz.utc)
        return answer_start <= now < grace

    @hybrid_property
    def judging_period(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        if not self.judge_start:
            return now >= answer_end
        else:
            return self.judge_start.replace(tzinfo=pytz.utc) <= now < self.judge_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def after_judging(self):
        now = dateutil.parser.parse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
        answer_end = self.answer_end.replace(tzinfo=pytz.utc)
        # judgement period not set
        if not self.judge_start:
            return now >= answer_end
        # judgement period is set
        else:
            return now >= self.judge_end.replace(tzinfo=pytz.utc)

    @hybrid_property
    def selfevaltype_id(self):
        # assume max one selfeval type per question for now
        eval_type = None
        if len(self.selfevaltype):
            eval_type = self.selfevaltype[0].selfevaltypes_id
        return eval_type

    @hybrid_property
    def evaluation_count(self):
        evaluation_count = self.judgement_count / self.criteria_count if self.criteria_count else 0
        return evaluation_count + self._selfeval_count

    def __repr__(self):
        if self.id:
            return "Question " + str(self.id)
        else:
            return "Question"


# each course can have different criteria
class CriteriaAndCourses(db.Model):
    __tablename__ = 'CriteriaAndCourses'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    criteria_id = db.Column(
        db.Integer,
        db.ForeignKey('Criteria.id', ondelete="CASCADE"),
        nullable=False)
    criterion = db.relationship("Criteria", backref=backref('course_assoc', uselist=False))
    courses_id = db.Column(
        db.Integer,
        db.ForeignKey('Courses.id', ondelete="CASCADE"),
        nullable=False)
    course = db.relationship("Courses")
    active = db.Column(db.Boolean(name='active'), default=True, nullable=False)

    in_question_count = column_property(
        select([func.count(CriteriaAndPostsForQuestions.id)]).
        where(and_(
            criteria_id == CriteriaAndPostsForQuestions.criteria_id,
            CriteriaAndPostsForQuestions.questions_id == PostsForQuestions.id,
            PostsForQuestions.posts_id == Posts.id,
            Posts.courses_id == courses_id
        ))
    )

    @hybrid_property
    def in_question(self):
        # criteria = [c for c in self.criterion.question_criteria if c.courses_id==self.courses_id]
        # return len(criteria) > 0
        return self.in_question_count > 0


class LTIInfo(db.Model):
    __tablename__ = 'LTIInfo'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True)
    LTIid = db.Column(db.String(100))
    LTIURL = db.Column(db.String(100))
    courses_id = db.Column(
        db.Integer,
        db.ForeignKey('Courses.id', ondelete="CASCADE"),
        nullable=False)
    course = db.relationship("Courses")


class Activities(db.Model):
    __tablename__ = 'Activities'
    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True)
    users_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=True)
    user = db.relationship("Users")
    courses_id = db.Column(
        db.Integer,
        db.ForeignKey('Courses.id', ondelete="CASCADE"),
        nullable=True)
    course = db.relationship("Courses")
    timestamp = db.Column(
        db.TIMESTAMP, default=func.current_timestamp(),
        nullable=False)
    event = db.Column(db.String(50))
    data = db.Column(db.Text)
    status = db.Column(db.String(20))
    message = db.Column(db.Text)
    session_id = db.Column(db.String(100))