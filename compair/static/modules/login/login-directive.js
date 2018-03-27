(function () {
    'use strict';

    angular
        .module('ubc.ctlt.compair.login')

        .directive('loginCreateUserForm',
            ['$route', '$log', 'UserResource', 'SystemRole', 'Toaster', 'AuthTypesEnabled',
             'AuthenticationService', 'LTI', 'UserSettings', 'EmailNotificationMethod',
            function ($route, $log, UserResource, SystemRole, Toaster, AuthTypesEnabled,
                      AuthenticationService, LTI, UserSettings, EmailNotificationMethod) {
            return {
                restrict: 'E',
                scope: {
                    uses_compair_login: '=usesCompairLogin'
                },
                templateUrl: 'modules/user/user-form-partial.html',
                link: function (scope, element, attrs) {
                    scope.method = 'create';
                    scope.canManageUsers = false;
                    scope.submitted = false;

                    scope.password = {};
                    scope.UserSettings = UserSettings;
                    scope.EmailNotificationMethod = EmailNotificationMethod;
                    scope.AuthTypesEnabled = AuthTypesEnabled;
                    scope.SystemRole = SystemRole;
                    scope.system_roles = [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin];

                    scope.user = {
                        // required parameter that will be ignored by backend
                        system_role: SystemRole.student,
                        uses_compair_login: scope.uses_compair_login,
                        email_notification_method: EmailNotificationMethod.enable
                    }
                    scope.loggedInUserIsStudent = true;

                    LTI.getStatus().then(function(status) {
                        // check if LTI session
                        if (LTI.isLTISession()) {
                            // overwrite user with LTI user info
                            scope.user = LTI.getLTIUser();
                            scope.user.uses_compair_login = scope.uses_compair_login;
                            scope.user.email_notification_method = EmailNotificationMethod.enable;
                            scope.loggedInUserIsStudent = scope.user.system_role == SystemRole.student;
                        }
                    });

                    scope.save = function() {
                        scope.submitted = true;

                        UserResource.save({}, scope.user, function(ret) {
                            Toaster.success("User Setup Complete");
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