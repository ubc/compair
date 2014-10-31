// Handles comment creation and editing.

(function() {

var module = angular.module('ubc.ctlt.acj.comment',
	[
		'ngResource',
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.classlist',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.judgement',
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
			{commentId: '@id'},
			{
				selfEval: {url: '/api/selfeval/courses/:courseId/questions/:questionId'},
				allSelfEval: {url: '/api/selfeval/courses/:courseId/questions'}
			}
		);
		ret.MODEL = "PostsForAnswersAndPostsForComments";
		return ret;
	}
);

module.factory(
	"UserAnswerCommentResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/questions/:questionId/answers/:answerId/users/comments'
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
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
	
		$scope.comment = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function(ret) {
				$scope.parent = ret.question;
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
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
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
				$scope.parent = ret.question;
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
	function ($scope, $log, $location, $routeParams, AnswerCommentResource, AnswerResource, QuestionResource, Authorize, required_rounds, Toaster)
	{
		var courseId = $scope.courseId = $routeParams['courseId']
		var questionId = $scope.questionId = $routeParams['questionId'];
		var answerId = $routeParams['answerId'];

		$scope.canManagePosts = 
			Authorize.can(Authorize.MANAGE, QuestionResource.MODEL)
		$scope.comment = {};
		AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerId}).$promise.then(
			function (ret) {
				$scope.parent = ret;
				$scope.replyToUser = ret.post.user.displayname;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret)
			{
				var min_pairs = ret.question.answers.length/2;
				var required = ret.students > 0 ? Math.ceil(min_pairs * required_rounds / ret.students): 0;
				if (!$scope.canManagePosts && ret.judged < required) {
					Toaster.error("The required number of judgements have to be made before any comments can be made.");
					$location.path('/course/' + courseId + '/question/' + questionId);
				}
			},
			function (ret)
			{
				Toaster.reqerror("Unable to retrieve judgement records.", ret);
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
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
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
				$scope.replyToUser = ret.post.user.displayname;
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

module.controller(
	"JudgementCommentController",
	function ($scope, $log, $routeParams, breadcrumbs, EvalCommentResource, CoursesCriteriaResource, CourseResource, QuestionResource,
			  AnswerResource, AttachmentResource, GroupResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		$scope.search = {'userId': null, 'criteriaId': null};
		$scope.course = {};
		$scope.courseId = courseId;
		$scope.questionId = questionId;

		var allStudents = {};
		$scope.group = null;
		
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
				breadcrumbs.options = {'Course Questions': ret.name};
			},
			function (ret) {
				Toaster.reqerror("Course Not Found For ID "+ courseId, ret);
			}
		);
		
		EvalCommentResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret) {
				$scope.comments = ret.comments;
			},
			function (ret) {
				Toaster.reqerror("Comment retrieval failed", ret);
			}
		);

		CourseResource.getStudents({'id': courseId}).$promise.then(
			function (ret) {
				allStudents = ret.students;
				$scope.students = allStudents;
			},
			function (ret) {
				Toaster.reqerror("Class list retrieval failed", ret);
			}
		);
		
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function(ret) {
				$scope.parent = ret.question;
				$scope.criteria = ret.question.criteria;
				$scope.search.criteriaId = $scope.criteria[0].id;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the question "+questionId, ret);
			}
		);

		GroupResource.get({'courseId': courseId}).$promise.then(
			function (ret) {
				$scope.groups = ret.groups;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the groups in the course.", ret);
			}
		);

		$scope.updateGroup = function() {
			$scope.search.userId = null;
			if ($scope.group == null) {
				$scope.students = allStudents;
			} else {
				GroupResource.get({'courseId': courseId, 'groupId': $scope.group}).$promise.then(
					function (ret) {
						$scope.students = ret.students;
					},
					function (ret) {
						Toaster.reqerror("Unable to retrieve the group members", ret);
					}
				);
			}
		};

		$scope.commentFilter = function(user_id, criteria_id) {
			return function(comment) {
				var criteria = false;
				var user = false;
				if (user_id == null || comment.judgement.users_id == user_id) {
					user = true;
				}
				if (criteria_id == null || comment.judgement.question_criterion.id == criteria_id) {
					criteria = true;
				}

				return user && criteria;
			}
		};

		$scope.answers = function(comment) {
			var answerpair = comment.judgement.answerpairing;
			AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerpair.postsforanswers_id1}).$promise.then(
				function (ret) {
					answerpair[answerpair.postsforanswers_id1] = ret;
					AttachmentResource.get({'postId': ret.post.id}).$promise.then(
						function (ret) {
							answerpair[answerpair.postsforanswers_id1]['file'] = ret.file;
						},
						function (ret) {
							Toaster.reqerror("Unable to retrieve attachment", ret);
						}
					);
				},
				function (ret) {
					Toaster.reqerror("Unable to retrieve answer 1", ret);
				}
			);
			AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerpair.postsforanswers_id2}).$promise.then(
				function (ret) {
					answerpair[answerpair.postsforanswers_id2] = ret;
					AttachmentResource.get({'postId': ret.post.id}).$promise.then(
						function (ret) {
							answerpair[answerpair.postsforanswers_id2]['file'] = ret.file;
						},
						function (ret) {
							Toaster.reqerror("Unable to retrieve attachment", ret);
						}
					);
				},
				function (ret) {
					Toaster.reqerror("Unable to retrieve answer 1", ret);
				}
			);
		}
	}
);

// End anonymouse function
}) ();
