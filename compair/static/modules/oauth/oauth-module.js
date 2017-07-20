// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.oauth', [
    'ngResource',
    'ngRoute',
    'ubc.ctlt.compair.session',
    'ubc.ctlt.compair.authorization'
]);

module.constant('ThirdPartyAuthType', {
    cas: "CAS"
});

/***** Controllers *****/
module.controller("OAuthController",
    ['$rootScope', '$scope', '$route', '$location', 'Session', 'LTI',
     'AuthenticationService', 'resolvedData',
    function($rootScope, $scope, $route, $location, Session, LTI,
             AuthenticationService, resolvedData) {

        $rootScope.$emit(AuthenticationService.AUTH_LOGIN_REQUIRED_EVENT);
        Session.getUser().then(function(user) {
            if (LTI.isLTISession()) {
                $location.path("/lti");
            } else {
                $location.path("/"); //redirect user to home screen
            }
        });
    }]
);
// End anonymous function
})();
