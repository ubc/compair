// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.course', ['ngResource']);

/***** Providers *****/
module.factory('CourseResource', function($resource) {
	return $resource('/api/courses/:id', {id: '@id'});
});

/***** Controllers *****/
module.controller(
	'CourseController',
	function($scope, $log, CourseResource)
	{
		$scope.newCourseSubmit = function() {
			$scope.submitted = true;
			CourseResource.save($scope.course).$promise.then(
				function (ret)
				{
					$scope.submitted = false;
					// TODO REDIRECT TO NEWLY CREATED COURSE
				},
				function (ret)
				{
					$scope.submitted = false;
					$scope.courseErr = ret.data.error
				}
			);
		};
	}
);

// End anonymous function
})();
