// Handles comment creation and editing.

(function() {

var module = angular.module('ubc.ctlt.acj.comment',
	[
		'ngResource',
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.classlist',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.common.interceptor',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.judgement',
		'ubc.ctlt.acj.question',
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
	function ($resource, Interceptors)
	{
		var url = '/api/courses/:courseId/questions/:questionId/answers/:answerId/comments/:commentId';
		var ret = $resource(
			url, {commentId: '@id'},
			{
				'get': {cache: true},
				'save': {method: 'POST', url: url, interceptor: Interceptors.answerCache},
				'delete': {method: 'DELETE', url: url, interceptor: Interceptors.answerCache},
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

module.filter('author', function() {
	return function(input, authorId) {
		if (angular.isObject(input)) {
			input = _.values(input);
		}
		return _.find(input, {'user_id': authorId});
	};
});

module.directive('acjStudentAnswer', function() {
	return {
		scope: {
			answer: '='
		},
		templateUrl: 'modules/comment/answer.html'
	}
});

module.directive('acjAnswerContent', function() {
	return {
		scope: {
			answer: '=',
			title: '@',
			isChosen: '=',
			criteriaAndQuestions: '='
		},
		templateUrl: 'modules/comment/answer-content.html'
	}
});

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
	function ($scope, $log, $location, $routeParams, AnswerCommentResource, AnswerResource,
			  QuestionResource, Authorize, Toaster)
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
		var answerId = $routeParams['answerId'];
		$scope.answerComment = true;
		$scope.canManagePosts =
			Authorize.can(Authorize.MANAGE, QuestionResource.MODEL, courseId);
		$scope.comment = {};

		AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerId}).$promise.then(
			function (ret) {
				$scope.parent = ret;
				$scope.replyToUser = ret.user_displayname;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);

		// only need to do this query if the user cannot manage users
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret) {
				if (!$scope.canManagePosts && !ret.question.can_reply) {
					Toaster.error("No replies can be made for answers in this question.");
					$location.path('/course/' + courseId + '/question/' + questionId);
				}
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the question.", ret);
			});
		$scope.commentSubmit = function () {
			$scope.submitted = true;
			AnswerCommentResource.save({'courseId': courseId, 'questionId': questionId, 'answerId': answerId},
				$scope.comment).$promise.then(
					function (ret)
					{
						$scope.submitted = false;
						Toaster.success("New reply posted!");
						$location.path('/course/'+courseId+'/question/'+questionId);
					},
					function (ret)
					{
						$scope.submitted = false;
						Toaster.reqerror("Unable to post new reply.", ret);
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
		$scope.answerComment = true;

		$scope.comment = {};
		$scope.parent = {}; // answer
		AnswerCommentResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerId, 'commentId': commentId}).$promise.then(
			function(ret) {
				$scope.comment = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve reply "+commentId, ret);
			}
		);
		AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': answerId}).$promise.then(
			function (ret) {
				$scope.parent = ret;
				$scope.replyToUser = ret.user_displayname;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);
		$scope.commentSubmit = function () {
			AnswerCommentResource.save({'courseId': courseId, 'questionId': questionId, 'answerId': answerId}, $scope.comment).$promise.then(
				function() {
					Toaster.success("Reply Updated!");
					$location.path('/course/' + courseId + '/question/' +questionId);
				},
				function(ret) { Toaster.reqerror("Reply Not Updated", ret);}
			);
		};
	}
);

module.controller(
	"JudgementCommentController",
	function ($scope, $log, $routeParams, breadcrumbs, EvalCommentResource, CoursesCriteriaResource,
			  CourseResource, QuestionResource, AnswerResource, AttachmentResource, GroupResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		$scope.courseId = courseId;
		$scope.questionId = questionId;
		$scope.listFilters = {
			page: 1,
			perPage: 20,
			group: null,
			author: null
		};
		$scope.answers = [];

		CourseResource.get({'id':courseId},
			function (ret) {
				breadcrumbs.options = {'Course Questions': ret['name']};
			},
			function (ret) {
				Toaster.reqerror("Course Not Found For ID "+ courseId, ret);
			}
		);

		$scope.students = CourseResource.getStudents({'id': courseId},
			function (ret) {},
			function (ret) {
				Toaster.reqerror("Class list retrieval failed", ret);
			}
		);

		QuestionResource.get({'courseId': courseId, 'questionId': questionId},
			function(ret) {
				$scope.parent = ret.question;
				$scope.criteria = {};
				angular.forEach(ret.question.criteria, function(criterion, key){
					$scope.criteria[criterion['id']] = criterion['criterion']['name'];
				});
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the question "+questionId, ret);
			}
		);

		$scope.groups = GroupResource.get({'courseId': courseId},
			function (ret) {},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the groups in the course.", ret);
			}
		);

		$scope.loadAnswer = function(id) {
			if (_.find($scope.answers, {id: id})) return;
			AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'answerId': id}, function(response) {
				$scope.answers.push(convertScore(response));
			});
		};

		$scope.loadAnswerByAuthor = function(author_id) {
			if (_.find($scope.answers, {user_id: author_id})) return;
			AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'author': author_id}, function(response) {
				var answer = response.objects[0];
				$scope.answers.push(convertScore(answer));
			});
		};

		$scope.loadAllAnswers = function() {
			var missingIds = _($scope.comparisons.objects).pluck('answer1.id')
				.concat(_.pluck($scope.comparisons.objects, 'answer2.id'))
				.uniq().difference(_.pluck($scope.answers, 'id')).value();
			AnswerResource.get({'courseId': courseId, 'questionId': questionId, 'ids': missingIds.join(','), 'perPage': missingIds.length}, function(response) {
				_.forEach(response.objects, function(answer) {
					$scope.answers.push(convertScore(answer));
				});
			});
		};

		$scope.$watchCollection('listFilters', function(newValue, oldValue) {
			if (angular.equals(newValue, oldValue)) return;
			if (oldValue.group != newValue.group) {
				$scope.listFilters.author = null;
				$scope.listFilters.page = 1;
			}
			if (oldValue.author != newValue.author) {
				$scope.listFilters.page = 1;
			}
			$scope.updateList();
		});

		$scope.updateList = function() {
			var params = angular.merge({'courseId': $scope.courseId, 'questionId': questionId}, $scope.listFilters);
			EvalCommentResource.view(params,
				function (ret) {
					$scope.comparisons = ret;
				},
				function (ret) {
					Toaster.reqerror('Error', ret);
				}
			);
		};

		$scope.updateList();
	}
);

function convertScore(answer) {
	var scores = answer.scores;
	answer.scores = _.reduce(scores, function(results, score) {
		results[score.criteriaandquestions_id] = score.normalized_score;
		return results;
	}, {});

	return answer;
}
// End anonymouse function
}) ();
