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
		'ubc.ctlt.acj.common.pdf',
		'ubc.ctlt.acj.session'
	]
);

/***** Providers *****/
module.factory('JudgementResource', ['$resource',
	function($resource) {
		var resourceUrl =
			'/api/courses/:courseId/questions/:questionId/judgements';
		var ret = $resource(
			resourceUrl,
			{},
			{
				'getAnswerPair': {url: resourceUrl + '/pair'},
				'count': {url: resourceUrl + '/users/:userId/count'},
				'getAvailPairLogic': {url: resourceUrl + '/users/:userId/availpair'}
			}
		);
		return ret;
}]);

module.factory('EvalCommentResource', ['$resource',
	function($resource) {
		var url = '/api/courses/:courseId/questions/:questionId/judgements/comments';
		var ret = $resource(url, {},
			{
				'view': {url: url + '/view', cache:true}
			}
		);
		ret.MODEL = "PostsForJudgements";
		return ret;
}]);

module.factory('AnswerPairingResource', ['$resource',
	function($resource) {
		var resourceUrl = '/api/courses/:courseId/questions/:questionId/answerpairing';
		var ret = $resource(
			resourceUrl
		);
		return ret;
}]);


/***** Constants *****/
module.constant('required_rounds', 6);

/***** Controllers *****/
module.controller(
	'JudgementController', ['$log', '$location', '$route', '$scope', '$timeout', '$routeParams', '$anchorScroll',
		'QuestionResource', 'AnswerResource', 'CoursesCriteriaResource', 'JudgementResource', 'AnswerCommentResource',
		'EvalCommentResource', 'Session', 'Toaster',
	function($log, $location, $route, $scope, $timeout, $routeParams, $anchorScroll, QuestionResource, AnswerResource,
		CoursesCriteriaResource, JudgementResource, AnswerCommentResource, EvalCommentResource, Session, Toaster)
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
		var userId;
		$scope.submitted = false;

		$scope.question = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret)
			{
				$scope.question = ret.question;
				$scope.total = ret.question.num_judgement_req;
				if (ret.question.selfevaltype_id) {
					$scope.total += 1;
				}
			},
			function (ret)
			{
				Toaster.reqerror("Question Not Loaded", ret);
			}
		);
		Session.getUser().then(function(user) {
			userId = user.id;
			JudgementResource.count(
				{'courseId': courseId, 'questionId': questionId, 'userId': userId}).
				$promise.then(
					function(ret) {
						// current comparison round user is on
						$scope.current = ret.count + 1;
						// first answer # in pair
						$scope.firstAnsNum = ret.count + $scope.current;
						// second answer # in pair
						$scope.secondAnsNum = $scope.current * 2;
					},
					function(ret) {
						Toaster.reqerror("Comparisons Total Not Found", ret);
					}
				);
		});

		// get an answerpair to be judged from the server
		$scope.answerPairError = false;
		$scope.answerPair = JudgementResource.getAnswerPair(
			{'courseId': courseId, 'questionId': questionId}, function (ret) {
				// check if there is any existing comments from current user
				var answer_ids = _.pluck(ret.answers, 'id').sort().join(',');
				AnswerCommentResource.query(
					{'courseId':courseId, 'questionId':questionId, 'answer_ids': answer_ids, 'user_ids': userId},
					function(ret) {
						_.forEach(ret, function(comment) {
							_.forEach($scope.answerPair.answers, function(answer) {
								if (answer.id == comment.answer_id) {
									answer.comment = comment;
								} else {
									answer.comment = {}
								}
							})
						});
					});
			}, function (ret) {
				$scope.answerPairError = true;
				Toaster.info("You've compared the available answers!", "Please check back later for more answers.");
			}
		);

		// enable scrolling to evaluation step 2, when step 2 revealed
		//$scope.showNext = function(selector) {
			// ensure hidden step revealed first
			//$timeout(function(){
				// jump to revealed step
				//window.scrollTo(0, $(selector)[0].offsetTop - 220);
			//}, 0);
		//};

		$scope.preventExit = true; //user should be warned before leaving page by default

		// save judgement to server
		$scope.judgementSubmit = function() {
			var judgement = {};
			$scope.submitted = true;
			judgement['answerpair_id'] = $scope.answerPair.id;
			judgement['judgements'] = [];
			var comments = {};
			angular.forEach($scope.question.criteria, function(questionCriterion) {
				var criterionWinner = {
					'question_criterion_id': questionCriterion.id,
					'answer_id_winner': questionCriterion.winner
				};
				judgement['judgements'].push(criterionWinner);
				comments[questionCriterion.id] = questionCriterion.comment;
			});
			// save comments for each individual answer
			angular.forEach($scope.answerPair.answers, function(answer) {
				var params = {
					courseId: courseId,
					questionId: questionId,
					answerId: answer.id,
					commentId: _.get(answer, 'comment.id')
				};
				answer.comment.evaluation = true;
				AnswerCommentResource.save(params, answer.comment);
			});
			JudgementResource.save(
				{'courseId': courseId, 'questionId': questionId}, judgement).
				$promise.then(
					function(ret) {
						var evaluations = {};
						evaluations['judgements'] = [];
						angular.forEach(ret.objects,
							function(judge) {
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
														Toaster.success("Your Comparison Saved Successfully", "The next answer pair is now being loaded. Good luck on the next round!");
														$scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
														$route.reload();
														window.scrollTo(0, 0);
													// self-evaluation
													} else if ($scope.question.selfevaltype_id) {
														QuestionResource.getAnswered({'id': $scope.courseId,
															'questionId': questionId}).$promise.then(
																function (ret) {
																	// if user has an answer submitted
																	if(ret.answered > 0) {
																		Toaster.success("Your Comparison Saved Successfully", "Write a self-evaluation, and your assignment will be complete!");
																		$scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
																		$location.path('/course/'+courseId+'/question/'+questionId+'/selfevaluation');
																	} else {
																		Toaster.success("Your Comparison Saved Successfully");
																		$scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
																		$location.path('/course/' + courseId);
																	}
																},
																function (ret) {
																	Toaster.reqerror("Your Answer Not Found", ret);
																}
														);
													} else {
														Toaster.success("Your Comparison Saved Successfully", "Your assignment is now complete. Good work!");
														$scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
														$location.path('/course/' + courseId);
													}
												},
												function(ret) {
													Toaster.success("Your Comparison Saved Successfully");
													$scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
													$location.path('/course/' + courseId);
												}
											);
									});
								},
								function(ret) {
									Toaster.reqerror("Comparison Submit Failed", ret);
								}
						);
					},
					function(ret) {
						Toaster.reqerror("Comparison Submit Failed", ret);
					}
			);
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
	}]
);

