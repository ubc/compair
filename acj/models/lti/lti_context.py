# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class LTIContext(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_context'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    context_id = db.Column(db.String(255), nullable=False)
    context_type = db.Column(db.String(255), nullable=True)
    context_title = db.Column(db.String(255), nullable=True)
    acj_course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"),
        nullable=True)

    # relationships
    # acj_course via Course Model

    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        db.UniqueConstraint('lti_consumer_id', 'context_id', name='_unique_lti_consumer_and_lti_context'),
        DefaultTableMixin.default_table_args
    )