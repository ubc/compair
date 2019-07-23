import hashlib

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_, exists
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property

from . import *

from compair.core import db

class Group(DefaultTableMixin, UUIDMixin, ActiveMixin, WriteTrackingMixin):
    # table columns
    course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"),
        nullable=False)
    name = db.Column(db.String(255), nullable=True)

    # relationships
    # course though Course Model
    user_courses = db.relationship("UserCourse", back_populates="group", lazy="dynamic")
    answers = db.relationship("Answer", backref="group")

    # hybrid and other functions
    course_uuid = association_proxy('course', 'uuid')
    group_uuid = association_proxy('group', 'uuid')

    @hybrid_property
    def avatar(self):
        """
        According to gravatar's hash specs
            1.Trim leading and trailing whitespace from an email address
            2.Force all characters to lower-case
            3.md5 hash the final string
        """
        hash_input = self.uuid + ".group.@compair" if self.uuid else None
        m = hashlib.md5()
        m.update(hash_input.strip().lower().encode('utf-8'))
        return m.hexdigest()

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Group Unavailable"
        if not message:
            message = "Sorry, this group was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def get_active_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Group Unavailable"
        if not message:
            message = "Sorry, this group was deleted or is no longer accessible."
        return super(cls, cls).get_active_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

        cls.group_answer_exists = column_property(
            exists([1]).
            where(and_(
                Answer.group_id == cls.id,
                Answer.practice == False,
                Answer.active == True,
                Answer.draft == False
            )),
            deferred=True,
            group="answer_associates"
        )