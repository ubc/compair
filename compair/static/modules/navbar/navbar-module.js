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
module.controller(
    "NavbarController",
    ["$scope", "$log", "$route", "breadcrumbs", "AuthTypesEnabled",
        "Session", "AuthenticationService", "Authorize", "CourseResource", "UserResource", "AssignmentResource",
    function NavbarController($scope, $log, $route, breadcrumbs, AuthTypesEnabled,
        Session, AuthenticationService, Authorize, CourseResource, UserResource, AssignmentResource)
    {
        $scope.breadcrumbs = breadcrumbs;
        $scope.isLoggedIn = false;
        $scope.isCollapsed = true;

        $scope.AuthTypesEnabled = AuthTypesEnabled;

        // determine if we're in a course so we know whether to show
        // the course settings
        //$scope.inCourse = false;
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
            var courseId = $route.current.params['courseId'];
            $scope.inCourse = false;
            if (courseId) {
                $scope.inCourse = true;
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
        // show course configure options if user can edit courses
        /*Authorize.can(Authorize.EDIT, CourseResource.MODEL).then(function(result) {
            $scope.canEditCourse = result;
        })*/
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

        // listen for changes in authentication state
//		$scope.$on(AuthenticationService.LOGIN_EVENT, updateAuthentication);
//		$scope.$on(AuthenticationService.LOGOUT_EVENT, updateAuthentication);

        $scope.showLogin = function() {
            $scope.$emit(AuthenticationService.LOGIN_REQUIRED_EVENT);
        };

        // TODO Not sure what listening to comparison, steps do
        $scope.$on("COMPARISON", function(event) {
            route = $scope.breadcrumb[$scope.breadcrumb.length - 1].link ? $scope.breadcrumb[$scope.breadcrumb.length - 1].link : "";
            $location.path(route.replace("#/", ""));
        });
        var steps = '';
        $scope.$on("STEPS", function(event, val) {
            $scope.hastutorial = true;
            steps = val.steps;
            var intro = val.intro;
            steps.unshift({element: '#stepTutorial', intro: intro});
        });
    }
]);

// End anonymous function
})();
