from flask import session, request
from flask_login import current_user, login_user

class Impersonation:
    # action constant. can be used with bouncer
    IMPERSONATE = 'impersonate'

    # Set of session keys used by impersonation. For easy clean up
    _SESSION_KEYS = set(['impersonation_original_user_id', 'impersonation_act_as_user_id'])

    def __init__(self):
        self._user_callback = None
        self._impersonation_authorize = None
        self._impersonation_process_request = None

    def init_app(self, app):
        # intercept incoming requests
        app.before_request(self._process_request)

    def user_loader(self, callback):
        '''
        Inject the callback for loading a user. Should be same as the user loader
        used for flask-login
        '''
        self._user_callback = callback
        return callback

    def authorize(self, callback):
        '''
        Inject the callback for authorizing impersonation. Callback should return
        True if the current user is authorized for impersonation.
        '''
        self._impersonation_authorize = callback
        return callback

    def process_request(self, callback):
        '''
        Inject the callback for intercepting incoming requests during impersonation.
        The callback will be invoked if the user is impersonating.
        Callback should return None if the request should proceed.  Any other return
        values will be treated as return value from the view and stop further request handling.
        '''
        self._impersonation_process_request = callback
        return callback

    def start_impersonation(self, act_as_user_id):
        '''
        Verify logged in user can do impersonation and switch the current_user of flask-login
        '''
        if self.can_impersonate(act_as_user_id):
            # store the current login user info to switch back later
            session['impersonation_original_user_id'] = current_user.get_id()
            session['impersonation_act_as_user_id'] = act_as_user_id

            login_user(self._load_user(act_as_user_id))

            return act_as_user_id

        return None

    def end_impersonation(self):
        '''
        End the impersonation.
        '''
        orig_user_id = self.get_impersonation_original_user_id()
        act_as_user_id = self.get_impersonation_act_as_user_id()
        if orig_user_id is not None and act_as_user_id is not None:
            login_user(self._load_user(orig_user_id))

        # clean up
        for key in self._SESSION_KEYS:
            session.pop(key, None)

    def get_impersonation_act_as_user_id(self):
        '''
        Check if impersonating another user.  If so, return that user id.  Otherwise, return None
        '''
        return session.get('impersonation_act_as_user_id', None)

    def get_impersonation_original_user_id(self):
        '''
        Check if impersonating another user.  If so, return user id of original user.  Otherwise, return None
        '''
        return session.get('impersonation_original_user_id', None)

    def get_impersonation_original_user(self):
        if not self.is_impersonating():
            return None
        return self._load_user(self.get_impersonation_original_user_id())

    def is_impersonating(self):
        return self.get_impersonation_act_as_user_id() is not None and \
               self.get_impersonation_original_user_id() is not None

    def can_impersonate(self, act_as_user_id):
        if self._impersonation_authorize is not None:
            return self._impersonation_authorize(act_as_user_id)
        return False

    def _process_request(self):
        if not self.is_impersonating() or self._impersonation_process_request is None:
            return None     # proceed with the request
        return self._impersonation_process_request(request)

    def _load_user(self, user_id):
        if self._user_callback is None:
            raise Exception("Missing user_loader for impersonation")
        return self._user_callback(user_id)