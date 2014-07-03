// Handles answer creation and editing.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.answer', 
	[
		'ngResource',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"AnswerResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/questions/:questionId/answers/:answerId',
			{answerId: '@id'}
		);
		ret.MODEL = "PostsForAnswers";
		return ret;
	}
);

/***** Controllers *****/
module.controller(
	"AnswerCreateController",
	function ($scope, $log, $location, $routeParams, AnswerResource, 
		QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];

		$scope.question = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).
			$promise.then(
				function (ret)
				{
					$scope.question = ret;
				},
				function (ret)
				{
					Toaster.reqerror("Unable to load question.", ret);
				}
			);

		$scope.answer = {};
		$scope.answerSubmit = function () {
			$scope.submitted = true;
			AnswerResource.save({'courseId': courseId, 'questionId': questionId},
				$scope.answer).$promise.then(
					function (ret)
					{
						$scope.submitted = false;
						Toaster.success("New answer posted!");
						$location.path('/course/' + courseId + '/question/' +
							questionId);
					},
					function (ret)
					{
						$scope.submitted = false;
						Toaster.reqerror("Unable to post new answer.", ret);
						$log.debug("Test");
						$log.debug(ret);
					}
				);
		};
	}
);

// End anonymous function
})();
