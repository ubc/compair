from werkzeug.utils import redirect

from . import login_manager


@login_manager.unauthorized_handler
def unauthorized():
	redirect('/login')
