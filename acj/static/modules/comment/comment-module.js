// Handles comment creation and editing.

(function() {

var module = angular.module('ubc.ctlt.acj.comment',
	[
		'ngResource',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"QuestionCommentResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/questions/:questionId/comments/:commentId',
			{commentId: '@id'}
		);
		ret.MODEL = "PostsForQuestionsAndPostsForComments";
		return ret;
	}
);

module.factory(
	"AnswerCommentResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/questions/:questionId/answers/:answerId/comments/:commentId',
			{commentId: '@id'}
		);
		ret.MODEL = "PostsForAnswersAndPostsForComments";
		return ret;
	}
);

/***** Controllers *****/
module.controller(
	"QuestionCommentCreateController",
	function ($scope, $log, $location, $routeParams, QuestionCommentResource, QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
	
		$scope.comment = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function(ret) {
				$scope.parent = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the question "+questionId, ret);
			}
		);
		$scope.commentSubmit = function () {
			$scope.submitted = true;
			QuestionCommentResource.save({'courseId': courseId, 'questionId': questionId},
				$scope.comment).$promise.then(
					function (ret)
					{
						$scope.submitted = false;
						Toaster.success("New comment posted!");
						$location.path('/course/'+courseId+'/question/'+questionId);
					},
					function (ret)
					{
						$scope.submitted = false;
						Toaster.reqerror("Unable to post new comment.", ret);
					}
				);
		};
	}
);

module.controller(
	"QuestionCommentEditController",
	function ($scope, $log, $location, $routeParams, QuestionCommentResource, QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		var commentId = $routeParams['commentId'];

		$scope.comment = {};
		$scope.parent = {}; // question
		QuestionCommentResource.get({'courseId': courseId, 'questionId': questionId, 'commentId': commentId}).$promise.then(
			function(ret) {
				$scope.comment = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve comment "+commentId, ret);
			}
		);
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function(ret) {
				$scope.parent = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the question "+questionId, ret);
			}
		);
		$scope.commentSubmit = function () {
			QuestionCommentResource.save({'courseId': courseId, 'questionId': questionId}, $scope.comment).$promise.then(
				function() { 
					Toaster.success("Comment Updated!");
					$location.path('/course/' + courseId + '/question/' +questionId);
				},
				function(ret) { Toaster.reqerror("Comment Save Failed.", ret);}
			);
		};
	}
);

module.controller(
	"AnswerCommentCreateController",
	function ($scope, $log, $location, $routeParams, AnswerCommentResource, AnswerResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		var answerId = $routeParams['answerId'];

		$scope.comment = {};
		AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerId}).$promise.then(
			function (ret) {
				$scope.parent = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);
		$scope.commentSubmit = function () {
			$scope.submitted = true;
			AnswerCommentResource.save({'courseId': courseId, 'questionId': questionId, 'answerId': answerId},
				$scope.comment).$promise.then(
					function (ret)
					{
						$scope.submitted = false;
						Toaster.success("New comment posted!");
						$location.path('/course/'+courseId+'/question/'+questionId);
					},
					function (ret)
					{
						$scope.submitted = false;
						Toaster.reqerror("Unable to post new comment.", ret);
					}
				);
		};	
	}
);

module.controller(
	"AnswerCommentEditController",
	function ($scope, $log, $location, $routeParams, AnswerCommentResource, AnswerResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		var answerId = $routeParams['answerId'];
		var commentId = $routeParams['commentId'];

		$scope.comment = {};
		$scope.parent = {}; // answer
		AnswerCommentResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerId, 'commentId': commentId}).$promise.then(
			function(ret) {
				$scope.comment = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve comment "+commentId, ret);
			}
		);
		AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerId}).$promise.then(
			function (ret) {
				$scope.parent = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);
		$scope.commentSubmit = function () {
			AnswerCommentResource.save({'courseId': courseId, 'questionId': questionId, 'answerId': answerId}, $scope.comment).$promise.then(
				function() {
					Toaster.success("Comment Updated!");
					$location.path('/course/' + courseId + '/question/' +questionId);
				},
				function(ret) { Toaster.reqerror("Comment Save Failed.", ret);}
			);
		};
	}
);

// End anonymouse function
}) ();
