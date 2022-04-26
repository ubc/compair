import hashlib
from flask import current_app
from datetime import datetime
import time
from six import text_type

# sqlalchemy
from sqlalchemy.orm import column_property, synonym, joinedload
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from flask_login import UserMixin, current_user
from . import *

from compair.core import db
from compair import security

def hash_password(password, is_admin=False):
    category = None
    if is_admin:
        # enables more rounds for admin passwords
        category = "admin"
    pwd_context = getattr(security, current_app.config['PASSLIB_CONTEXT'])
    return pwd_context.encrypt(password, category=category)

# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class User(DefaultTableMixin, UUIDMixin, WriteTrackingMixin, UserMixin):
    __tablename__ = 'user'

    # table columns
    global_unique_identifier = db.Column(db.String(191), nullable=True) #should be treated as write once and only once
    username = db.Column(db.String(191), unique=True, nullable=True)
    _password = db.Column(db.String(255), unique=False, nullable=True)
    system_role = db.Column(Enum(SystemRole), nullable=False, index=True)
    displayname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(254), nullable=True)  # email addresses are max 254 characters
    firstname = db.Column(db.String(255), nullable=True)
    lastname = db.Column(db.String(255), nullable=True)
    student_number = db.Column(db.String(50), unique=True, nullable=True)
    last_online = db.Column(db.DateTime)
    email_notification_method = db.Column(Enum(EmailNotificationMethod),
        nullable=False, default=EmailNotificationMethod.enable, index=True)

    # relationships

    # user many-to-many course with association user_course
    user_courses = db.relationship("UserCourse",
        foreign_keys='UserCourse.user_id',
        back_populates="user")
    course_grades = db.relationship("CourseGrade",
        foreign_keys='CourseGrade.user_id',
        backref="user", lazy='dynamic')
    assignments = db.relationship("Assignment",
        foreign_keys='Assignment.user_id',
        backref="user", lazy='dynamic')
    assignment_grades = db.relationship("AssignmentGrade",
        foreign_keys='AssignmentGrade.user_id',
        backref="user", lazy='dynamic')
    answers = db.relationship("Answer",
        foreign_keys='Answer.user_id',
        backref="user", lazy='dynamic')
    answer_comments = db.relationship("AnswerComment",
        foreign_keys='AnswerComment.user_id',
        backref="user", lazy='dynamic')
    criteria = db.relationship("Criterion",
        foreign_keys='Criterion.user_id',
        backref="user", lazy='dynamic')
    files = db.relationship("File",
        foreign_keys='File.user_id',
        backref="user", lazy='dynamic')
    kaltura_files = db.relationship("KalturaMedia",
        foreign_keys='KalturaMedia.user_id',
        backref="user", lazy='dynamic')
    comparisons = db.relationship("Comparison",
        foreign_keys='Comparison.user_id',
        backref="user", lazy='dynamic')
    # third party authentification
    third_party_auths = db.relationship("ThirdPartyUser",
        foreign_keys='ThirdPartyUser.user_id',
        backref="user", lazy='dynamic')
    # lti authentification
    lti_user_links = db.relationship("LTIUser",
        foreign_keys='LTIUser.compair_user_id',
        backref="compair_user", lazy='dynamic')

    # hybrid and other functions
    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = hash_password(password) if password != None else None

    @hybrid_property
    def fullname(self):
        if self.firstname and self.lastname:
            return '%s %s' % (self.firstname, self.lastname)
        elif self.firstname:  # only first name provided
            return self.firstname
        elif self.lastname:  # only last name provided
            return self.lastname
        elif self.displayname:
            return self.displayname
        else:
            return None

    @hybrid_property
    def fullname_sortable(self):
        if self.firstname and self.lastname and self.system_role == SystemRole.student and self.student_number:
            return '%s, %s (%s)' % (self.lastname, self.firstname, self.student_number)
        elif self.firstname and self.lastname:
            return '%s, %s' % (self.lastname, self.firstname)
        elif self.firstname:  # only first name provided
            return self.firstname
        elif self.lastname:  # only last name provided
            return self.lastname
        elif self.displayname:
            return self.displayname
        else:
            return None

    @hybrid_property
    def avatar(self):
        """
        According to gravatar's hash specs
            1.Trim leading and trailing whitespace from an email address
            2.Force all characters to lower-case
            3.md5 hash the final string
        """
        hash_input = None
        if self.system_role != SystemRole.student and self.email:
            hash_input = self.email
        elif self.uuid:
            hash_input = self.uuid + "@compair"

        m = hashlib.md5()
        m.update(hash_input.strip().lower().encode('utf-8'))
        return m.hexdigest()

    @hybrid_property
    def uses_compair_login(self):
        # third party auth users may have their username not set
        return self.username != None and current_app.config['APP_LOGIN_ENABLED']

    @hybrid_property
    def lti_linked(self):
        return self.lti_user_link_count > 0

    @hybrid_property
    def has_third_party_auth(self):
        return self.third_party_auth_count > 0

    def verify_password(self, password):
        if self.password == None or not current_app.config['APP_LOGIN_ENABLED']:
            return False
        pwd_context = getattr(security, current_app.config['PASSLIB_CONTEXT'])
        return pwd_context.verify(password, self.password)

    def update_last_online(self):
        self.last_online = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def generate_session_token(self):
        """
        Generate a session token that identifies the user login session. Since the flask
        wll generate the same session _id for the same IP and browser agent combination,
        it is hard to distinguish the users by session from the activity log
        """
        key = str(self.id) + '-' + str(time.time())
        return hashlib.md5(key.encode('UTF-8')).hexdigest()

    # This could be used for token based authentication
    # def generate_auth_token(self, expiration=60):
    #     s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    #     return s.dumps({'id': self.id})

    @classmethod
    def get_user_course_role(cls, user_id, course_id):
        from . import UserCourse
        user_course = UserCourse.query \
            .filter_by(
                course_id=course_id,
                user_id=user_id
            ) \
            .one_or_none()
        return user_course.course_role if user_course else None

    def get_course_role(self, course_id):
        """ Return user's course role by course id """

        for user_course in self.user_courses:
            if user_course.course_id == course_id:
                return user_course.course_role

        return None

    @classmethod
    def get_user_course_group(cls, user_id, course_id):
        from . import UserCourse
        user_course = UserCourse.query \
            .options(joinedload('group')) \
            .filter_by(
                course_id=course_id,
                user_id=user_id
            ) \
            .one_or_none()

        return user_course.group if user_course else None

    def get_course_group(self, course_id):
        """ Return user's course group by course id """

        for user_course in self.user_courses:
            if user_course.course_id == course_id:
                return user_course.group

        return None

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "User Unavailable"
        if not message:
            message = "Sorry, this user was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "User Unavailable"
        if not message:
            message = "Sorry, this user was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        from .lti_models import LTIUser
        from . import ThirdPartyUser
        super(cls, cls).__declare_last__()

        cls.third_party_auth_count = column_property(
            select([func.count(ThirdPartyUser.id)]).
            where(ThirdPartyUser.user_id == cls.id).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )

        cls.lti_user_link_count = column_property(
            select([func.count(LTIUser.id)]).
            where(LTIUser.compair_user_id == cls.id).
            scalar_subquery(),
            deferred=True,
            group="counts"
        )

    __table_args__ = (
        # prevent duplicate user in course
        db.UniqueConstraint('global_unique_identifier', name='_unique_global_unique_identifier'),
        DefaultTableMixin.default_table_args
    )
