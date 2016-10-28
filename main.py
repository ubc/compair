import os
from compair import create_app

app = create_app()

# needed to get flask debugging working with uwsgi in docker
# (since it ignores FLASK_DEBUG & DEBUG)
if os.environ['DEV'] == '1':
    app.debug = True