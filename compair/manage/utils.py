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
        app_login_enabled=current_app.config['APP_LOGIN_ENABLED'],
        cas_login_enabled=current_app.config['CAS_LOGIN_ENABLED'],
        lti_login_enabled=current_app.config['LTI_LOGIN_ENABLED']
    )

    with open("compair/static/index.html", 'wt', encoding='utf-8') as f:
        f.write(index)

    print("compair/static/index.html is generated.")
