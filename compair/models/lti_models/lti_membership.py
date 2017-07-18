from six import text_type

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_enum34 import EnumType
from flask_login import current_user
from flask import current_app

from . import *

from compair.core import db

from oauthlib.oauth1 import SIGNATURE_TYPE_BODY, SIGNATURE_TYPE_AUTH_HEADER, SIGNATURE_HMAC
from .helpers import LTIMemerbshipServiceOauthClient

from requests_oauthlib import OAuth1
from lti.utils import parse_qs
import requests
from xml.etree import ElementTree

class LTIMembership(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_membership'

    # table columns
    lti_context_id = db.Column(db.Integer, db.ForeignKey("lti_context.id", ondelete="CASCADE"),
        nullable=False)
    lti_user_id = db.Column(db.Integer, db.ForeignKey("lti_user.id", ondelete="CASCADE"),
        nullable=False)
    roles = db.Column(db.String(255), nullable=True)
    lis_result_sourcedid = db.Column(db.String(255), nullable=True)
    course_role = db.Column(EnumType(CourseRole, name="course_role"),
        nullable=False)

    compair_course_id = association_proxy('lti_context', 'compair_course_id')
    compair_user_id = association_proxy('lti_user', 'compair_user_id')

    # relationships
    # lti_conext via LTIContext Model
    # lti_user via LTIUser Model


    # hyprid and other functions
    @classmethod
    def update_membership_for_course(cls, course):
        from . import MembershipNoValidContextsException

        valid_membership_contexts = [
            lti_context for lti_context in course.lti_contexts if lti_context.membership_enabled
        ]

        if len(valid_membership_contexts) == 0:
            raise MembershipNoValidContextsException

        lti_members = []
        for lti_context in valid_membership_contexts:
            members = LTIMembership._get_membership(lti_context)
            lti_members += LTIMembership._update_membership_for_context(lti_context, members)

        LTIMembership._update_enrollment_for_course(course.id, lti_members)

    @classmethod
    def _update_membership_for_context(cls, lti_context, members):
        from compair.models import LTIUser, SystemRole, CourseRole

        # remove old membership rows
        LTIMembership.query \
            .filter_by(
                lti_context_id=lti_context.id
            ) \
            .delete()

        # retreive existing lti_user rows
        user_ids = []
        for member in members:
            user_ids.append(member['user_id'])

        existing_lti_users = LTIUser.query \
            .filter(and_(
                LTIUser.lti_consumer_id == lti_context.lti_consumer_id,
                LTIUser.user_id.in_(user_ids)
            )) \
            .all()

        new_lti_users = []
        lti_memberships = []
        for member in members:
            # get lti user if exists
            lti_user = next(
                (lti_user for lti_user in existing_lti_users if lti_user.user_id == member.get('user_id')),
                None
            )
            roles = member.get('roles')
            has_instructor_role = next((role for role in roles if role.find("Instructor") >= 0), None)
            has_ta_role = next((role for role in roles if role.find("TeachingAssistant") >= 0), None)

            # create lti user if doesn't exist
            if not lti_user:
                lti_user = LTIUser(
                    lti_consumer_id=lti_context.lti_consumer_id,
                    user_id=member.get('user_id'),
                    system_role=SystemRole.instructor if has_instructor_role else SystemRole.student,
                    lis_person_name_given=member.get('person_name_given'),
                    lis_person_name_family=member.get('person_name_family'),
                    lis_person_name_full=member.get('person_name_full'),
                    lis_person_contact_email_primary=member.get('person_contact_email_primary')
                )
                new_lti_users.append(lti_user)

            course_role = CourseRole.student
            if has_instructor_role:
                course_role = CourseRole.instructor
            elif has_ta_role:
                course_role = CourseRole.teaching_assistant

            # create new lti membership row
            lti_membership = LTIMembership(
                lti_user=lti_user,
                lti_context=lti_context,
                roles=text_type(roles),
                lis_result_sourcedid=member.get('lis_result_sourcedid'),
                course_role=course_role
            )
            lti_memberships.append(lti_membership)

        db.session.add_all(new_lti_users)
        db.session.add_all(lti_memberships)

        # save new lti users
        db.session.commit()

        return lti_memberships

    @classmethod
    def _update_enrollment_for_course(cls, course_id, lti_members):
        from compair.models import UserCourse

        user_courses = UserCourse.query \
            .filter_by(course_id=course_id) \
            .all()
        new_user_courses = []

        for lti_member in lti_members:
            if lti_member.compair_user_id != None:
                user_course = next(
                    (user_course for user_course in user_courses if user_course.user_id == lti_member.compair_user_id),
                    None
                )
                # add new user_course if doesn't exist
                if user_course == None:
                    user_course = UserCourse(
                        course_id=course_id,
                        user_id=lti_member.compair_user_id,
                        course_role=lti_member.course_role
                    )
                    new_user_courses.append(user_course)

                # update user_course role
                else:
                    user_course.course_role=lti_member.course_role

        db.session.add_all(new_user_courses)
        db.session.commit()

        # set user_course to dropped role if missing from membership results and not current user
        for user_course in user_courses:
            # never unenrol current_user
            if current_user and current_user.is_authenticated and user_course.user_id == current_user.id:
                continue

            lti_member = next(
                (lti_member for lti_member in lti_members if user_course.user_id == lti_member.compair_user_id),
                None
            )
            if lti_member == None:
                user_course.course_role = CourseRole.dropped

        db.session.commit()

    @classmethod
    def _get_membership(cls, lti_context):
        if lti_context.membership_ext_enabled:
            return LTIMembership._get_membership_ext(lti_context)
        elif lti_context.membership_service_enabled:
            return LTIMembership._get_membership_service(lti_context)
        return []

    @classmethod
    def _get_membership_ext(cls, lti_context):
        lti_consumer = lti_context.lti_consumer
        memberships_id = lti_context.ext_ims_lis_memberships_id
        memberships_url = lti_context.ext_ims_lis_memberships_url
        params = {
            'id': memberships_id,
            'lti_message_type':'basic-lis-readmembershipsforcontext',
            'lti_version': 'LTI-1p0',
            'oauth_callback': 'about:blank'
        }
        request = requests.Request('POST', memberships_url, data=params).prepare()
        sign = OAuth1(lti_consumer.oauth_consumer_key, lti_consumer.oauth_consumer_secret,
            signature_type=SIGNATURE_TYPE_BODY, signature_method=SIGNATURE_HMAC)
        signed_request = sign(request)
        params = parse_qs(signed_request.body.decode('utf-8'))

        data = LTIMembership._post_membership_request(memberships_url, params)
        root = ElementTree.fromstring(data)

        codemajor = root.find('statusinfo/codemajor')
        if codemajor is not None and codemajor.text in ['Failure', 'Unsupported']:
            raise MembershipInvalidRequestException

        if root.find('memberships') == None or len(root.findall('memberships/member')) == 0:
            raise MembershipNoResultsException

        members = []
        for record in root.findall('memberships/member'):
            roles_text = record.findtext('roles')

            member = {
                'user_id': record.findtext('user_id'),
                'roles': roles_text.split(",") if roles_text != None else [],
                'person_contact_email_primary': record.findtext('person_contact_email_primary'),
                'person_name_given': record.findtext('person_name_given'),
                'person_name_family': record.findtext('person_name_family'),
                'person_name_full': record.findtext('person_name_full')
            }

            # override user_id with user_id_override if present in membership result
            if lti_consumer.user_id_override and record.findtext(lti_consumer.user_id_override) is not None:
                member['user_id'] = record.findtext(lti_consumer.user_id_override)

            members.append(member)
        return members

    @classmethod
    def _get_membership_service(cls, lti_context):
        # possible parameters are role, lis_result_sourcedid, limit
        lti_consumer = lti_context.lti_consumer
        memberships_url = lti_context.custom_context_memberships_url

        members = []

        while True:
            headers = { 'Accept': 'application/vnd.ims.lis.v2.membershipcontainer+json' }
            request = requests.Request('GET', memberships_url, headers=headers).prepare()
            # Note: need to use LTIMemerbshipServiceOauthClient since normal client will
            #       not include oauth_body_hash if there is not content type or the body is None
            sign = OAuth1(lti_consumer.oauth_consumer_key, lti_consumer.oauth_consumer_secret,
                signature_type=SIGNATURE_TYPE_AUTH_HEADER, signature_method=SIGNATURE_HMAC,
                client_class=LTIMemerbshipServiceOauthClient)
            signed_request = sign(request)
            headers = signed_request.headers
            data = LTIMembership._get_membership_request(memberships_url, headers)

            membership = data['pageOf']['membershipSubject']['membership']

            if len(membership) == 0:
                raise MembershipNoResultsException

            for record in membership:
                if record.get('status').find("Inactive") >= 0:
                    continue
                member = {
                    'user_id': record['member'].get('userId'),
                    'roles': record.get('role'),
                    'person_contact_email_primary': record['member'].get('email'),
                    'person_name_given': record['member'].get('givenName'),
                    'person_name_family': record['member'].get('familyName'),
                    'person_name_full': record['member'].get('name')
                }

                # override user_id with user_id_override if present in membership result
                if lti_consumer.user_id_override and 'message' in record:
                    for message in record['message']:
                        if not message['message_type'] == 'basic-lti-launch-request':
                            continue

                        # check if user_id_override is a basic lti parameter
                        if lti_consumer.user_id_override in message:
                            member['user_id'] = message[lti_consumer.user_id_override]
                        # check if user_id_override is an extension and present
                        elif lti_consumer.user_id_override.startswith('ext_'):
                            ext_override = lti_consumer.user_id_override[len('ext_'):]
                            if ext_override in message['ext']:
                                member['user_id'] = message['ext'][ext_override]
                        # check if user_id_override is an custom attribute and present
                        elif lti_consumer.user_id_override.startswith('custom_'):
                            custom_override = lti_consumer.user_id_override[len('custom_'):]
                            if custom_override in message['custom']:
                                member['user_id'] = message['custom'][custom_override]

                members.append(member)
            # check if another page or else finish
            memberships_url = data.get('nextPage')
            if not memberships_url:
                break

        return members

    @classmethod
    def _post_membership_request(cls, memberships_url, params):
        verify = current_app.config.get('ENFORCE_SSL', True)
        return requests.post(memberships_url, data=params, verify=verify).text

    @classmethod
    def _get_membership_request(cls, memberships_url, headers=None):
        verify = current_app.config.get('ENFORCE_SSL', True)
        return requests.get(memberships_url, headers=headers, verify=verify).json()

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_context_id', 'lti_user_id', name='_unique_lti_context_and_lti_user'),
        DefaultTableMixin.default_table_args
    )