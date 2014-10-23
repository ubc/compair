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

module.factory('AnswerPairingResource',
	function($resource) {
		var resourceUrl = '/api/courses/:courseId/questions/:questionId/answerpairing';
		var ret = $resource(
			resourceUrl
		);
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
		$scope.questionCriteria = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret)
			{
				$scope.question = ret.question;
				$scope.total = ret.question.num_judgement_req;
				$scope.questionCriteria = ret.question.criteria;
			},
			function (ret)
			{
				Toaster.reqerror("Question Not Loaded", ret);
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
						Toaster.reqerror("Evaluations Total Not Found", ret);
					}
				);
		});	

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
					Toaster.reqerror("Answer Pair Not Found", ret);
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
			angular.forEach($scope.questionCriteria,
				function(questionCriterion, index) {
					var criterionWinner = {
						'question_criterion_id': questionCriterion.id,
						'answer_id_winner': questionCriterion.winner
					};
					judgement['judgements'].push(criterionWinner);
					comments[questionCriterion.id] = questionCriterion.comment;
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
								temp['comment'] = comments[judge.question_criterion.id];
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
														Toaster.success("Evaluation Submitted Successfully", "Please submit " + left + " more evaluation(s).");
														$route.reload();
														window.scrollTo(0, 0);
													} else {
														Toaster.success("Evaluation Submitted Successfully");
														$location.path('/course/' + courseId);
													}
												},
												function(ret) {
													Toaster.success("Evaluation Submitted Successfully");
													$location.path('/course/' + courseId);
												}
											);
									});
								},
								function(ret) {
									Toaster.reqerror("Evaluation Submit Failed", ret);
								}
						);
					},
					function(ret) {
						Toaster.reqerror("Evaluation Submit Failed", ret);
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
								Toaster.reqerror("Unable To Save Reply", ret);
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
								Toaster.reqerror("Unable To Save Reply", ret);
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
					Toaster.reqerror("Unable To Change Flag", ret);
				}
			);

		};
	}
);

// End anonymous function
})();
