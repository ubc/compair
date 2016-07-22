(function () {
    'use strict';

    angular
        .module('ubc.ctlt.acj.login')

        .directive('loginCreateUserForm',
            ['$route', '$log', 'Session', 'UserResource', 'SystemRole', 'Toaster',
             'AuthenticationService',
            function ($route, $log, Session, UserResource, SystemRole, Toaster,
                      AuthenticationService) {
            return {
                restrict: 'E',
                templateUrl: 'modules/user/user-form-partial.html',
                link: function (scope, element, attrs) {
        	        scope.method = 'new';
                    scope.canManageUsers = false;
                    scope.submitted = false;
                    scope.user = {
                        //required parameter that will be ignored by backendup
                        system_role: SystemRole.student
                    };
                    scope.password = {};
                    scope.system_roles = [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin];

                    scope.save = function() {
                        scope.submitted = true;

                        UserResource.save({}, scope.user, function(ret) {
                            Toaster.success("Account Setup Complete", "You have successfully completed setting up your ComPAIR account.");
                            AuthenticationService.login().then(function() {
                                scope.submitted = false;
                                $route.reload();
                            }, function() {
                                $log.error("Failed to retrieve logged in user's data: " + JSON.stringify(ret));
                                scope.submitted = false;
                            });
                        }).$promise.finally(function() {
                            scope.submitted = false;
                        });
                    };
                }
            }
        }]);
})();