module.controller(
	'JudgementSelfEvalController',
	['$log', '$location', '$scope', '$routeParams', 'AnswerResource', 'JudgementResource', 'AnswerCommentResource',
		'Session', 'Toaster',
	function($log, $location, $scope, $routeParams, AnswerResource, JudgementResource,
			 AnswerCommentResource, Session, Toaster)
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
		$scope.comment = {};

		Session.getUser().then(function(user) {
			var userId = user.id;
			var count = JudgementResource.count(
				{'courseId': courseId, 'questionId': questionId, 'userId': userId}).
				$promise.then(
					function(ret) {
						$scope.total = ret.count + 1;
					},
					function(ret) {
						Toaster.reqerror("Comparisons Total Not Found", ret);
					}
				);
		});

		AnswerResource.user({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret) {
				if (!ret.answer.length) {
					Toaster.error("No Answer Found", "Your answer for this assignment was not found, so the self-evaluation is unavailable.");
					$location.path('/course/' + courseId);
				} else {
					$scope.parent = ret.answer[0];
				}
			},
			function (ret) {
				Toaster.reqerror("Unable To Retrieve Answer", ret);
			}
		);

		$scope.commentSubmit = function () {
			$scope.submitted = true;
			$scope.comment.selfeval = true;
			AnswerCommentResource.save({'courseId': courseId, 'questionId': questionId, 'answerId': $scope.parent.id},
				$scope.comment).$promise.then(
					function (ret) {
						$scope.submitted = false;
						Toaster.success("Your Self-Evaluation Saved Successfully", "Your assignment is now complete. Good work!");
						$location.path('/course/' + courseId);
					},
					function (ret) {
						$scope.submitted = false;
						Toaster.reqerror("Unable To Save Self-Evaluation", ret);
					}
			)
		};
	}]
);

// End anonymous function
})();
