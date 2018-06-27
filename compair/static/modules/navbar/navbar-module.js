// Module for the main navbar at the top of the application.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.navbar',
    [
        'ng-breadcrumbs',
        'ngRoute',
        'ubc.ctlt.compair.login',
        'ubc.ctlt.compair.authentication',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.login', // for LogoutController
        'ubc.ctlt.compair.assignment',
        'ubc.ctlt.compair.user',
        'ubc.ctlt.compair.studentview',
    ]
);

/***** Controllers *****/
module.component('navbarComponent', {
    controller: 'NavbarController',
    templateUrl: 'modules/navbar/navbar-partial.html'
});

module.controller(
    "NavbarController",
    ["$scope", "$log", "$routeParams", "breadcrumbs", "AuthTypesEnabled",
        "Session", "AuthenticationService", "Authorize", "CourseResource", "UserResource",
        "AssignmentResource", "$rootScope", "$uibModal", "ImpersonationSettings",
        "LearningRecordStatementHelper", "Toaster",
    function NavbarController($scope, $log, $routeParams, breadcrumbs, AuthTypesEnabled,
        Session, AuthenticationService, Authorize, CourseResource, UserResource,
        AssignmentResource, $rootScope, $uibModal, ImpersonationSettings,
        LearningRecordStatementHelper, Toaster)
    {
        $scope.breadcrumbs = breadcrumbs;
        $scope.isCollapsed = true;
        $scope.AuthTypesEnabled = AuthTypesEnabled;

        // determine if we're in a course so we know whether to show
        // the course settings
         $scope.getPermissions = function() {
            Session.getUser().then(function(user) {
                $scope.loggedInUser = user;
                $log.debug("Logged in as " + $scope.loggedInUser.username);

                Authorize.can(Authorize.CREATE, UserResource.MODEL).then(function (result) {
                    $scope.canCreateUsers = result;
                });
                Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function (result) {
                    $scope.canManageUsers = result;
                });
                Authorize.can(Authorize.CREATE, CourseResource.MODEL).then(function (result) {
                    $scope.canCreateCourses = result;
                });
                Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL).then(function (result) {
                    $scope.canManageAssignments = result;
                });
                // anyone that can create courses can use student view
                Authorize.can(Authorize.CREATE, CourseResource.MODEL).then(function (result) {
                    $scope.canStartStudentView = result;
                });
            });
        };
        $scope.setInCourse = function() {
            $scope.courseId = $routeParams.courseId;
            if ($scope.courseId) {
                // update breadcrumb to show the course name
                CourseResource.get({'id': $scope.courseId}).$promise.then(
                    function(ret)
                    {
                        breadcrumbs.options = {'Course Assignments': ret['name']};
                    }
                );
            }
        };
        $scope.setInCourse(); // init for first page load
        $scope.$on('$routeChangeSuccess', function(event, next) {
            // update for further navigation after the page has loaded
            $scope.setInCourse();
        });

        $scope.getPermissions();
        $scope.$on(AuthenticationService.LOGIN_EVENT, function() {
            $scope.getPermissions();
        });
        $scope.$on(Session.PERMISSION_REFRESHED_EVENT, function() {
            $scope.getPermissions();
        });

        $scope.showLogin = function() {
            $scope.$emit(AuthenticationService.LOGIN_REQUIRED_EVENT);
        };

        $scope.impersonationEnabled = ImpersonationSettings.enabled;
        $scope.getImpersonation = function() {
            Session.getImpersonation().then(function (impersonate_details) {
                $scope.impersonating = impersonate_details && impersonate_details.impersonating;
                if ($scope.impersonating &&
                    impersonate_details.original_user && impersonate_details.original_user.displayname) {
                    $scope.impersonate_original_user_name = impersonate_details.original_user.displayname;
                } else {
                    $scope.impersonate_original_user_name = '';
                }

                if ($scope.impersonating) {
                    $scope.impersonate_as_user_name = '';
                    Session.getUser().then(function (user) {
                        $scope.impersonate_as_user_name = ((user.firstname || '') + ' ' + (user.lastname || '')).trim();
                    });
                }
            }).catch(function() {
                $scope.impersonating = false;
                $scope.impersonate_original_user_name = '';
                $scope.impersonate_as_user_name = '';
            });
        };
        $scope.getImpersonation();
        $scope.$on(Session.IMPERSONATE_START_EVENT, function() {
            $scope.getImpersonation();
            $scope.getPermissions();
        });
        $scope.$on(Session.IMPERSONATE_END_EVENT, function() {
            $scope.impersonating = false;
            $scope.impersonate_original_user_name = '';
            $scope.impersonate_as_user_name = '';
            $scope.getImpersonation();
            $scope.getPermissions();
        });
        $scope.stop_impersonate = function() {
            // clear dirty state so the user wont be asked for confirmation
            angular.forEach(angular.element(".ng-dirty"), function(elm) {
                if ($(elm).is('form')) {
                    var controller = angular.element(elm).controller('form');
                    if (controller) {
                        controller.$setPristine();
                    }
                }
            });

            Session.stop_impersonate($routeParams.courseId);
            Toaster.success("Student View Closed", 'You are now viewing ComPAIR as yourself again.');
        };
        $scope.selectStudentView = function() {
            var modalScope = $scope.$new();
            modalScope.currentCourseId = $scope.courseId;

            $scope.modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "StudentViewController",
                templateUrl: 'modules/student_view/student-view-modal-partial.html',
                scope: modalScope
            });
            $scope.modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal("Student View");
            });
            $scope.modalInstance.result.finally(function () {
                LearningRecordStatementHelper.closed_modal("Student View");
            });
        }
    }
]);

// End anonymous function
})();
