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
	function ($rootScope, $resource, $cookieStore, $log, $http, $q, authService, Session) {
		return {
			// Use these constants to listen to login or logout events.
			LOGIN_EVENT: "event:Authentication-Login",
			LOGOUT_EVENT: "event:Authentication-Logout",
			LOGIN_REQUIRED_EVENT: "event:auth-loginRequired",
			isAuthenticated: function() {
                return Session.getUser().then(function(result) {
                    if (result) {
                        return $q.when(true);
                    }

                   return $q.when(false);
                });
			},
			login: function () {
                return Session.getUser().then(function() {
                    authService.loginConfirmed();
                    $rootScope.$broadcast(this.LOGIN_EVENT);
                });
			},
			logout: function() {
                Session.destroy();
				$rootScope.$broadcast(this.LOGOUT_EVENT);
			}
		};
	}
);

// end anonymous function
})();
