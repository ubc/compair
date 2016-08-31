import hashlib
from flask import current_app
from datetime import datetime
import time

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType

from flask.ext.login import UserMixin
from . import *

from acj.core import db
from acj import security

def hash_password(password, is_admin=False):
    category = None
    if is_admin:
        # enables more rounds for admin passwords
        category = "admin"
    pwd_context = getattr(security, current_app.config['PASSLIB_CONTEXT'])
    return pwd_context.encrypt(password, category=category)

# Flask-Login requires the user class to have some methods, the easiest way
# to get those methods is to inherit from the UserMixin class.
class User(DefaultTableMixin, WriteTrackingMixin, UserMixin):
    # table columns
    username = db.Column(db.String(255), unique=True, nullable=False)
    _password = db.Column(db.String(255), unique=False, nullable=False)
    system_role = db.Column(EnumType(SystemRole, name="system_role"), nullable=False, index=True)
    displayname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(254))  # email addresses are max 254 characters
    firstname = db.Column(db.String(255))
    lastname = db.Column(db.String(255))
    student_number = db.Column(db.String(50), unique=True, nullable=True)
    last_online = db.Column(db.DateTime)

    # relationships

    # user many-to-many course with association user_course
    user_courses = db.relationship("UserCourse",
        foreign_keys='UserCourse.user_id',
        back_populates="user")
    assignments = db.relationship("Assignment",
        foreign_keys='Assignment.user_id',
        backref="user", lazy='dynamic')
    assignment_comments = db.relationship("AssignmentComment",
        foreign_keys='AssignmentComment.user_id',
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
    comparisons = db.relationship("Comparison",
        foreign_keys='Comparison.user_id',
        backref="user", lazy='dynamic')
    third_party_auths = db.relationship("ThirdPartyUser",
        foreign_keys='ThirdPartyUser.user_id',
        backref="user", lazy='dynamic')

    # third party authentification
    lti_user_links = db.relationship("LTIUser",
        foreign_keys='LTIUser.acj_user_id',
        backref="acj_user", lazy='dynamic')

    # hyprid and other functions

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

    @hybrid_property
    def avatar(self):
        """
        According to gravatar's hash specs
            1.Trim leading and trailing whitespace from an email address
            2.Force all characters to lower-case
            3.md5 hash the final string
        Defaults to a hash of the user's username if no email is available
        """
        hash_input = None
        if self.system_role == SystemRole.student:
            hash_input = str(self.id) + "@compair"
        else:
            hash_input = self.email if self.email else self.username

        m = hashlib.md5()
        m.update(hash_input.strip().lower().encode('utf-8'))
        return m.hexdigest()

    def verify_password(self, password):
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
        key = str(self.id) + str(time.time())
        return hashlib.md5(key.encode('UTF-8')).hexdigest()

    # This could be used for token based authentication
    # def generate_auth_token(self, expiration=60):
    #     s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    #     return s.dumps({'id': self.id})

    def __repr__(self):
        if self.username:
            return self.username
        else:
            return "User"

    def get_course_role(self, course_id):
        """ Return user's course role by course id """

        for user_course in self.user_courses:
            if user_course.course_id == course_id:
                return user_course.course_role

        return None

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

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