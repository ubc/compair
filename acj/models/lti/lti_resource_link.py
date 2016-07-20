# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

class LTIResourceLink(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_resource_link'

    # table columns
    lti_consumer_id = db.Column(db.Integer, db.ForeignKey("lti_consumer.id", ondelete="CASCADE"),
        nullable=False)
    resource_link_id = db.Column(db.String(255), nullable=False)
    resource_link_title = db.Column(db.String(255), nullable=True)
    launch_presentation_return_url = db.Column(db.Text, nullable=True)
    ext_ims_lis_memberships_id = db.Column(db.String(255), nullable=True)
    ext_ims_lis_memberships_url = db.Column(db.Text, nullable=True)
    custom_param_assignment_id = db.Column(db.String(255), nullable=True)
    acj_assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=True)

    # relationships
    # acj_assignment via Assignment Model


    # hyprid and other functions
    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_consumer_id', 'resource_link_id', name='_unique_lti_consumer_and_lti_resource_link'),
        DefaultTableMixin.default_table_args
    )