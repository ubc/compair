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
		'ubc.ctlt.acj.user'
	]
);

/***** Providers *****/
// module.factory(...)

/***** Controllers *****/
module.controller(
	'HomeController',
	function HomeController($rootScope, $scope, $location, $log,
							AuthenticationService,
							Authorize,
							CourseResource,
							UserResource) {
		$scope.canAddCourse = 
			Authorize.can(Authorize.CREATE, CourseResource.MODEL);
		UserResource.getUserCourses(
			{id: AuthenticationService.getUser().id}).$promise.then(
			function(ret) {
				$scope.courses = ret.objects;
				for (var i = 0; i < $scope.courses.length; i++) {
					courseanduser = $scope.courses[i];
				}
			},
			function (ret) {
				$log.error("Failed to retrieve the user's courses.");
			}
		);

		$scope.submit = function() {
			input = {"name": $scope.course};
			var retval = courseService.save( input, function() {
				$scope.check = false;
				$scope.flash = retval.flash;
				if (!$scope.flash) {
					$scope.courses.push(retval);
				}
				else {
					flashService.flash('danger', retval.flash);
				}
			});
		};
		$scope.redirect = function(url) {
			$location.path(unescape(url));
		};
	}
);
// End anonymous function
})();
