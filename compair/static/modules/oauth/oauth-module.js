// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.oauth', [
    'ngResource',
    'ngRoute',
    'ng-breadcrumbs',
    'ubc.ctlt.acj.session',
    'ubc.ctlt.acj.authorization'
]);

module.constant('ThirdPartyAuthType', {
    cwl: "CWL"
});

/***** Controllers *****/
module.controller("OAuthController",
    ['$rootScope', '$scope', '$route', '$location', 'breadcrumbs', 'Session', 'LTI', 'AuthenticationService',
    function($rootScope, $scope, $route, $location, breadcrumbs, Session, LTI, AuthenticationService) {

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
