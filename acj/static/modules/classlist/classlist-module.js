// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.classlist',
	[
		'ngResource',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"ClassListResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/users'
		);
		ret.MODEL = "CoursesAndUsers";
		return ret;
	}
);

/***** Controllers *****/
module.controller(
	'ClassViewController',
	function($scope, $log, $routeParams, ClassListResource, CourseResource, Toaster)
	{
		$scope.course = {};
		$scope.classlist = {};
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve course: "+courseId, ret);
			}
		);
		ClassListResource.get({'courseId':courseId}).$promise.then(
			function (ret) {
				$scope.classlist = ret.objects;
				console.log($scope.classlist);
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve class list for course: "+courseId, ret);
			}
		);
	}
);

// End anonymous function
})();
