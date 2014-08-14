// Provides the services and controllers for questions.
//
(function() {

var module = angular.module('ubc.ctlt.acj.question', 
	[
		'ngResource',
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.authentication',
		'ubc.ctlt.acj.authorization',
		'ubc.ctlt.acj.comment',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
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

/***** Filters *****/
module.filter("notScoredEnd", function () {
	return function (array, key) {
		if (!angular.isArray(array)) return;
		var scored = array.filter(function(item) {
			return item.scores[key]
		});
		var not_scored = array.filter(function(item) {
			return !item.scores[key]
		});
		return scored.concat(not_scored);
	}
});

/***** Controllers *****/
module.controller("QuestionViewController",
	function($scope, $log, $routeParams, AnswerResource, AuthenticationService, Authorize, QuestionResource, QuestionCommentResource, Toaster)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		$scope.loggedInUserId = AuthenticationService.getUser().id;
		$scope.canManagePosts = 
			Authorize.can(Authorize.MANAGE, QuestionResource.MODEL);
		$scope.question = {};
		QuestionResource.get({'courseId': $scope.courseId, 
			'questionId': questionId}).$promise.then(
				function (ret)
				{
					$scope.question = ret.question;
					$scope.criteria = ret.criteria;
					$scope.sortby = '0';
					$scope.order = 'scores.'+$scope.sortby+'.score';
					$scope.answers = ret.question.answers;
					$scope.reverse = true;

					$scope.answered = ret.answers > 0 ? true:false;
				},
				function (ret)
				{
					Toaster.reqerror("Unable to retrieve question "
						+ questionId, ret);
				}
			);
		QuestionCommentResource.get({'courseId': $scope.courseId,
			'questionId': questionId}).$promise.then(
				function (ret)
				{
					$scope.comments = ret.objects;
				},
				function (ret)
				{
					Toaster.reqerror("Unable to retrieve comments.", ret);
				}
			);
	}
);
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
						Toaster.reqerror("Unable to create new question.", ret);
					}
				);
		};
	}
);

module.controller("QuestionEditController",
	function($scope, $log, $location, $routeParams, QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		$scope.questionId = $routeParams['questionId'];
		$scope.question = {};
		QuestionResource.get({'courseId': courseId, 'questionId': $scope.questionId}).$promise.then(
			function (ret) {
				$scope.question = ret.question;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve question "+$scope.questionId, ret);
			}
		);
		$scope.questionSubmit = function () {
			QuestionResource.save({'courseId': courseId}, $scope.question).$promise.then(
				function() { 
					Toaster.success("Question Updated!");
					$location.path('/course/' + courseId);
				 },
				function(ret) { Toaster.reqerror("Question Save Failed.", ret); }
			);
		};
	}
);
// End anonymous function
})();
