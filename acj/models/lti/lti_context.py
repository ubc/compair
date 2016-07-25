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
    def is_linked_to_course(self):
        return self.acj_course_id != None

    @classmethod
    def get_by_lti_consumer_id_and_context_id(cls, lti_consumer_id, context_id):
        lti_context = LTIContext.query \
            .filter_by(
                lti_consumer_id=lti_consumer_id,
                context_id=context_id
            ) \
            .one()

        return lti_context

    @classmethod
    def get_by_launch_request(cls, lti_consumer, launch_request):
        lti_context = LTIContext.get_by_lti_consumer_id_and_context_id(
            lti_consumer.id, launch_request['context_id'])

        if lti_context == None:
            lti_context = LTIContext(
                lti_consumer_id=lti_consumer.id,
                context_id=launch_request['context_id']
            )
        lti_context.context_type = launch_request['context_type']
        lti_context.context_title = launch_request['context_title']

        # create/update if needed
        if lti_context.session.is_modified(lti_context, include_collections=False):
            db.session.add(lti_context)
            db.session.commit()

        return lti_context

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        db.UniqueConstraint('lti_consumer_id', 'context_id', name='_unique_lti_consumer_and_lti_context'),
        DefaultTableMixin.default_table_args
    )