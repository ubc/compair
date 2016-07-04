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
    ["$rootScope", "$scope", "$location", "$log",
     "Session", "AuthenticationService", "Authorize", "CourseResource", "Toaster", "UserResource",
	function HomeController($rootScope, $scope, $location, $log,
                            Session,
							AuthenticationService,
							Authorize,
							CourseResource,
							Toaster,
							UserResource) {
        Authorize.can(Authorize.CREATE, CourseResource.MODEL).then(function(canAddCourse){
            $scope.canAddCourse = canAddCourse;
        });
        Session.getUser().then(function(user) {
            UserResource.getUserCourses(
                {id: user.id}).$promise.then(
                function(ret) {
                    $scope.courses = ret.objects;
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve your courses.", ret);
                    $log.error("Failed to retrieve the user's courses.");
                }
            );
        });
	}
]);
// End anonymous function
})();
