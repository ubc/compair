// Controls the home page for this application, which is mainly just a listing
// of courses which this user is enroled in.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.home',
    [
        'ngSanitize',
        'ubc.ctlt.acj.authentication',
        'ubc.ctlt.acj.authorization',
        'ubc.ctlt.acj.course',
        'ubc.ctlt.acj.toaster',
        'ubc.ctlt.acj.user'
    ]
);

/***** Providers *****/
// module.factory(...)

/***** Controllers *****/
module.controller(
    'HomeController',
    ["$rootScope", "$scope", "$location", "Session", "AuthenticationService",
     "Authorize", "CourseResource", "Toaster", "UserResource",
    function ($rootScope, $scope, $location, Session, AuthenticationService,
              Authorize, CourseResource, Toaster, UserResource) {

        $scope.loggedInUserId = null;
        $scope.totalNumCourses = 0;
        $scope.courseFilters = {
            page: 1,
            perPage: 10,
            search: null
        };

        Authorize.can(Authorize.CREATE, CourseResource.MODEL).then(function(canAddCourse){
            $scope.canAddCourse = canAddCourse;
        });

        Session.getUser().then(function(user) {
            $scope.loggedInUserId = user.id;
            $scope.updateCourseList();

            // register watcher here so that we start watching when all filter values are set
            $scope.$watchCollection('courseFilters', filterWatcher);
        });

        $scope.updateCourseList = function() {
            UserResource.getUserCourses($scope.courseFilters).$promise.then(
                function(ret) {
                    $scope.courses = ret.objects;
                    $scope.totalNumCourses = ret.total;
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve your courses.", ret);
                }
            );
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.search != newValue.search) {
                $scope.courseFilters.page = 1;
            }
            if(newValue.search === "") {
                $scope.courseFilters.search = null;
            }
            $scope.updateCourseList();
        };
    }
]);
// End anonymous function
})();
