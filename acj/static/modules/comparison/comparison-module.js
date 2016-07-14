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
        'ubc.ctlt.acj.common.highlightjs',
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
            {}
        );
        return ret;
}]);


/***** Constants *****/
module.constant('required_rounds', 6);

/***** Controllers *****/
module.controller(
    'ComparisonController',
    ['$log', '$location', '$route', '$scope', '$timeout', '$routeParams', '$anchorScroll', 'AssignmentResource', 'AnswerResource',
        'ComparisonResource', 'AnswerCommentResource', 'Session', 'Toaster', 'AnswerCommentType', "TimerResource",
        'EditorOptions',
    function($log, $location, $route, $scope, $timeout, $routeParams, $anchorScroll, AssignmentResource, AnswerResource,
        ComparisonResource, AnswerCommentResource, Session, Toaster, AnswerCommentType, TimerResource,
        EditorOptions)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        var userId;
        $scope.submitted = false;
        $scope.isDraft = false;
        $scope.preventExit = true; //user should be warned before leaving page by default

        $scope.editorOptions = EditorOptions.basic;

        var countDown = function() {
            $scope.showCountDown = true;
        };

        $scope.assignment = {};
        AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
            function (ret)
            {
                $scope.assignment = ret;
                $scope.total = $scope.assignment.number_of_comparisons;
                if ($scope.assignment.enable_self_evaluation) {
                    $scope.total += 1;
                }
                // if there is a comparison end date, check if timer is needed
                var due_date = new Date($scope.assignment.compare_end);
                if (due_date) {
                    TimerResource.get(
                        function (ret) {
                            var current_time = ret.date;
                            var trigger_time = due_date.getTime() - current_time - 600000; //(10 mins)
                            if (trigger_time < 86400000) { //(1 day)
                                $timeout(countDown, trigger_time);
                            }
                        },
                        function (ret) {
                            Toaster.reqerror("Unable to get the current time", ret);
                        }
                    );
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
            AssignmentResource.getCurrentUserStatus({'id': $scope.courseId, 'assignmentId': assignmentId},
                function (ret) {
                    // current comparison round user is on
                    $scope.current = ret.status.comparisons.count + 1;
                    // first answer # in pair
                    $scope.firstAnsNum = ret.status.comparisons.count + $scope.current;
                    // second answer # in pair
                    $scope.secondAnsNum = $scope.current * 2;
                },
                function (ret) {
                    Toaster.reqerror("Assignment Status Not Found", ret);
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
                        {'courseId':courseId, 'assignmentId':assignmentId, 'answer_ids': answer_ids, 'user_ids': userId, 'evaluation':'only', 'draft':'true'},
                        function(ret) {
                            _.forEach(ret, function(comment) {
                                if (comment.answer_id == $scope.answer1.id) {
                                    $scope.answer1.comment = comment;
                                } else if (comment.answer_id == $scope.answer2.id) {
                                    $scope.answer2.comment = comment;
                                }
                            });
                        }
                    );
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
                answer.comment.draft = $scope.isDraft;
                AnswerCommentResource.save(params, answer.comment).$promise.then(
                    function(ret) {
                        // need comment id if saving draft
                        answer.comment = ret;
                    }
                );
            });
            comparisons_submit = []
            angular.forEach($scope.comparisons, function(comparison) {
                comparisons_submit.push({
                    criterion_id: comparison.criterion_id,
                    content: comparison.content,
                    winner_id: comparison.winner_id,
                    draft: $scope.isDraft
                });
            });

            ComparisonResource.save(
                {'courseId': courseId, 'assignmentId': assignmentId},
                { 'comparisons': comparisons_submit }
            ).$promise.then(
                function(ret) {
                    $scope.submitted = false;
                    if (!$scope.isDraft) {
                        AssignmentResource.getCurrentUserStatus({'id': $scope.courseId, 'assignmentId': assignmentId},
                            function(ret) {
                                var comparisons_count = ret.status.comparisons.count;

                                if ($scope.assignment.number_of_comparisons > comparisons_count) {
                                    var left = $scope.assignment.number_of_comparisons - comparisons_count;
                                    Toaster.success("Your Comparison Saved Successfully", "The next answer pair is now being loaded. Good luck on the next round!");
                                    $scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
                                    $route.reload();
                                    window.scrollTo(0, 0);
                                // self-evaluation
                                } else if ($scope.assignment.enable_self_evaluation && ret.status.answers.answered) {
                                    Toaster.success("Your Comparison Saved Successfully", "Write a self-evaluation, and your assignment will be complete!");
                                    $scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
                                    $location.path('/course/'+courseId+'/assignment/'+assignmentId+'/self_evaluation');
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
                    } else {
                        Toaster.success("Saved Draft Successfully!", "Remember to submit your comparison before the deadline.");
                    }
                },
                function(ret) {
                    $scope.submitted = false;
                    // if compare period is not in session
                    if (ret.status == '403' && 'error' in ret.data) {
                        Toaster.error(ret.data.error);
                    } else {
                        Toaster.reqerror("Comparison Submit Failed", ret);
                    }
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
    ['$log', '$location', '$scope', '$routeParams', 'AnswerResource', 'AssignmentResource', 'AnswerCommentResource',
        'Session', 'Toaster', 'AnswerCommentType', 'EditorOptions',
    function($log, $location, $scope, $routeParams, AnswerResource, AssignmentResource,
             AnswerCommentResource, Session, Toaster, AnswerCommentType, EditorOptions)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        $scope.comment = {
            draft: true
        };

        $scope.editorOptions = EditorOptions.basic;

        AssignmentResource.getCurrentUserStatus({'id': courseId, 'assignmentId': assignmentId},
            function (ret) {
                // current comparison round user is on
                $scope.total = ret.status.comparisons.count + 1;
            },
            function (ret) {
                Toaster.reqerror("Assignment Status Not Found", ret);
            }
        );

        Session.getUser().then(function(user) {
            userId = user.id;
            AnswerResource.user({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
                function (ret) {
                    var answer = {}
                    if (!ret.objects.length) {
                        Toaster.error("No Answer Found", "Your answer for this assignment was not found, so the self-evaluation is unavailable.");
                        $location.path('/course/' + courseId);
                    } else {
                        answer = ret.objects[0];
                        $scope.parent = answer;
                    }
                    AnswerCommentResource.query(
                        {'courseId':courseId, 'assignmentId':assignmentId, 'answer_ids': answer.id, 'user_ids': userId, 'self_evaluation':'only', 'draft':'only'},
                        function(ret) {
                            if (ret.length > 0) {
                                $scope.comment = ret[0];
                            }
                        }
                    );
                },
                function (ret) {
                    Toaster.reqerror("Unable To Retrieve Answer", ret);
                }
            );
        });

        $scope.commentSubmit = function () {
            $scope.submitted = true;
            $scope.comment.comment_type = AnswerCommentType.self_evaluation;
            var params = {
                courseId: courseId,
                assignmentId: assignmentId,
                answerId: $scope.parent.id,
                commentId: _.get($scope.comment, 'id')
            };
            AnswerCommentResource.save(params, $scope.comment).$promise.then(
                function (ret) {
                    $scope.submitted = false;
                    if (ret.draft) {
                        $scope.comment = ret;
                        Toaster.success("Saved Draft Successfully!", "Remember to submit your self-evaluation before the deadline.");
                    } else {
                        Toaster.success("Your Self-Evaluation Saved Successfully", "Your assignment is now complete. Good work!");
                        $location.path('/course/' + courseId);
                    }
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
