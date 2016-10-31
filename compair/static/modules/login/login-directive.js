(function () {
    'use strict';

    angular
        .module('ubc.ctlt.compair.login')

        .directive('loginCreateUserForm',
            ['$route', '$log', 'Session', 'UserResource', 'SystemRole', 'Toaster',
             'AuthenticationService', 'LTI',
            function ($route, $log, Session, UserResource, SystemRole, Toaster,
                      AuthenticationService, LTI) {
            return {
                restrict: 'E',
                scope: {
                    uses_compair_login: '=usescompairLogin'
                },
                templateUrl: 'modules/user/user-form-partial.html',
                link: function (scope, element, attrs) {
		        scope.method = 'new';
                    scope.canManageUsers = false;
                    scope.submitted = false;

                    scope.password = {};
                    scope.SystemRole = SystemRole;
                    scope.system_roles = [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin];

                    scope.user = {
                        // required parameter that will be ignored by backend
                        system_role: SystemRole.student,
                        uses_compair_login: scope.uses_compair_login
                    }

                    LTI.getStatus().then(function(status) {
                        // check if LTI session
                        if (LTI.isLTISession()) {
                            // overwrite user with LTI user info
                            scope.user = LTI.getLTIUser();
                            scope.user.uses_compair_login = scope.uses_compair_login;
                        }
                    });

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