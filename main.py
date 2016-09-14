import os

from acj import create_app

# this logic can be removed after upgraded to flask 0.11
if os.environ.get('FLASK_DEBUG') and \
        (os.environ.get('FLASK_DEBUG') == 'True'
         or os.environ.get('FLASK_DEBUG') == 'true'):
    os.environ['DEBUG'] = 'True'

app = create_app()

# needed to get flask debugging working with uwsgi in docker
# (since it ignores FLASK_DEBUG & DEBUG)
if os.environ['DEV'] == '1':
    app.debug = True