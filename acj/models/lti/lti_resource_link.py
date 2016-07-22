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
    def is_linked_to_assignment(self):
        return self.acj_assignment_id != None

    def _update_link_to_acj_assignment(self):
        from acj.models import Assignment

        if self.custom_param_assignment_id:
            assignment_id = None
            try:
                assignment_id = int(self.custom_param_assignment_id)
            except ValueError:
                return self
                # do nothing
            # check if int conversion worked
            if assignment_id:
                # check if assignment exists
                assignment = Assignment.get(assignment_id)
                if assignment:
                    self.acj_assignment_id = assignment.id
                    return self

        self.acj_assignment_id = None
        return self

    @classmethod
    def get_by_lti_consumer_id_and_resource_link_id(cls, lti_consumer_id, resource_link_id):
        lti_resource_link = LTIContext.query \
            .filter_by(
                lti_consumer_id=lti_consumer_id,
                resource_link_id=resource_link_id
            ) \
            .one()

        return lti_resource_link

    @classmethod
    def get_by_launch_request(cls, lti_consumer, launch_request):
        lti_resource_link = LTIResourceLink.get_by_lti_consumer_id_and_resource_link_id(
            lti_consumer.id, launch_request['resource_link_id'])

        if lti_resource_link == None:
            lti_resource_link = LTIResourceLink(
                lti_consumer_id=lti_consumer.id,
                lti_resource_link=launch_request['lti_resource_link']
            )
        original_custom_param_assignment_id = lti_resource_link.custom_param_assignment_id

        lti_resource_link.resource_link_title = launch_request['resource_link_title']
        lti_resource_link.launch_presentation_return_url = launch_request['launch_presentation_return_url']
        lti_resource_link.ext_ims_lis_memberships_id = launch_request['ext_ims_lis_memberships_id']
        lti_resource_link.ext_ims_lis_memberships_url = launch_request['ext_ims_lis_memberships_url']
        lti_resource_link.custom_param_assignment_id = launch_request['custom_assignment']

        if original_custom_param_assignment_id != launch_request['custom_assignment']:
            lti_resource_link._update_link_to_acj_assignment()

        # create/update if needed
        if lti_resource_link.session.is_modified(lti_resource_link, include_collections=False):
            db.session.add(lti_resource_link)
            db.session.commit()

        return lti_resource_link

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_consumer_id', 'resource_link_id', name='_unique_lti_consumer_and_lti_resource_link'),
        DefaultTableMixin.default_table_args
    )