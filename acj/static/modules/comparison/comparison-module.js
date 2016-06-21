// Controls how comparisons are entered for a assignment's answers.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.comparison',
	[
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.comment',
		'ubc.ctlt.acj.criterion',
		'ubc.ctlt.acj.assignment',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.common.pdf',
		'ubc.ctlt.acj.session'
	]
);

/***** Providers *****/
module.factory('ComparisonResource', ['$resource',
	function($resource) {
		var resourceUrl = '/api/courses/:courseId/assignments/:assignmentId/comparisons';
		var ret = $resource(
			resourceUrl,
			{},
			{
                'count': {url: resourceUrl + '/users/:userId/count'},
				'getComparisonAvailable': {url: resourceUrl + '/users/:userId/available'}
			}
		);
		return ret;
}]);


/***** Constants *****/
module.constant('required_rounds', 6);

/***** Controllers *****/
module.controller(
	'ComparisonController',
    ['$log', '$location', '$route', '$scope', '$timeout', '$routeParams', '$anchorScroll', 'AssignmentResource', 'AnswerResource',
        'ComparisonResource', 'AnswerCommentResource', 'Session', 'Toaster', 'AnswerCommentType',
	function($log, $location, $route, $scope, $timeout, $routeParams, $anchorScroll, AssignmentResource, AnswerResource,
		ComparisonResource, AnswerCommentResource, Session, Toaster, AnswerCommentType)
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
		var userId;
		$scope.submitted = false;

		$scope.assignment = {};
		AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
			function (ret)
			{
				$scope.assignment = ret;
				$scope.total = $scope.assignment.number_of_comparisons;
				if ($scope.assignment.enable_self_evaluation) {
					$scope.total += 1;
				}
			},
			function (ret)
			{
				Toaster.reqerror("Assignment Not Loaded", ret);
			}
		);

		// get an comparisons to be compared from the server
		$scope.comparisonsError = false;
        $scope.answer1 = {};
        $scope.answer2 = {};
        $scope.comparisons = [];
		Session.getUser().then(function(user) {
			userId = user.id;
			ComparisonResource.count(
				{'courseId': courseId, 'assignmentId': assignmentId, 'userId': userId}).
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
            ComparisonResource.get({'courseId': courseId, 'assignmentId': assignmentId},
                function (ret) {
                    // check if there is any existing comments from current user
                    $scope.comparisons = ret.objects;
                    $scope.answer1 = angular.copy($scope.comparisons[0].answer1);
                    $scope.answer1.comment = {};
                    $scope.answer2 = angular.copy($scope.comparisons[0].answer2);
                    $scope.answer2.comment = {};

                    var answer_ids = [$scope.answer1.id, $scope.answer2.id].sort().join(',');
                    AnswerCommentResource.query(
                        {'courseId':courseId, 'assignmentId':assignmentId, 'answer_ids': answer_ids, 'user_ids': userId, 'evaluation':'only'},
                        function(ret) {
                            _.forEach(ret, function(comment) {
                                if (comment.answer_id == $scope.answer1.id) {
                                    $scope.answer1.comment = comment;
                                } else if (comment.answer_id == $scope.answer2.id) {
                                    $scope.answer2.comment = comment;
                                }
                            });
                        });
                }, function (ret) {
                    $scope.comparisonsError = true;
                    Toaster.info("You've compared the available answers!", "Please check back later for more answers.");
                }
            );
		});

		// enable scrolling to evaluation step 2, when step 2 revealed
		//$scope.showNext = function(selector) {
			// ensure hidden step revealed first
			//$timeout(function(){
				// jump to revealed step
				//window.scrollTo(0, $(selector)[0].offsetTop - 220);
			//}, 0);
		//};

		$scope.preventExit = true; //user should be warned before leaving page by default

		// save comparison to server
		$scope.comparisonSubmit = function() {
			$scope.submitted = true;
			// save comments for each individual answer
			angular.forEach([$scope.answer1, $scope.answer2], function(answer) {
				var params = {
					courseId: courseId,
					assignmentId: assignmentId,
					answerId: answer.id,
					commentId: _.get(answer, 'comment.id')
				};
                answer.comment.comment_type = AnswerCommentType.evaluation;
				AnswerCommentResource.save(params, answer.comment);
			});
            comparisons_submit = []
			angular.forEach($scope.comparisons, function(comparison) {
                comparisons_submit.push({
					criterion_id: comparison.criterion_id,
					content: comparison.content,
					winner_id: comparison.winner_id
				});
			});

			ComparisonResource.save(
				{'courseId': courseId, 'assignmentId': assignmentId}, {
                    'comparisons': comparisons_submit
                }).$promise.then(
					function(ret) {
                        Session.getUser().then(function(user) {
                            var userId = user.id;
                            var count = ComparisonResource.count(
                                {'courseId': courseId, 'assignmentId': assignmentId, 'userId': userId}).
                                $promise.then(
                                    function(ret) {
                                        if ($scope.assignment.number_of_comparisons > ret.count) {
                                            var left = $scope.assignment.number_of_comparisons - ret.count;
                                            Toaster.success("Your Comparison Saved Successfully", "The next answer pair is now being loaded. Good luck on the next round!");
                                            $scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
                                            $route.reload();
                                            window.scrollTo(0, 0);
                                        // self-evaluation
                                        } else if ($scope.assignment.enable_self_evaluation) {
                                            AssignmentResource.getAnswered({'id': $scope.courseId,
                                                'assignmentId': assignmentId}).$promise.then(
                                                    function (ret) {
                                                        // if user has an answer submitted
                                                        if(ret.answered > 0) {
                                                            Toaster.success("Your Comparison Saved Successfully", "Write a self-evaluation, and your assignment will be complete!");
                                                            $scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
                                                            $location.path('/course/'+courseId+'/assignment/'+assignmentId+'/self_evaluation');
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
		};

		// flag answer for instructor
		$scope.toggleAnswerFlag = function(answer) {
			var params = {'flagged': !answer['flagged']};
			var resultMsg =
				"Answer has been flagged as inappropriate or incomplete.";
			if (answer['flagged']) {
				resultMsg = "Answer has been unflagged.";
			}
			AnswerResource.flagged({'courseId':courseId,'assignmentId':assignmentId,
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
	'ComparisonSelfEvalController',
	['$log', '$location', '$scope', '$routeParams', 'AnswerResource', 'ComparisonResource', 'AnswerCommentResource',
		'Session', 'Toaster', 'AnswerCommentType',
	function($log, $location, $scope, $routeParams, AnswerResource, ComparisonResource,
			 AnswerCommentResource, Session, Toaster, AnswerCommentType)
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
		$scope.comment = {};

		Session.getUser().then(function(user) {
			var userId = user.id;
			var count = ComparisonResource.count(
				{'courseId': courseId, 'assignmentId': assignmentId, 'userId': userId}).
				$promise.then(
					function(ret) {
						$scope.total = ret.count + 1;
					},
					function(ret) {
						Toaster.reqerror("Comparisons Total Not Found", ret);
					}
				);
		});

		AnswerResource.user({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
			function (ret) {
				if (!ret.objects.length) {
					Toaster.error("No Answer Found", "Your answer for this assignment was not found, so the self-evaluation is unavailable.");
					$location.path('/course/' + courseId);
				} else {
					$scope.parent = ret.objects[0];
				}
			},
			function (ret) {
				Toaster.reqerror("Unable To Retrieve Answer", ret);
			}
		);

		$scope.commentSubmit = function () {
			$scope.submitted = true;
			$scope.comment.comment_type = AnswerCommentType.self_evaluation;
			AnswerCommentResource.save({'courseId': courseId, 'assignmentId': assignmentId, 'answerId': $scope.parent.id},
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
