// Provides the services and controllers for questions.
//
(function() {

var module = angular.module('ubc.ctlt.acj.question', 
	[
		'ngResource',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"QuestionResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/questions/:questionId', 
			{questionId: '@id'}
		);
		ret.MODEL = "PostsForQuestions";
		return ret;
	}
);

/***** Controllers *****/
module.controller("QuestionCreateController",
	function($scope, $log, $location, $routeParams, QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		$scope.question = {};
		$scope.questionSubmit = function () {
			$scope.submitted = true;
			QuestionResource.save({'courseId': courseId}, $scope.question).
				$promise.then(
					function (ret)
					{
						$scope.submitted = false;
						Toaster.success("New Question Created!", 
							'"' + ret.title + '" should now be listed.');
						$location.path('/course/' + courseId);
					},
					function (ret)
					{
						$scope.submitted = false;
						Toaster.reqerror("Unable to create new question.");
					}
				);
		};
	}
);

// End anonymous function
})();
