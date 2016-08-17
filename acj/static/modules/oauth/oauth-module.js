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
    'ubc.ctlt.acj.authorization',
    'ubc.ctlt.acj.toaster'
]);

/***** Controllers *****/
module.controller("OAuthController",
    ['$rootScope', '$scope', '$log', '$route', '$routeParams', '$location', 'breadcrumbs', 'Session',
     'UserResource', 'Authorize', 'SystemRole', 'Toaster', 'LTI', 'AuthenticationService',
    function($rootScope, $scope, $log, $route, $routeParams, $location, breadcrumbs, Session,
             UserResource, Authorize, SystemRole, Toaster, LTI, AuthenticationService) {

        var userId;
        var self = this;
        var messages = {
            new: {title: 'New User Created', msg: 'User should now have access.'},
            edit: {title: 'User Successfully Updated', msg: 'Your changes were saved.'}
        };
        $scope.user = {};
        $scope.method = 'new';
        $scope.password = {};
        $scope.system_roles = [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]
        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;
        });
        $rootScope.$emit(AuthenticationService.AUTH_REQUIRED_EVENT);
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
