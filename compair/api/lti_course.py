from flask import Blueprint, session as sess
from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask_login import login_required, current_user
from flask_restful import Resource, marshal, reqparse, marshal_with
from sqlalchemy import exc, or_, and_, desc, asc
from six import text_type

from . import dataformat
from compair.core import event, db, abort
from compair.authorization import require
from compair.models import User, Course, LTIConsumer, LTIContext, LTIMembership, \
    LTIResourceLink, LTIUser, LTIUserResourceLink, LTINonce
from compair.models.lti_models import MembershipNoValidContextsException, \
    MembershipNoResultsException, MembershipInvalidRequestException
from .util import new_restful_api, get_model_changes, pagination_parser
from compair.tasks import update_lti_course_membership

lti_course_api = Blueprint('lti_course_api', __name__)
api = new_restful_api(lti_course_api)

context_list_parser = pagination_parser.copy()
context_list_parser.add_argument('orderBy', type=str, required=False, default=None)
context_list_parser.add_argument('reverse', type=bool, default=False)
context_list_parser.add_argument('search', required=False, default=None)

# events
on_lti_course_links_get = event.signal('LTI_CONTEXT_COURSE_LINKS')
on_lti_course_link_create = event.signal('LTI_CONTEXT_COURSE_LINKED')
on_lti_course_unlink = event.signal('LTI_CONTEXT_COURSE_UNLINKED')
on_lti_course_membership_update = event.signal('LTI_CONTEXT_COURSE_MEMBERSHIP_UPDATE')
on_lti_course_membership_status_get = event.signal('LTI_CONTEXT_COURSE_MEMBERSHIP_STATUS_GET')

# /context
class LTICourseLinksRootAPI(Resource):
    @login_required
    def get(self):
        require(READ, LTIContext,
            title="Course Links Unavailable",
            message="Sorry, your system role does not allow you to view LTI course links.")

        params = context_list_parser.parse_args()

        query = LTIContext.query \
            .join("lti_consumer") \
            .join("compair_course") \
            .add_columns(LTIConsumer.oauth_consumer_key, Course.name)

        if params['orderBy']:
            if params['reverse']:
                query = query.order_by(desc(params['orderBy']))
            else:
                query = query.order_by(asc(params['orderBy']))
        query = query.order_by(LTIContext.created)

        if params['search']:
            # match each word of search
            for word in params['search'].strip().split(' '):
                if word != '':
                    search = '%'+word+'%'
                    query = query.filter(or_(
                        # course search
                        Course.name.like(search),
                        # consumer search
                        LTIConsumer.oauth_consumer_key.like(search),
                        # context search
                        LTIContext.context_id.like(search),
                        LTIContext.context_title.like(search)
                    ))

        page = query.paginate(params['page'], params['perPage'])

        # unwrap link info
        lti_course_links = []
        for (_course_link, _oauth_consumer_key, _compair_course_name) in page.items:
            _course_link.oauth_consumer_key = _oauth_consumer_key
            _course_link.compair_course_name = _compair_course_name

            lti_course_links.append(_course_link)

        on_lti_course_links_get.send(
            self,
            event_name=on_lti_course_links_get.name,
            user=current_user)

        return {'objects': marshal(lti_course_links, dataformat.get_lti_course_links()),
            "page": page.page, "pages": page.pages, "total": page.total, "per_page": page.per_page}

api.add_resource(LTICourseLinksRootAPI, '/context')

