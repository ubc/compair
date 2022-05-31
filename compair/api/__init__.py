import mimetypes
import os
import re
from functools import wraps

from flask import redirect, render_template, jsonify, current_app
from flask_login import login_required, current_user
from flask import make_response
from flask import send_file, url_for, redirect, request
from flask_restful.reqparse import RequestParser

from bouncer.constants import READ
from compair.authorization import require
from compair.kaltura import KalturaAPI
from compair.models import File
from compair.core import event
on_get_file = event.signal('GET_FILE')

attachment_download_parser = RequestParser()
attachment_download_parser.add_argument('name', default=None)

def register_api_blueprints(app):
    # Initialize rest of the api modules
    from .course import course_api
    app.register_blueprint(
        course_api,
        url_prefix='/api/courses')

    from .classlist import classlist_api
    app.register_blueprint(
        classlist_api,
        url_prefix='/api/courses/<course_uuid>/users')

    from .group import group_api
    app.register_blueprint(
        group_api,
        url_prefix='/api/courses/<course_uuid>/groups')

    from .group_user import group_user_api
    app.register_blueprint(
        group_user_api,
        url_prefix='/api/courses/<course_uuid>/groups')

    from .login import login_api
    app.register_blueprint(login_api)

    from .lti_launch import lti_api
    app.register_blueprint(
        lti_api,
        url_prefix='/api/lti')

    from .lti_course import lti_course_api
    app.register_blueprint(
        lti_course_api,
        url_prefix='/api/lti/course')

    from .lti_consumers import lti_consumer_api
    app.register_blueprint(
        lti_consumer_api,
        url_prefix='/api/lti/consumers')

    from .users import user_api
    app.register_blueprint(
        user_api,
        url_prefix='/api/users')

    from .assignment import assignment_api
    app.register_blueprint(
        assignment_api,
        url_prefix='/api/courses/<course_uuid>/assignments')

    from .assignment_search_enddate import assignment_search_enddate_api
    app.register_blueprint(
        assignment_search_enddate_api,
        url_prefix='/api/assignment/search/enddate')

    from .answer import answers_api
    app.register_blueprint(
        answers_api,
        url_prefix='/api/courses/<course_uuid>/assignments/<assignment_uuid>/answers')

    from .file import file_api
    app.register_blueprint(
        file_api,
        url_prefix='/api/attachment')

    from .assignment_attachment import assignment_attachment_api
    app.register_blueprint(
        assignment_attachment_api,
        url_prefix='/api/courses/<course_uuid>/assignments/<assignment_uuid>/attachments')
    
    from .answer_comment import answer_comment_api
    app.register_blueprint(
        answer_comment_api,
        url_prefix='/api/courses/<course_uuid>/assignments/<assignment_uuid>')

    from .criterion import criterion_api
    app.register_blueprint(
        criterion_api,
        url_prefix='/api/criteria')

    from .comparison import comparison_api
    app.register_blueprint(
        comparison_api,
        url_prefix='/api/courses/<course_uuid>/assignments/<assignment_uuid>/comparisons')

    from .comparison_example import comparison_example_api
    app.register_blueprint(
        comparison_example_api,
        url_prefix='/api/courses/<course_uuid>/assignments/<assignment_uuid>/comparisons/examples')

    from .report import report_api
    app.register_blueprint(
        report_api,
        url_prefix='/api/courses/<course_uuid>/report')

    from .gradebook import gradebook_api
    app.register_blueprint(
        gradebook_api,
        url_prefix='/api/courses/<course_uuid>/assignments/<assignment_uuid>/gradebook')

    from .common import timer_api
    app.register_blueprint(
        timer_api,
        url_prefix='/api/timer')

    from .healthz import healthz_api
    app.register_blueprint(healthz_api)

    from .impersonation import impersonation_api, IMPERSONATION_API_BASE_URL
    app.register_blueprint(impersonation_api, url_prefix=IMPERSONATION_API_BASE_URL)

    @app.route('/app/')
    def route_app():
        if app.debug or app.config.get('TESTING', False):
            return render_template(
                'index-dev.html',
                ga_tracking_id=app.config['GA_TRACKING_ID'],
                attachment_extensions=list(app.config['ATTACHMENT_ALLOWED_EXTENSIONS']),
                attachment_upload_limit=app.config['ATTACHMENT_UPLOAD_LIMIT'],
                attachment_preview_extensions=list(app.config['ATTACHMENT_PREVIEW_EXTENSIONS']),
                app_login_enabled=app.config['APP_LOGIN_ENABLED'],
                cas_login_enabled=app.config['CAS_LOGIN_ENABLED'],
                saml_login_enabled=app.config['SAML_LOGIN_ENABLED'],
                lti_login_enabled=app.config['LTI_LOGIN_ENABLED'],
                login_addition_instructions_html=app.config['LOGIN_ADDITIONAL_INSTRUCTIONS_HTML'],
                cas_login_html=app.config['CAS_LOGIN_HTML'],
                saml_login_html=app.config['SAML_LOGIN_HTML'],
                kaltura_enabled=app.config['KALTURA_ENABLED'],
                kaltura_extensions=list(app.config['KALTURA_ATTACHMENT_EXTENSIONS']),
                expose_email_to_instructor=app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'],
                allow_student_change_name=app.config['ALLOW_STUDENT_CHANGE_NAME'],
                allow_student_change_display_name=app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'],
                allow_student_change_student_number=app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'],
                allow_student_change_email=app.config['ALLOW_STUDENT_CHANGE_EMAIL'],
                notifications_enabled=app.config['MAIL_NOTIFICATION_ENABLED'],
                xapi_enabled=app.config['XAPI_ENABLED'],
                caliper_enabled=app.config['CALIPER_ENABLED'],
                lrs_app_base_url=app.config.get('LRS_APP_BASE_URL'),
                demo=app.config.get('DEMO_INSTALLATION'),
                impersonation_enabled=app.config['IMPERSONATION_ENABLED'],
            )

        # running in prod mode, figure out asset location
        assets = app.config['ASSETS']
        prefix = app.config['ASSET_PREFIX']

        return render_template(
            'index.html',
            bower_js_libs=prefix + assets['bowerJsLibs.js'],
            compair_js=prefix + assets['compair.js'],
            compair_css=prefix + assets['compair.css'],
            static_img_path=prefix,
            ga_tracking_id=app.config['GA_TRACKING_ID'],
            attachment_extensions=list(app.config['ATTACHMENT_ALLOWED_EXTENSIONS']),
            attachment_upload_limit=app.config['ATTACHMENT_UPLOAD_LIMIT'],
            attachment_preview_extensions=list(app.config['ATTACHMENT_PREVIEW_EXTENSIONS']),
            app_login_enabled=app.config['APP_LOGIN_ENABLED'],
            cas_login_enabled=app.config['CAS_LOGIN_ENABLED'],
            saml_login_enabled=app.config['SAML_LOGIN_ENABLED'],
            lti_login_enabled=app.config['LTI_LOGIN_ENABLED'],
            login_addition_instructions_html=app.config['LOGIN_ADDITIONAL_INSTRUCTIONS_HTML'],
            cas_login_html=app.config['CAS_LOGIN_HTML'],
            saml_login_html=app.config['SAML_LOGIN_HTML'],
            kaltura_enabled=app.config['KALTURA_ENABLED'],
            kaltura_extensions=list(app.config['KALTURA_ATTACHMENT_EXTENSIONS']),
            expose_email_to_instructor=app.config['EXPOSE_EMAIL_TO_INSTRUCTOR'],
            allow_student_change_name=app.config['ALLOW_STUDENT_CHANGE_NAME'],
            allow_student_change_display_name=app.config['ALLOW_STUDENT_CHANGE_DISPLAY_NAME'],
            allow_student_change_student_number=app.config['ALLOW_STUDENT_CHANGE_STUDENT_NUMBER'],
            allow_student_change_email=app.config['ALLOW_STUDENT_CHANGE_EMAIL'],
            notifications_enabled=app.config['MAIL_NOTIFICATION_ENABLED'],
            xapi_enabled=app.config['XAPI_ENABLED'],
            caliper_enabled=app.config['CALIPER_ENABLED'],
            lrs_app_base_url=app.config.get('LRS_APP_BASE_URL'),
            demo=app.config.get('DEMO_INSTALLATION'),
            impersonation_enabled=app.config['IMPERSONATION_ENABLED'],
        )

    @app.route('/')
    def route_root():
        return redirect("/app/")

    @app.route('/app/pdf')
    def route_pdf_viewer():
        if app.debug or app.config.get('TESTING', False):
            return render_template(
                'pdf-viewer.html',
                pdf_lib_folder=url_for('static', filename='lib/pdf.js-viewer')
            )

        # running in prod mode, figure out asset location
        assets = app.config['ASSETS']
        prefix = app.config['ASSET_PREFIX']

        return render_template(
            'pdf-viewer.html',
            pdf_lib_folder=prefix + 'pdf.js-viewer'
        )

    def force_ms_office_refresh(f):
        """
        Hack for opening ComPAIR attachments from Excel etc tools.
        MS office doesn't share browser sessions, causing authorization error even
        when the user has a valid ComPAIR session opened in browser.
        https://support.microsoft.com/en-us/help/899927/you-are-redirected-to-a-logon-page-or-an-error-page-or-you-are-prompte
        https://stackoverflow.com/questions/2653626/why-are-cookies-unrecognized-when-a-link-is-clicked-from-an-external-source-i-e
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if any(agent in request.headers.get('User-Agent', '') for agent in ['ms-office', 'PowerPoint', 'Excel', 'Word']):
                # Generate an empty response with header telling the actual browser to refresh
                response = make_response('')
                response.headers['Refresh'] = '0'
                return response
            return f(*args, **kwargs)

        return decorated_function

    @app.route('/app/<regex("attachment|report"):file_type>/<file_name>')
    @force_ms_office_refresh
    @login_required
    def file_retrieve(file_type, file_name):
        file_dirs = {
            'attachment': app.config['ATTACHMENT_UPLOAD_FOLDER'],
            'report': app.config['REPORT_FOLDER']
        }
        file_path = '{}/{}'.format(file_dirs[file_type], file_name)
        params = attachment_download_parser.parse_args()

        if file_type == 'attachment':
            attachment = File.get_by_file_name_or_404(
                file_name,
                joinedloads=['answers', 'assignments']
            )

            for answer in attachment.answers:
                require(READ, answer,
                    title="Attachment Unavailable",
                    message="Sorry, your role does not allow you to view the attachment.")

            for assignment in attachment.assignments:
                require(READ, assignment,
                    title="Attachment Unavailable",
                    message="Sorry, your role does not allow you to view the attachment.")

            # If attachment is in Kaltura, redirect the user
            if attachment.kaltura_media and KalturaAPI.enabled():
                entry_id = attachment.kaltura_media.entry_id
                download_url = attachment.kaltura_media.download_url
                if entry_id:
                    # Short-lived session of 60 seconds for user to start the media download
                    kaltura_url = KalturaAPI.get_direct_access_url(entry_id, download_url, 60)
                    return redirect(kaltura_url)

        if not os.path.exists(file_path):
            return make_response('invalid file name', 404)

        # TODO: add bouncer for reports
        mimetype, encoding = mimetypes.guess_type(file_name)
        attachment_filename = None
        as_attachment = False

        if file_type == 'attachment' and mimetype != "application/pdf":
            attachment_filename = params.get('name') #optionally set the download file name
            as_attachment = True

        on_get_file.send(
            current_app._get_current_object(),
            event_name=on_get_file.name,
            user=current_user,
            file_type=file_type,
            file_name=file_name,
            data={'file_path': file_path, 'mimetype': mimetype})

        return send_file(file_path, mimetype=mimetype,
            attachment_filename=attachment_filename, as_attachment=as_attachment)

    # set Cache-Control for /api/* calls
    _api_call_pattern = re.compile('^' + re.escape('/api/'))
    def _api_call_cache_control(resp):
        if _api_call_pattern.match(request.full_path):
            if 'cache-contorl' not in set(k.lower() for k in resp.headers.keys()):
                resp.headers['Cache-Control'] = 'no-store'
        return resp
    app.after_request(_api_call_cache_control)

    return app

def register_learning_record_api_blueprints(app):
    from .learning_records import learning_record_api
    app.register_blueprint(
        learning_record_api,
        url_prefix='/api/learning_records')

    return app

def register_demo_api_blueprints(app):
    from .demo import demo_api
    app.register_blueprint(
        demo_api,
        url_prefix='/api/demo')

    return app

def log_events(log):
    # user events
    from .users import on_user_modified, on_user_get, on_user_list_get, on_user_create, on_user_course_get, \
        on_user_password_update, on_user_edit_button_get, on_teaching_course_get, on_user_notifications_update, \
        on_user_course_status_get, on_user_lti_users_get, on_user_lti_user_unlink, on_user_third_party_users_get, \
        on_user_third_party_user_delete
    on_user_modified.connect(log)
    on_user_get.connect(log)
    on_user_list_get.connect(log)
    on_user_create.connect(log)
    on_user_course_get.connect(log)
    on_teaching_course_get.connect(log)
    on_user_edit_button_get.connect(log)
    on_user_notifications_update.connect(log)
    on_user_password_update.connect(log)
    on_user_course_status_get.connect(log)
    on_user_lti_users_get.connect(log)
    on_user_lti_user_unlink.connect(log)
    on_user_third_party_users_get.connect(log)
    on_user_third_party_user_delete.connect(log)

    # course events
    from .course import on_course_modified, on_course_get, on_course_list_get, on_course_create, \
        on_course_delete, on_course_duplicate
    on_course_modified.connect(log)
    on_course_get.connect(log)
    on_course_delete.connect(log)
    on_course_list_get.connect(log)
    on_course_create.connect(log)
    on_course_duplicate.connect(log)

    # assignment events
    from .assignment import on_assignment_modified, on_assignment_get, on_assignment_list_get, on_assignment_create, \
        on_assignment_delete, on_assignment_list_get_status, on_assignment_get_status, \
        on_assignment_user_comparisons_get, on_assignment_users_comparisons_get
    on_assignment_modified.connect(log)
    on_assignment_get.connect(log)
    on_assignment_list_get.connect(log)
    on_assignment_create.connect(log)
    on_assignment_delete.connect(log)
    on_assignment_list_get_status.connect(log)
    on_assignment_get_status.connect(log)
    on_assignment_user_comparisons_get.connect(log)
    on_assignment_users_comparisons_get.connect(log)

    # answer events
    from .answer import on_answer_modified, on_answer_get, on_answer_list_get, on_answer_create, \
        on_set_top_answer, on_answer_delete, on_user_answer_get
    on_answer_modified.connect(log)
    on_answer_get.connect(log)
    on_answer_list_get.connect(log)
    on_answer_create.connect(log)
    on_set_top_answer.connect(log)
    on_answer_delete.connect(log)
    on_user_answer_get.connect(log)

    # answer comment events
    from .answer_comment import on_answer_comment_modified, on_answer_comment_get, on_answer_comment_list_get, \
        on_answer_comment_create, on_answer_comment_delete
    on_answer_comment_modified.connect(log)
    on_answer_comment_get.connect(log)
    on_answer_comment_list_get.connect(log)
    on_answer_comment_create.connect(log)
    on_answer_comment_delete.connect(log)

    # criterion events
    from .criterion import on_criterion_get, on_criterion_update, on_criterion_list_get, on_criterion_create
    on_criterion_get.connect(log)
    on_criterion_update.connect(log)
    on_criterion_list_get.connect(log)
    on_criterion_create.connect(log)

    # comparison events
    from .comparison import on_comparison_get, on_comparison_create, on_comparison_update
    on_comparison_get.connect(log)
    on_comparison_create.connect(log)
    on_comparison_update.connect(log)

    # comparison example events
    from .comparison_example import on_comparison_example_create, on_comparison_example_delete, \
        on_comparison_example_list_get, on_comparison_example_modified
    on_comparison_example_create.connect(log)
    on_comparison_example_delete.connect(log)
    on_comparison_example_list_get.connect(log)
    on_comparison_example_modified.connect(log)

    # classlist events
    from .classlist import on_classlist_get, on_classlist_upload, on_classlist_enrol, on_classlist_unenrol, \
        on_classlist_instructor, on_classlist_student, on_classlist_update_users_course_roles
    on_classlist_get.connect(log)
    on_classlist_upload.connect(log)
    on_classlist_enrol.connect(log)
    on_classlist_unenrol.connect(log)
    on_classlist_instructor.connect(log)
    on_classlist_student.connect(log)
    on_classlist_update_users_course_roles.connect(log)

    # group events
    from .group import on_group_create, on_group_delete, \
        on_group_edit, on_group_get
    on_group_create.connect(log)
    on_group_delete.connect(log)
    on_group_edit.connect(log)
    on_group_get.connect(log)

    # course user group events
    from .group_user import on_group_user_create, on_group_user_delete, \
        on_group_user_list_create, on_group_user_list_delete, \
        on_group_user_list_get, on_group_user_get
    on_group_user_create.connect(log)
    on_group_user_delete.connect(log)
    on_group_user_list_create.connect(log)
    on_group_user_list_delete.connect(log)
    on_group_user_list_get.connect(log)
    on_group_user_get.connect(log)

    # report event
    from .report import on_export_report
    on_export_report.connect(log)

    # file attachment event
    from .file import on_save_file, on_get_kaltura_token, on_save_kaltura_file, \
        on_attach_file, on_detach_file
    on_save_file.connect(log)
    on_get_kaltura_token.connect(log)
    on_save_kaltura_file.connect(log)
    on_attach_file.connect(log)
    on_detach_file.connect(log)

    # gradebook event
    from .gradebook import on_gradebook_get
    on_gradebook_get.connect(log)

    # lti launch event
    from .lti_course import on_lti_course_link_create, on_lti_course_membership_update, \
        on_lti_course_membership_status_get, on_lti_course_unlink
    on_lti_course_link_create.connect(log)
    on_lti_course_membership_update.connect(log)
    on_lti_course_membership_status_get.connect(log)

    # lti consumer event
    from .lti_consumers import on_consumer_create, on_consumer_get, \
        on_consumer_list_get, on_consumer_update
    on_consumer_create.connect(log)
    on_consumer_get.connect(log)
    on_consumer_list_get.connect(log)
    on_consumer_update.connect(log)

    # misc
    on_get_file.connect(log)

    # impersonation
    from .impersonation import on_impersonation_started, on_impersonation_stopped
    on_impersonation_started.connect(log)
    on_impersonation_stopped.connect(log)

def log_demo_events(log):
    # demo events
    from .demo import on_user_demo_create
    on_user_demo_create.connect(log)
