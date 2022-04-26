import json
import re
from six import text_type

# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Enum, func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import current_user
from flask import current_app

from . import *

from compair.core import db

from oauthlib.oauth1 import SIGNATURE_TYPE_BODY, SIGNATURE_TYPE_AUTH_HEADER, SIGNATURE_HMAC
from .helpers import LTIMemerbshipServiceOauthClient

from requests_oauthlib import OAuth1
from lti.utils import parse_qs, urlparse
import requests
from xml.etree import ElementTree

import urllib
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

class LTIMembership(DefaultTableMixin, WriteTrackingMixin):
    __tablename__ = 'lti_membership'

    # table columns
    lti_context_id = db.Column(db.Integer, db.ForeignKey("lti_context.id", ondelete="CASCADE"),
        nullable=False)
    lti_user_id = db.Column(db.Integer, db.ForeignKey("lti_user.id", ondelete="CASCADE"),
        nullable=False)
    roles = db.Column(db.String(255), nullable=True)
    lis_result_sourcedid = db.Column(db.String(255), nullable=True)
    lis_result_sourcedids = db.Column(db.Text, nullable=True)
    course_role = db.Column(Enum(CourseRole, name="course_role"),
                            nullable=False)

    compair_course_id = association_proxy('lti_context', 'compair_course_id')
    compair_user_id = association_proxy('lti_user', 'compair_user_id')

    # relationships
    # lti_conext via LTIContext Model
    # lti_user via LTIUser Model

    # hybrid and other functions
    context_id = association_proxy('lti_context', 'context_id')
    user_id = association_proxy('lti_user', 'user_id')

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
        from compair.models import SystemRole, CourseRole, \
            LTIUser, LTIUserResourceLink

        lti_resource_links = lti_context.lti_resource_links

        # remove old membership rows
        LTIMembership.query \
            .filter_by(
                lti_context_id=lti_context.id
            ) \
            .delete()

        # retrieve existing lti_user rows
        user_ids = []
        for member in members:
            user_ids.append(member['user_id'])

        existing_lti_users = []
        if len(user_ids) > 0:
            existing_lti_users = LTIUser.query \
                .filter(and_(
                    LTIUser.lti_consumer_id == lti_context.lti_consumer_id,
                    LTIUser.user_id.in_(user_ids)
                )) \
                .all()

        # get existing lti_user_resource_link if there there exists lti users and known resource links for context
        existing_lti_user_resource_links = []
        if len(existing_lti_users) > 0 and len(lti_resource_links) > 0:
            lti_resource_link_ids = [lti_resource_link.id for lti_resource_link in lti_resource_links]
            existing_lti_user_ids = [existing_lti_user.id for existing_lti_user in existing_lti_users]
            existing_lti_user_resource_links = LTIUserResourceLink.query \
                .filter(and_(
                    LTIUserResourceLink.lti_resource_link_id.in_(lti_resource_link_ids),
                    LTIUserResourceLink.lti_user_id.in_(existing_lti_user_ids)
                )) \
                .all()

        new_lti_users = []
        new_lti_user_resource_links = []
        lti_memberships = []
        for member in members:
            # get lti user if exists
            lti_user = next(
                (lti_user for lti_user in existing_lti_users if lti_user.user_id == member.get('user_id')),
                None
            )
            roles = member.get('roles')
            has_instructor_role = any(
                role.lower().find("instructor") >= 0 or
                role.lower().find("faculty") >= 0 or
                role.lower().find("staff") >= 0
                for role in roles
            )
            has_ta_role =  any(role.lower().find("teachingassistant") >= 0 for role in roles)

            # create lti user if doesn't exist
            if not lti_user:
                lti_user = LTIUser(
                    lti_consumer_id=lti_context.lti_consumer_id,
                    user_id=member.get('user_id')
                )
                new_lti_users.append(lti_user)

            # update/set fields if needed
            lti_user.system_role = SystemRole.instructor if has_instructor_role else SystemRole.student
            lti_user.lis_person_name_given = member.get('person_name_given')
            lti_user.lis_person_name_family = member.get('person_name_family')
            lti_user.lis_person_name_full = member.get('person_name_full')
            lti_user.handle_fullname_with_missing_first_and_last_name()

            lti_user.lis_person_contact_email_primary = member.get('person_contact_email_primary')
            lti_user.lis_person_sourcedid = member.get('lis_person_sourcedid')

            if member.get('global_unique_identifier'):
                lti_user.global_unique_identifier = member.get('global_unique_identifier')

            if member.get('student_number'):
                lti_user.student_number = member.get('student_number')

            if not lti_user.is_linked_to_user() and lti_user.global_unique_identifier:
                lti_user.generate_or_link_user_account()

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
                lis_result_sourcedids=json.dumps(member.get('lis_result_sourcedids')) if member.get('lis_result_sourcedids') else None,
                course_role=course_role
            )
            lti_memberships.append(lti_membership)

            # if membership includes lis_result_sourcedids, create/update lti user resource links
            if member.get('lis_result_sourcedids'):
                for lis_result_sourcedid_set in member.get('lis_result_sourcedids'):
                    lti_resource_link = next(
                        lti_resource_link for lti_resource_link in lti_resource_links
                        if lti_resource_link.resource_link_id == lis_result_sourcedid_set['resource_link_id']
                    )

                    if not lti_resource_link:
                        continue

                    lti_user_resource_link = None
                    if len(existing_lti_user_resource_links) > 0 and lti_user.id:
                        # get lti user resource link if exists
                        lti_user_resource_link = next(
                            (lti_user_resource_link for lti_user_resource_link in existing_lti_user_resource_links
                            if lti_user_resource_link.lti_user_id == lti_user.id and lti_user_resource_link.lti_resource_link_id == lti_resource_link.id),
                            None
                        )

                    # create new lti user resource link if needed
                    if not lti_user_resource_link:
                        lti_user_resource_link = LTIUserResourceLink(
                            lti_resource_link=lti_resource_link,
                            lti_user=lti_user,
                            roles=text_type(roles),
                            course_role=course_role
                        )
                        new_lti_user_resource_links.append(lti_user_resource_link)

                    # finally update the lis_result_sourcedid value for the user resource link
                    lti_user_resource_link.lis_result_sourcedid = lis_result_sourcedid_set['lis_result_sourcedid']

        db.session.add_all(new_lti_users)
        db.session.add_all(existing_lti_users)
        db.session.add_all(lti_memberships)
        db.session.add_all(new_lti_user_resource_links)
        db.session.add_all(existing_lti_user_resource_links)

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

                # update user profile if needed
                lti_member.lti_user.update_user_profile()

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
        root = ElementTree.fromstring(data.encode('utf-8'))

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
                'global_unique_identifier': None,
                'student_number': None,
                'lis_result_sourcedid': record.findtext('lis_result_sourcedid'),
                'person_contact_email_primary': record.findtext('person_contact_email_primary'),
                'person_name_given': record.findtext('person_name_given'),
                'person_name_family': record.findtext('person_name_family'),
                'person_name_full': record.findtext('person_name_full')
            }

            # find global unique identifier if available
            if lti_consumer.global_unique_identifier_param and record.findtext(lti_consumer.global_unique_identifier_param):
                member['global_unique_identifier'] = record.findtext(lti_consumer.global_unique_identifier_param)
                if lti_consumer.custom_param_regex_sanitizer and lti_consumer.global_unique_identifier_param.startswith('custom_'):
                    regex = re.compile(lti_consumer.custom_param_regex_sanitizer)
                    member['global_unique_identifier'] = regex.sub('', member['global_unique_identifier'])
                    if member['global_unique_identifier'] == '':
                        member['global_unique_identifier'] = None

            # find student number if available
            if lti_consumer.student_number_param and record.findtext(lti_consumer.student_number_param):
                member['student_number'] = record.findtext(lti_consumer.student_number_param)
                if lti_consumer.custom_param_regex_sanitizer and lti_consumer.student_number_param.startswith('custom_'):
                    regex = re.compile(lti_consumer.custom_param_regex_sanitizer)
                    member['student_number'] = regex.sub('', member['student_number'])
                    if member['student_number'] == '':
                        member['student_number'] = None

            members.append(member)
        return members

    @classmethod
    def _get_membership_service(cls, lti_context):
        # possible parameters are role, lis_result_sourcedid, limit
        lti_consumer = lti_context.lti_consumer
        memberships_url = lti_context.custom_context_memberships_url
        lti_resource_links = lti_context.lti_resource_links

        members = []

        while True:
            headers = { 'Accept': 'application/vnd.ims.lis.v2.membershipcontainer+json' }
            request = requests.Request('GET', memberships_url, headers=headers).prepare()
            # Note: need to use LTIMemerbshipServiceOauthClient since normal client will
            #       not include oauth_body_hash if there is not content type or the body is None
            sign = OAuth1(lti_consumer.oauth_consumer_key, lti_consumer.oauth_consumer_secret,
                signature_type=SIGNATURE_TYPE_AUTH_HEADER, signature_method=SIGNATURE_HMAC,
                client_class=LTIMemerbshipServiceOauthClient)
            # sign = OAuth1(lti_consumer.oauth_consumer_key, lti_consumer.oauth_consumer_secret,
            #     signature_type=SIGNATURE_TYPE_AUTH_HEADER, signature_method=SIGNATURE_HMAC)
            signed_request = sign(request)
            headers = signed_request.headers
            data = LTIMembership._get_membership_request(memberships_url, headers)

            if data == None:
                break

            membership = data['pageOf']['membershipSubject']['membership']

            if len(membership) == 0:
                raise MembershipNoResultsException

            for record in membership:
                if record.get('status').find("Inactive") >= 0:
                    continue
                member = {
                    'user_id': record['member'].get('userId'),
                    'roles': record.get('role'),
                    'lis_person_sourcedid': record['member'].get('sourcedId'),
                    'global_unique_identifier': None,
                    'student_number': None,
                    'person_contact_email_primary': record['member'].get('email'),
                    'person_name_given': record['member'].get('givenName'),
                    'person_name_family': record['member'].get('familyName'),
                    'person_name_full': record['member'].get('name')
                }

                if (lti_consumer.global_unique_identifier_param or lti_consumer.student_number_param) and 'message' in record:
                    for message in record['message']:
                        if not message['message_type'] == 'basic-lti-launch-request':
                            continue

                        # find global unique identifier if present in membership result
                        if lti_consumer.global_unique_identifier_param:
                            # check if global_unique_identifier_param is a basic lti parameter
                            if lti_consumer.global_unique_identifier_param in message:
                                member['global_unique_identifier'] = message[lti_consumer.global_unique_identifier_param]
                            # check if global_unique_identifier_param is an extension and present
                            elif lti_consumer.global_unique_identifier_param.startswith('ext_'):
                                ext_global_unique_identifier = lti_consumer.global_unique_identifier_param[len('ext_'):]
                                if ext_global_unique_identifier in message['ext']:
                                    member['global_unique_identifier'] = message['ext'][ext_global_unique_identifier]
                            # check if global_unique_identifier_param is an custom attribute and present
                            elif lti_consumer.global_unique_identifier_param.startswith('custom_'):
                                custom_global_unique_identifier = lti_consumer.global_unique_identifier_param[len('custom_'):]
                                if custom_global_unique_identifier in message['custom']:
                                    member['global_unique_identifier'] = message['custom'][custom_global_unique_identifier]

                        # get student number if present in membership result
                        if lti_consumer.student_number_param:
                            # check if student_number_param is a basic lti parameter
                            if lti_consumer.student_number_param in message:
                                member['student_number'] = message[lti_consumer.student_number_param]
                            # check if student_number_param is an extension and present
                            elif lti_consumer.student_number_param.startswith('ext_'):
                                ext_student_number = lti_consumer.student_number_param[len('ext_'):]
                                if ext_student_number in message['ext']:
                                    member['student_number'] = message['ext'][ext_student_number]
                            # check if student_number_param is an custom attribute and present
                            elif lti_consumer.student_number_param.startswith('custom_'):
                                custom_student_number = lti_consumer.student_number_param[len('custom_'):]
                                if custom_student_number in message['custom']:
                                    member['student_number'] = message['custom'][custom_student_number]

                members.append(member)
            # check if another page or else finish
            memberships_url = data.get('nextPage')
            if not memberships_url:
                break

        # get lis_result_sourcedid for all resource links known to the system
        for lti_resource_link in lti_resource_links:
            memberships_url = lti_context.custom_context_memberships_url
            # add role t0 membership url query string
            memberships_url += "?" if memberships_url.find("?") == -1 else "&"
            memberships_url += "role=Learner"
            # add rlid to membership url query string
            memberships_url += "&rlid={}".format(lti_resource_link.resource_link_id)

            while True:
                headers = { 'Accept': 'application/vnd.ims.lis.v2.membershipcontainer+json' }
                request = requests.Request('GET', memberships_url, headers=headers).prepare()
                # Note: need to use LTIMemerbshipServiceOauthClient since normal client will
                #       not include oauth_body_hash if there is not content type or the body is None
                sign = OAuth1(lti_consumer.oauth_consumer_key, lti_consumer.oauth_consumer_secret,
                    signature_type=SIGNATURE_TYPE_AUTH_HEADER, signature_method=SIGNATURE_HMAC,
                    client_class=LTIMemerbshipServiceOauthClient)
                # sign = OAuth1(lti_consumer.oauth_consumer_key, lti_consumer.oauth_consumer_secret,
                #     signature_type=SIGNATURE_TYPE_AUTH_HEADER, signature_method=SIGNATURE_HMAC)
                signed_request = sign(request)
                headers = signed_request.headers
                data = LTIMembership._get_membership_request(memberships_url, headers)

                if data == None:
                    break

                membership = data['pageOf']['membershipSubject']['membership']

                if len(membership) == 0:
                    continue

                for record in membership:
                    if record.get('status').find("Inactive") >= 0:
                        continue

                    member = next(
                        (member for member in members if member['user_id'] == record['member'].get('userId')),
                        None
                    )

                    if not member or not 'message' in record:
                        continue

                    for message in record['message']:
                        if not message['message_type'] == 'basic-lti-launch-request' or not 'lis_result_sourcedid' in message:
                            continue

                        lis_result_sourcedid_array = member.setdefault('lis_result_sourcedids', [])
                        lis_result_sourcedid_array.append({
                            'resource_link_id': lti_resource_link.resource_link_id,
                            'lis_result_sourcedid': message['lis_result_sourcedid']
                        })

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
        rv = requests.get(memberships_url, headers=headers, verify=verify)
        if rv.content:
            return rv.json()
        return None

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    __table_args__ = (
        # prevent duplicate resource link in consumer
        db.UniqueConstraint('lti_context_id', 'lti_user_id', name='_unique_lti_context_and_lti_user'),
        DefaultTableMixin.default_table_args
    )
