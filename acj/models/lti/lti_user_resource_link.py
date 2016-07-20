# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class LTIUserResourceLink(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_user_resource_link'

    # table columns
    lti_resource_link_id = db.Column(db.Integer, db.ForeignKey("lti_resource_link.id", ondelete="CASCADE"),
        nullable=False)
    lti_user_id = db.Column(db.Integer, db.ForeignKey("lti_user.id", ondelete="CASCADE"),
        nullable=False)
    roles = db.Column(db.String(255), nullable=True)
    lis_result_sourcedid = db.Column(db.String(255), nullable=True)
    acj_user_course_id = db.Column(db.Integer, db.ForeignKey("user_course.id", ondelete="CASCADE"),
        nullable=True)

    # relationships
    # acj_user_course via UserCourse Model

    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_resource_link_id', 'lti_user_id', name='_unique_lti_resource_link_and_lti_user'),
        DefaultTableMixin.default_table_args
    )