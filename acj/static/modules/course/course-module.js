// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.course', 
	[
		'angularMoment',
		'ngResource', 
		'ngRoute',
		'ckeditor',
		'ng-breadcrumbs',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory('CourseResource', function($resource) {
	var ret = $resource('/api/courses/:id', {id: '@id'},
		{
			getQuestions: {url: '/api/courses/:id/questions'}
		}
	)
	ret.MODEL = "Courses"; // add constant to identify the model
						// being used, this is for permissions checking
						// and should match the server side model name
	return ret;
});

/***** Controllers *****/
module.controller(
	'CourseQuestionsController',
	function($scope, $log, $routeParams, breadcrumbs, CourseResource, Toaster)
	{
		$scope.courseId = $routeParams['courseId'];
		// get course record
		CourseResource.get({'id': $scope.courseId}).$promise.then(
			function (ret)
			{
				$scope.course = ret;
				// update breadcrumbs with course name
				breadcrumbs.options = {'Course Questions': $scope.course.name};
			},
			function (ret)
			{
				Toaster.reqerror("Unable to retrieve course: "+ $scope.courseId);
			}
		);
		// get course questions
		CourseResource.getQuestions({'id': $scope.courseId}).$promise.then(
			function (ret)
			{
				$scope.questions = ret.questions;
			},
			function (ret)
			{
				Toaster.reqerror("Unable to retrieve course questions: " +
					$scope.courseId);
			}
		);

	}
);

module.controller(
	'CourseCreateController',
	function($scope, $log, $location, CourseResource, Toaster)
	{
		$scope.editorOptions = 
		{
			language: 'en',
			disableInline: true,
			removeButtons: 'Anchor,Strike,Subscript,Superscript',
			toolbarGroups: [
				{ name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
				{ name: 'links' }
			]
		};
		$scope.newCourseSubmit = function() {
			$scope.submitted = true;
			CourseResource.save($scope.course).$promise.then(
				function (ret)
				{
					$scope.submitted = false;
					Toaster.success(ret.name + " created successfully!");
					$location.path('/course/' + ret.id);
				},
				function (ret)
				{
					$scope.submitted = false;
					Toaster.error(ret.data.error);
				}
			);
		};
	}
);

// End anonymous function
})();
