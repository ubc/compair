"""
    Utility Commands
"""
from io import open

from flask import current_app
from flask import render_template
from flask_script import Manager

manager = Manager(usage="Utility Commands")


@manager.command
def generate_index():
    """
    Generate compair/static/index.html for acceptance testing

    :return: None
    """
    current_app.static_url_path = '/'
    index = render_template(
        'index-dev.html',
        attachment_extensions=list(current_app.config['ATTACHMENT_ALLOWED_EXTENSIONS']),
        attachment_upload_limit=current_app.config['ATTACHMENT_UPLOAD_LIMIT'],
        attachment_preview_extensions=list(current_app.config['ATTACHMENT_PREVIEW_EXTENSIONS']),
        app_login_enabled=True,
        cas_login_enabled=True,
        saml_login_enabled=True,
        lti_login_enabled=True,
        login_addition_instructions_html=current_app.config['LOGIN_ADDITIONAL_INSTRUCTIONS_HTML'],
        cas_login_html=current_app.config['CAS_LOGIN_HTML'],
        saml_login_html=current_app.config['SAML_LOGIN_HTML'],
        allow_student_change_name=True,
        allow_student_change_display_name=True,
        allow_student_change_student_number=True,
        allow_student_change_email=True,
        kaltura_enabled=False,
        kaltura_extensions=list(current_app.config['KALTURA_ATTACHMENT_EXTENSIONS']),
        expose_email_to_instructor=False,
        notifications_enabled=True,
        impersonation_enabled=False,
    )

    with open("compair/static/index.html", 'wt', encoding='utf-8') as f:
        f.write(index)

    print("compair/static/index.html is generated.")
