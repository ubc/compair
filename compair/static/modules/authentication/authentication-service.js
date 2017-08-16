(function() {

// the module needs a unique name that prevents conflicts with 3rd party modules
var module = angular.module(
    'ubc.ctlt.compair.authentication',
    [
        'ngResource',
        'http-auth-interceptor'
    ]
);

module.factory('AuthenticationService',
    ["$rootScope", "$http", "$q", "authService", "Session",
    function ($rootScope, $http, $q, authService, Session) {
        var LOGIN_EVENT = "event:Authentication-Login";
        var LOGOUT_EVENT = "event:Authentication-Logout";

        return {
            // Use these constants to listen to login or logout events.
            LOGIN_EVENT: LOGIN_EVENT,
            LOGOUT_EVENT: LOGOUT_EVENT,
            LOGIN_REQUIRED_EVENT: "event:auth-loginRequired",
            LTI_LOGIN_REQUIRED_EVENT: "event:auth-ltiLoginRequired",
            LOGIN_FORBIDDEN_EVENT: "event:auth-forbidden",
            AUTH_LOGIN_REQUIRED_EVENT: "event:auth-authLoginRequired",
            isAuthenticated: function() {
                return Session.getUser().then(function(result) {
                    if (result) {
                        return $q.when(true);
                    }

                   return $q.when(false);
                });
            },
            login: function (skipRetry) {
                skipRetry = skipRetry || false;

                Session.destroy();
                return Session.getUser().then(function() {
                    authService.loginConfirmed('success', function(config) {
                        if (skipRetry) {
                            return false;
                        }
                        return config;
                    });
                    $rootScope.$broadcast(LOGIN_EVENT);
                });
            },
            logout: function() {
                Session.destroy();
                $rootScope.$broadcast(LOGOUT_EVENT);
            }
        };
    }
]);

// end anonymous function
})();
