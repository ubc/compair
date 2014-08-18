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
		'ubc.ctlt.acj.judgement',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.session'
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
	function($scope, $log, $routeParams, AnswerResource, Authorize, QuestionResource, QuestionCommentResource, required_rounds, Session, Toaster)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		Session.getUser().then(function(user) {
            $scope.loggedInUserId = user.id;
        });
        Authorize.can(Authorize.MANAGE, QuestionResource.MODEL).then(function(result) {
            $scope.canManagePosts = result;
        });
		$scope.question = {};
		QuestionResource.get({'courseId': $scope.courseId,
			'questionId': questionId}).$promise.then(
				function (ret)
				{
					ret.question.answer_start = new Date(ret.question.answer_start);
					ret.question.answer_end = new Date(ret.question.answer_end);
					ret.question.judge_start = new Date(ret.question.judge_start);
					ret.question.judge_end = new Date(ret.question.judge_end);
					$scope.question = ret.question;
					$scope.criteria = ret.criteria;
					$scope.sortby = '0';
					$scope.order = 'answer.post.created';
					$scope.answers = ret.question.answers;
					$scope.reverse = true;
					// only sort by scores if scores are available
					if ($scope.answers.length > 0) {
						var answer = $scope.answers[0];
						if (answer['scores'].length > 0) {
							$scope.order = 'scores.'+$scope.sortby+'.score';
						}
					}

					var instructors = {}
					for (key in ret.instructors) {
						instructors[ret.instructors[key].user.id] = ret.instructors[key].usertypeforcourse.name;
					}
					$scope.instructors = instructors;

					$scope.answered = $scope.canManagePosts || ret.answers > 0;
					var min_pairs = ret.question.answers.length / 2;
					var required = ret.students > 0 ? Math.ceil(min_pairs * required_rounds / ret.students) : 0;
					$scope.judged_req_met = $scope.canManagePosts || ret.judged >= required;
					$scope.readDate = Date.parse(ret.question.post.created);
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
		$('#answers a').click(function (e) {
			e.preventDefault();
			$(this).tab('show');
		});
		$('#comments a').click(function (e) {
			e.preventDefault();
			$(this).tab('show');
		});
	}
);
module.controller("QuestionCreateController",
	function($scope, $log, $location, $routeParams, QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		$scope.question = {};
		$scope.questionSubmit = function () {
			$scope.submitted = true;
			if ($scope.question.availableCheck && !($scope.question.answer_start < $scope.question.answer_end && $scope.question.answer_end <= $scope.question.judge_start && $scope.question.judge_start < $scope.question.judge_end)) {
				Toaster.error('The answer and/or judging period is invalid.');
				$scope.submitted = false;
				return;
			}
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
				if (ret.question.answer_start && ret.question.answer_end && ret.question.judge_start && ret.question.judge_end) {
					ret.question.availableCheck = true;
					ret.question.answer_start = new Date(ret.question.answer_start);
					ret.question.answer_end = new Date(ret.question.answer_end);
					ret.question.judge_start = new Date(ret.question.judge_start);
					ret.question.judge_end = new Date(ret.question.judge_end);
				}
				$scope.question = ret.question;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve question "+$scope.questionId, ret);
			}
		);
		$scope.questionSubmit = function () {
			$scope.submitted = true;
			if ($scope.question.availableCheck && !($scope.question.answer_start < $scope.question.answer_end && $scope.question.answer_end <= $scope.question.judge_start && $scope.question.judge_start < $scope.question.judge_end)) {
				Toaster.error('The answer and/or judging period is invalid.');
				$scope.submitted = false;
				return;
			}
			QuestionResource.save({'courseId': courseId}, $scope.question).$promise.then(
				function() {
					$scope.submitted = false;
					Toaster.success("Question Updated!");
					$location.path('/course/' + courseId);
				 },
				function(ret) { 
					$scope.submitted = false;
					Toaster.reqerror("Question Save Failed.", ret);
				}
			);
		};
	}
);

module.controller("QuestionDeleteController",
	function($scope, $log, $location, $routeParams, QuestionResource, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		QuestionResource.delete({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret) {
				Toaster.success("Successfully deleted question " + ret.id);	
				$location.path('/course/'+courseId);
			},
			function (ret) {
				Toaster.reqerror("Question deletion failed", ret);
				$location.path('/course/'+courseId);
			}
		);
	}
);

// End anonymous function
})();
