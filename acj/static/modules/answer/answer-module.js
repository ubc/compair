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
			{answerId: '@id'},
			{
				flagged: {
					method: 'POST', 
					url: '/api/courses/:courseId/questions/:questionId/answers/:answerId/flagged'
				}
			}
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
					$scope.question = ret.question;
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

module.controller(
	"AnswerEditController",
	function ($scope, $log, $location, $routeParams, AnswerResource, 
		QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		$scope.answerId = $routeParams['answerId'];
		
		$scope.question = {};
		$scope.answer = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret) {
				$scope.question = ret.question;	
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve question "+questionId, ret);
			}
		);
		AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': $scope.answerId}).$promise.then(
			function (ret) {
				$scope.answer = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);
		$scope.answerSubmit = function () {
			AnswerResource.save({'courseId': courseId, 'questionId': questionId}, $scope.answer).$promise.then(
				function() { 
					Toaster.success("Answer Updated!");
					$location.path('/course/' + courseId + '/question/' +questionId);
					
				},
				function(ret) { Toaster.reqerror("Answer Save Failed.", ret); }
			);
		};
	}
);

module.controller(
	"AnswerDeleteController",
	function ($scope, $log, $location, $routeParams, AnswerResource, 
		Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		var answerId = $routeParams['answerId'];
		AnswerResource.delete({'courseId':courseId, 'questionId':questionId, 'answerId':answerId}).$promise.then(
			function (ret) {
				Toaster.success("Successfully deleted answer "+ ret.id);
				$location.path('/course/'+courseId+'/question/'+questionId);
			},
			function (ret) {
				Toaster.reqerror("Answer deletion failed", ret);
				$location.path('/course/'+courseId+'/question/'+questionId);
			}
		);
	}
);

// End anonymous function
})();

