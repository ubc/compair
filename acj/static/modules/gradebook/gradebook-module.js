// Shows the instructor summary of student participations by question

// Isolate this module's creation by putting it in an anonymous function
(function() {

// TODO 
// Create the module with a unique name.
// The module needs a unique name that prevents conflicts with 3rd party modules
// We're using "ubc.ctlt.acj" as the project's prefix, followed by the module 
// name.
var module = angular.module('ubc.ctlt.acj.gradebook', 
	[
		'ngResource',
		'ngRoute',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	'GradebookResource',
	function($resource)
	{
		var ret = $resource('/api/courses/:courseId/questions/:questionId/gradebook');
		return ret;
	}
);

/***** Controllers *****/
module.controller("GradebookController",
	function($scope, $log, $routeParams, CourseResource, GradebookResource, 
		Toaster) 
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		CourseResource.getQuestions({'id': courseId}).$promise.then(
			function (ret)
			{
				$scope.questions = ret.questions;
			},
			function (ret)
			{
				Toaster.reqerror("Unable to retrieve course questions: " +
					courseId, ret);
			}
		);

		$scope.changeQuestion = function(questionId) {
			GradebookResource.get(
				{'courseId': courseId,'questionId': questionId}).$promise.then(
				function(ret) 
				{
					$scope.gradebook = ret['gradebook'];
					$scope.numJudgementsRequired=ret['num_judgements_required'];
				},
				function (ret)
				{
					$scope.gradebook = [];
				}
			);
		};

	}
);

// End anonymous function
})();
