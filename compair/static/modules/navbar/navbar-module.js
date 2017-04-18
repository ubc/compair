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
        'ubc.ctlt.compair.user'
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
        "Session", "AuthenticationService", "Authorize", "CourseResource", "UserResource", "AssignmentResource",
    function NavbarController($scope, $log, $routeParams, breadcrumbs, AuthTypesEnabled,
        Session, AuthenticationService, Authorize, CourseResource, UserResource, AssignmentResource)
    {
        $scope.breadcrumbs = breadcrumbs;
        $scope.isCollapsed = true;
        $scope.AuthTypesEnabled = AuthTypesEnabled;

        $scope.AuthTypesEnabled = AuthTypesEnabled;

        // determine if we're in a course so we know whether to show
        // the course settings
        $scope.getPermissions = function() {
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
        };
        $scope.setInCourse = function() {
            var courseId = $routeParams.courseId;
            if (courseId) {
                // update breadcrumb to show the course name
                CourseResource.get({'id': courseId}).$promise.then(
                    function(ret)
                    {
                        breadcrumbs.options = {'Course Assignments': ret['name']};
                    }
                );
            }
            $scope.courseId = courseId;
        };
        $scope.setInCourse(); // init for first page load
        $scope.$on('$locationChangeSuccess', function(event, next) {
            // update for further navigation after the page has loaded
            $scope.setInCourse();
        });
        Session.getUser().then(function(user) {
            $scope.loggedInUser = user;
            $log.debug("Logged in as " + $scope.loggedInUser.username);
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
    }
]);

// End anonymous function
})();
