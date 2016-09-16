"""
    Utility Commands
"""
from flask import current_app
from flask import render_template
from flask.ext.script import Manager

manager = Manager(usage="Utility Commands")


@manager.command
def generate_index():
    """
    Generate acj/static/index.html for acceptance testing

    :return: None
    """
    current_app.static_url_path = '/'
    index = render_template('index-dev.html')

    with open("acj/static/index.html", "wb") as f:
        f.write(index)

    print "acj/static/index.html is generated."