# /:course_uuid/context
class LTICourseLinkingAPI(Resource):
    @login_required
    def post(self, course_uuid):
        """
        link current session's lti context with a course
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, course,
            title="Course Not Linked",
            message="Sorry, you do not have permission to link this course since you are not enrolled as an instructor in the course.")

        if not sess.get('LTI'):
            abort(400, title="Course Not Linked",
                message="Sorry, your LTI session has expired. Please log in via LTI and try linking again.")

        if not sess.get('lti_context'):
            abort(400, title="Course Not Linked",
                message="Sorry, your LTI link settings have no course context. Please edit your LTI link settings and try linking again.")

        lti_context = LTIContext.query.get_or_404(sess.get('lti_context'))
        lti_context.compair_course_id = course.id
        db.session.commit()

        # automatically fetch membership if enabled for context
        if lti_context.membership_enabled:
            update_lti_course_membership.delay(course.id)

        on_lti_course_link_create.send(
            self,
            event_name=on_lti_course_link_create.name,
            user=current_user,
            data={ 'course_id': course.id, 'lti_context_id': lti_context.id })

        return { 'success': True }

api.add_resource(LTICourseLinkingAPI, '/<course_uuid>/context')

# /:course_uuid/context/:lti_context_uuid
class LTICourseUnlinkAPI(Resource):
    @login_required
    def delete(self, course_uuid, lti_context_uuid):
        """
        unlink lti context from course
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        lti_context = LTIContext.get_by_uuid_or_404(lti_context_uuid)
        require(DELETE, lti_context,
            title="Course Not Unlinked",
            message="Sorry, your system role does not allow you to unlink LTI courses.")

        if lti_context.compair_course_id != course.id:
            abort(400, title="Course Not Unlinked", message="Sorry, The LTI context is already not linked to the course.")

        lti_context.compair_course_id = None
        db.session.commit()

        # automatically refresh membership if it was enabled for the removed context
        if lti_context.membership_enabled:
            update_lti_course_membership.delay(course.id)

        on_lti_course_unlink.send(
            self,
            event_name=on_lti_course_unlink.name,
            user=current_user,
            data={ 'course_id': course.id, 'lti_context_id': lti_context.id })

        return { 'success': True }

api.add_resource(LTICourseUnlinkAPI, '/<course_uuid>/context/<lti_context_uuid>')

# /:course_uuid/membership
class LTICourseMembershipAPI(Resource):
    @login_required
    def post(self, course_uuid):
        """
        refresh the course membership if able
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, course,
            title="Membership Not Updated",
            message="Sorry, your role in this course does not allow you to update membership.")

        if not course.lti_linked:
            abort(400, title="Membership Not Updated",
                message="Sorry, your LTI link settings have no course context. Please edit your LTI link settings and try linking again.")

        try:
            LTIMembership.update_membership_for_course(course)
        except MembershipNoValidContextsException as err:
            abort(400, title="Membership Not Updated",
                message="The LTI link does not support the membership extension. Please edit your LTI link settings or contact your system administrator and try again.")
        except MembershipNoResultsException as err:
            abort(400, title="Membership Not Updated",
                message="The membership service did not return any users. Please check your LTI course and try again.")
        except MembershipInvalidRequestException as err:
            abort(400, title="Membership Not Updated",
                message="The membership request was invalid. Please relaunch the LTI link and try again.")

        on_lti_course_membership_update.send(
            self,
            event_name=on_lti_course_membership_update.name,
            user=current_user,
            data={ 'course_id': course.id })

        return { 'imported': True }

api.add_resource(LTICourseMembershipAPI, '/<course_uuid>/membership')


# /:course_uuid/membership/status
class LTICourseMembershipStatusAPI(Resource):
    @login_required
    def get(self, course_uuid):
        """
        refresh the course membership if able
        """
        course = Course.get_active_by_uuid_or_404(course_uuid)
        require(EDIT, course,
            title="Membership Status Unavailable",
            message="Sorry, your role in this course does not allow you to view LTI membership status.")

        if not course.lti_linked:
            abort(400, title="Membership Status Unavailable",
                message="The course is not linked to an LTI context yet. Launch an LTI link to link this course first, then check the status.")

        valid_membership_contexts = [
            lti_context for lti_context in course.lti_contexts \
            if lti_context.membership_enabled
        ]

        pending = 0
        enabled = len(valid_membership_contexts) > 0
        if enabled:
            lti_context_ids = [lti_context.id for lti_context in valid_membership_contexts]

            pending = LTIMembership.query \
                .join(LTIUser) \
                .filter(and_(
                    LTIUser.compair_user_id == None,
                    LTIMembership.lti_context_id.in_(lti_context_ids)
                )) \
                .count()

        status = {
            'enabled': enabled,
            'pending': pending
        }

        on_lti_course_membership_status_get.send(
            self,
            event_name=on_lti_course_membership_status_get.name,
            user=current_user,
            data={ 'course_id': course.id })

        return { 'status': status }

api.add_resource(LTICourseMembershipStatusAPI, '/<course_uuid>/membership/status')
