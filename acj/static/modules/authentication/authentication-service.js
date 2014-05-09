(function() {

// the module needs a unique name that prevents conflicts with 3rd party modules
var module = angular.module(
	'ubc.ctlt.acj.authentication',
	[
		'ngResource',
		'ngCookies',
		'http-auth-interceptor'
	]
);

module.factory('AuthenticationService',
	function ($rootScope, $resource, $cookieStore, $log, authService) {
		var _user = null
		return {
			// Use these constants to listen to login or logout events.
			LOGIN_EVENT: "event:Authentication-Login",
			LOGOUT_EVENT: "event:Authentication-Logout",
			LOGIN_REQUIRED_EVENT: "event:auth-loginRequired",
			getUser: function() {
				return _user;
			},
			isAuthenticated: function() {
				if (_user)
				{ // user stored in service
					return true
				}
				else
				{ // no user stored in service, check cookies
					var cookie_user = $cookieStore.get('current.user');
					if (cookie_user)
					{
						_user = cookie_user;
						return true;
					}
				}
				return false;
			},
			login: function (newUser) {
				_user = newUser;
				$cookieStore.put('current.user', newUser);
				authService.loginConfirmed();
				$rootScope.$broadcast(this.LOGIN_EVENT);
			},
			logout: function() {
				_user = null
				$cookieStore.remove('current.user', _user);
				$rootScope.$broadcast(this.LOGOUT_EVENT);
			}
		};
	}
);

// end anonymous function
})();