// Controls how judgements are entered for a question's answers.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.judgement', 
	[
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.comment',
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.session'
	]
);

/***** Providers *****/
module.factory('JudgementResource',
	function($resource) {
		var resourceUrl = 
			'/api/courses/:courseId/questions/:questionId/judgements';
		var ret = $resource(
			resourceUrl,
			{},
			{
				'getAnswerPair': {url: resourceUrl + '/pair'},
				'count': {url: resourceUrl + '/count/users/:userId'}
			}
		);
		return ret;
});

module.factory('EvalCommentResource',
	function($resource) {
		var ret = $resource(
			'/api/courses/:courseId/questions/:questionId/judgements/comments'
		);
		ret.MODEL = "PostsForJudgements";
		return ret;
});


/***** Constants *****/
module.constant('required_rounds', 6);

/***** Controllers *****/
module.controller(
	'JudgementController', 
	function($log, $location, $route, $scope, $timeout, $routeParams, $anchorScroll, QuestionResource, AnswerResource,
		CoursesCriteriaResource, JudgementResource, AnswerCommentResource, EvalCommentResource, UserAnswerCommentResource, Session, Toaster)
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
		$scope.submitted = false;
		
		$scope.question = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret)
			{
				$scope.question = ret.question;
				$scope.total = ret.question.num_judgement_req;
			},
			function (ret)
			{
				Toaster.reqerror("Unable to load question.", ret);
			}
		);
		Session.getUser().then(function(user) {
		    	var userId = user.id;
			var count = JudgementResource.count(
				{'courseId': courseId, 'questionId': questionId, 'userId': userId}).
				$promise.then(
					function(ret) {
						$scope.current = ret.count + 1;
					},
					function(ret) {
						Toaster.reqerror("Unable to load number of evaluations completed.", ret);
					}
				);
		});	

		// get all the criterias we're using for this course
		$scope.courseCriteria = {};
		CoursesCriteriaResource.get({'courseId': courseId}).$promise.then(
			function (ret)
			{
				$scope.courseCriteria = ret.objects
			},
			function (ret)
			{
				Toaster.reqerror("Unable to load criteria.", ret);
			}
		);
		// get an answerpair to be judged from the server
		$scope.answerPair = {};
		$scope.answerPairError = false;
		$scope.ansComments = {answer1: true, answer2: true};
		JudgementResource.getAnswerPair(
			{'courseId': courseId, 'questionId': questionId}).$promise.then(
				function (ret)
				{
					$scope.answerPair = ret;
					angular.forEach($scope.ansComments, function(value, key) {
						UserAnswerCommentResource.get({'courseId':courseId, 'questionId':questionId,
							'answerId': ret[key]['id']}).$promise.then(
								function (ret) {
									if (ret.object.length) {
										$scope.answerPair[key]['comment'] = ret.object['0'].postsforcomments;
										$scope.answerPair[key]['comment']['post']['id'] = ret.object['0'].id;
										$scope.ansComments[key] = false;
									}
								},
								function (ret) {}
						);
					});
				},
				function (ret)
				{
					$scope.answerPairError = true;
					Toaster.reqerror("Unable to retrieve an answer pair.", ret);
				}
		);
		
		// enable scrolling to evaluation step 2, when step 2 revealed
		$scope.showNext = function(selector) {
			// ensure hidden step revealed first
			$timeout(function(){
				// jump to revealed step
				window.scrollTo(0, $(selector)[0].offsetTop - 80);
			}, 0);
		};
		
		// save judgement to server
		$scope.judgementSubmit = function() {
			var judgement = {};
			$scope.submitted = true;
			judgement['answerpair_id'] = $scope.answerPair.id;
			judgement['judgements'] = [];
			var comments = {};
			angular.forEach($scope.courseCriteria, 
				function(courseCriterion, index) {
					var criterionWinner = {
						'course_criterion_id': courseCriterion.id,
						'answer_id_winner': courseCriterion.winner,
					};
					judgement['judgements'].push(criterionWinner);
					comments[courseCriterion.id] = courseCriterion.comment;
				}
			);
			JudgementResource.save(
				{'courseId': courseId, 'questionId': questionId}, judgement).
				$promise.then(
					function(ret) {
						var evaluations = {};
						evaluations['judgements'] = [];
						angular.forEach(ret.objects,
							function(judge, index) {
								var temp = judge;								
								temp['comment'] = comments[judge.course_criterion.id];
								evaluations['judgements'].push(temp);
							}
						);
						EvalCommentResource.save(
							{'courseId': courseId, 'questionId': questionId}, evaluations).
							$promise.then(
								function() {
									Session.getUser().then(function(user) {
		    								var userId = user.id;
										var count = JudgementResource.count(
											{'courseId': courseId, 'questionId': questionId, 'userId': userId}).
											$promise.then(
												function(ret) {
													if ($scope.question.num_judgement_req > ret.count) {
														var left = $scope.question.num_judgement_req - ret.count;
														Toaster.success("Judgement Submitted Successfully! Please submit " + left + " more evaluation(s).");
														$route.reload();
														window.scrollTo(0, 0);
													} else {
														Toaster.success("Judgement Submitted Successfully!");
														$location.path('/course/' + courseId);
													}
												},
												function(ret) {
													Toaster.success("Judgement Submitted Successfully!");
													$location.path('/course/' + courseId);
												}
											);
									});
								},
								function(ret) {
									Toaster.reqerror("Judgement Comment Submit Failed.", ret);
								}
						);
					},
					function(ret) {
						Toaster.reqerror("Judgement Submit Failed.", ret);
					}
			);
			// save comments for each individual answer
			angular.forEach($scope.ansComments, function(value, key) {
				if (value) {
					// save new comment
					AnswerCommentResource.save({'courseId': courseId, 'questionId': questionId, 'answerId': $scope.answerPair[key]['id']},
						$scope.answerPair[key]['comment']['post']).$promise.then(
							function (ret)
							{},
							function (ret)
							{
								Toaster.reqerror("Unable to post new comment.", ret);
							}
					);
				} else {
					// update previous comment
					AnswerCommentResource.save({'courseId': courseId, 'questionId': questionId, 'answerId': $scope.answerPair[key]['id'],
						'commentId': $scope.answerPair[key]['comment']['post']['id']},
						$scope.answerPair[key]['comment']['post']).$promise.then(
							function (ret)
							{},
							function (ret)
							{
								Toaster.reqerror("Unable to post new comment.", ret);
							}
					);
				}
			});
		};

		// flag answer for instructor
		$scope.toggleAnswerFlag = function(answer) {
			var params = {'flagged': !answer['flagged']};
			var resultMsg = 
				"Answer has been flagged as inappropriate or incomplete.";
			if (answer['flagged']) {
				resultMsg = "Answer has been unflagged.";
			}
			AnswerResource.flagged({'courseId':courseId,'questionId':questionId, 
				'answerId': answer['id']}, params).$promise.then(
				function() {
					answer.flagged = params['flagged'];
					Toaster.success(resultMsg);
				},
				function(ret) {
					Toaster.reqerror("Unable to change answer flag.", ret);
				}
			);

		};
	}
);

// End anonymous function
})();
