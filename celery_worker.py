import os
from compair import create_app, celery
from compair.core import db

app = create_app(skip_endpoints=True, skip_assets=True)

# needed to get flask debugging working with uwsgi in docker
# (since it ignores FLASK_DEBUG & DEBUG)
if os.environ.get('DEV') == '1':
    app.debug = True

TaskBase = celery.Task
class ContextTask(TaskBase):
    abstract = True
    def __call__(self, *args, **kwargs):
        with app.app_context():
            try:
                return TaskBase.__call__(self, *args, **kwargs)
            finally:
                db.session.remove()
celery.Task = ContextTask
