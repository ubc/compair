import os
from acj import create_app, celery

app = create_app(skip_endpoints=True, skip_assets=True)

# needed to get flask debugging working with uwsgi in docker
# (since it ignores FLASK_DEBUG & DEBUG)
if os.environ['DEV'] == '1':
    app.debug = True

app.app_context().push()