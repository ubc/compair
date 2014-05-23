// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

// TODO 
// Create the module with a unique name.
// The module needs a unique name that prevents conflicts with 3rd party modules
// We're using "ubc.ctlt.acj" as the project's prefix, followed by the module 
// name.
var module = angular.module('ubc.ctlt.acj.home',
	[
		'ubc.ctlt.acj.authentication',
		'ubc.ctlt.acj.authorization',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.user'
	]
);

/***** Providers *****/
// TODO declare providers here, e.g.:
// module.factory(...)

/***** Controllers *****/
module.controller(
	'HomeController',
	function HomeController($rootScope, $scope, $location, $log,
							AuthenticationService,
							Authorize,
							CourseResource,
							UserResource) {
		$rootScope.breadcrumb = [{'name':'Home'}];


		$scope.canAddCourse = false;
		if (Authorize.can(Authorize.CREATE, CourseResource.MODEL)) {
			$log.debug("User has permission to add courses.");
			$scope.canAddCourse = true;
		}
		UserResource.getUserCourses({id: AuthenticationService.getUser().id}).$promise.then(
			function(ret) {
				$log.debug("Retrieved the logged in user's courses.");
				$log.debug(ret);
				$scope.courses = ret.objects;
				$log.debug($scope.courses);
				for (var i = 0; i < $scope.courses.length; i++) {
					courseanduser = $scope.courses[i];
				}
			},
			function (ret) {
				$log.debug("Failed to retrieve the user's courses.");
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
