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
        app_login_enabled=True,
        cas_login_enabled=True,
        saml_login_enabled=True,
        lti_login_enabled=True,
        kaltura_enabled=False,
        kaltura_extensions=list(current_app.config['KALTURA_ATTACHMENT_EXTENSIONS']),
        expose_email_to_instructor=False,
        notifications_enabled=True
    )

    with open("compair/static/index.html", 'wt', encoding='utf-8') as f:
        f.write(index)

    print("compair/static/index.html is generated.")
