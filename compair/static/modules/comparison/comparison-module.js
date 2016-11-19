// Controls how comparisons are entered for a assignment's answers.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.comparison',
    [
        'localytics.directives',
        'ubc.ctlt.compair.answer',
        'ubc.ctlt.compair.authentication',
        'ubc.ctlt.compair.comment',
        'ubc.ctlt.compair.criterion',
        'ubc.ctlt.compair.assignment',
        'ubc.ctlt.compair.toaster',
        'ubc.ctlt.compair.common.xapi',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.mathjax',
        'ubc.ctlt.compair.common.highlightjs',
        'ubc.ctlt.compair.common.pdf',
        'ubc.ctlt.compair.session'
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
        'EditorOptions', "Authorize", "xAPI", "xAPIStatementHelper",
    function($log, $location, $route, $scope, $timeout, $routeParams, $anchorScroll, AssignmentResource, AnswerResource,
        ComparisonResource, AnswerCommentResource, Session, Toaster, AnswerCommentType, TimerResource,
        EditorOptions, Authorize, xAPI, xAPIStatementHelper)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        var userId;
        $scope.assignment = {};
        $scope.submitted = false;
        $scope.isDraft = false;
        $scope.preventExit = true; //user should be warned before leaving page by default
        $scope.tracking = xAPI.generateTracking();

        $scope.editor1Options =  xAPI.ckeditorContentTracking(EditorOptions.basic, function(duration) {
            xAPIStatementHelper.interacted_answer_comment($scope.answer1.comment, $scope.tracking.getRegistration(), duration);
        });
        $scope.editor2Options =  xAPI.ckeditorContentTracking(EditorOptions.basic, function(duration) {
            xAPIStatementHelper.interacted_answer_comment($scope.answer2.comment, $scope.tracking.getRegistration(), duration);
        });

        var countDown = function() {
            $scope.showCountDown = true;
        };

        Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId).then(function(result) {
            $scope.canManageAssignment = result;
        });

        // get an comparisons to be compared from the server
        $scope.comparisonsError = false;
        $scope.answer1 = {};
        $scope.answer2 = {};
        $scope.comparisons = [];
        Session.getUser().then(function(user) {
            userId = user.id;
            ComparisonResource.get({'courseId': courseId, 'assignmentId': assignmentId},
                function (ret) {
                    // check if there is any existing comments from current user
                    var newPair = ret.new_pair;
                    $scope.comparisons = ret.objects;
                    $scope.answer1 = angular.copy($scope.comparisons[0].answer1);
                    $scope.answer1.comment = {};
                    $scope.answer2 = angular.copy($scope.comparisons[0].answer2);
                    $scope.answer2.comment = {};

                    $scope.current = ret.current;
                    $scope.firstAnsNum = ($scope.current * 2) - 1;
                    $scope.secondAnsNum = ($scope.current * 2);

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
                            // create new answer comment drafts if they don't already exist
                            _.forEach([$scope.answer1, $scope.answer2], function(answer) {
                                if (!answer.comment.id) {
                                    var params = {
                                        courseId: courseId,
                                        assignmentId: assignmentId,
                                        answerId: answer.id
                                    };
                                    answer.comment.comment_type = AnswerCommentType.evaluation;
                                    answer.comment.draft = true;
                                    AnswerCommentResource.save(params, answer.comment).$promise.then(
                                        function(ret) {
                                            answer.comment = ret;
                                        }
                                    );
                                }
                            });
                        }
                    );
                    AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
                        function (ret)
                        {
                            $scope.assignment = ret;
                            $scope.total = $scope.assignment.total_steps_required;
                            // if there is a comparison end date, check if timer is needed
                            var due_date = new Date($scope.assignment.compare_end);
                            if (due_date && $scope.assignment.compare_end != null) {
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
                            if (newPair) {
                                xAPIStatementHelper.initialize_comparison_question(
                                    $scope.comparisons, $scope.current, $scope.assignment.pairing_algorithm,
                                    $scope.tracking.getRegistration()
                                );
                            } else {
                                xAPIStatementHelper.resume_comparison_question(
                                    $scope.comparisons, $scope.current, $scope.assignment.pairing_algorithm,
                                    $scope.tracking.getRegistration()
                                );
                            }
                        },
                        function (ret)
                        {
                            Toaster.reqerror("Assignment Not Loaded", ret);
                        }
                    );
                }, function (ret) {
                    $scope.comparisonsError = true;
                    if (ret.status == 403 && ret.data && ret.data.error) {
                        Toaster.info(ret.data.error);
                    } else if (ret.status == 400 && ret.data && ret.data.error)  {
                        Toaster.info("You have compared all the currently available answers.", "Please check back later for more answers.");
                    } else {
                        Toaster.reqerror("Cannot Compare Answers", ret);
                    }
                    $scope.preventExit = false; //no work done. its safe to exit
                }
            );
        });

        $scope.trackExited = function() {
            xAPIStatementHelper.exited_comparison_question(
                $scope.comparisons, $scope.current, $scope.assignment.pairing_algorithm,
                $scope.tracking.getRegistration(), $scope.tracking.getDuration()
            );
        };

        $scope.trackComparisonWinner = function(comparison) {
            xAPIStatementHelper.interacted_comparison_solution(
                comparison, $scope.tracking.getRegistration()
            );
        };

        // save comparison to server
        $scope.comparisonSubmit = function(comparisonForm) {
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
                answer.comment.tracking = $scope.tracking.toParams();
                AnswerCommentResource.save(params, answer.comment).$promise.then(
                    function(ret) {
                        // need comment id if saving draft
                        answer.comment = ret;
                    }
                );
            });
            var comparisons = []
            angular.forEach($scope.comparisons, function(comparison) {
                comparisons.push({
                    criterion_id: comparison.criterion_id,
                    content: comparison.content,
                    winner_id: comparison.winner_id,
                    draft: $scope.isDraft
                });
            });

            $data = {
                comparisons: comparisons,
                tracking: $scope.tracking.toParams()
            };

            ComparisonResource.save({'courseId': courseId, 'assignmentId': assignmentId}, $data).$promise.then(
                function(ret) {
                    $scope.submitted = false;
                    if (!$scope.isDraft) {
                        if(!$scope.canManageAssignment) {
                            AssignmentResource.getCurrentUserStatus({'id': $scope.courseId, 'assignmentId': assignmentId},
                                function(ret) {
                                    var comparisons_count = ret.status.comparisons.count;

                                    if ($scope.assignment.total_comparisons_required > comparisons_count) {
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
                            Toaster.success("Your Comparison Saved Successfully", "The next answer pair is now being loaded.");
                            $scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
                            $route.reload();
                            window.scrollTo(0, 0);
                        }
                    } else {
                        if (comparisonForm) {
                            comparisonForm.$setPristine();
                        }
                        $scope.tracking = xAPI.generateTracking();
                        xAPIStatementHelper.resume_comparison_question(
                            $scope.comparisons, $scope.current, $scope.assignment.pairing_algorithm,
                            $scope.tracking.getRegistration()
                        );
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
            var params = {
                flagged: !answer['flagged'],
                tracking: $scope.tracking.toParams()
            };
            var resultMsg = answer['flagged'] ?
                "Answer has been unflagged." :
                "Answer has been flagged as inappropriate or incomplete.";

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
        'Session', 'Toaster', 'AnswerCommentType', 'EditorOptions', "xAPI", "xAPIStatementHelper",
    function($log, $location, $scope, $routeParams, AnswerResource, AssignmentResource,
             AnswerCommentResource, Session, Toaster, AnswerCommentType, EditorOptions, xAPI, xAPIStatementHelper)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        $scope.comment = {
            draft: true
        };
        $scope.tracking = xAPI.generateTracking();
        $scope.editorOptions =  xAPI.ckeditorContentTracking(EditorOptions.basic, function(duration) {
            xAPIStatementHelper.interacted_self_evaluation_review(
                $scope.comment, $scope.tracking.getRegistration(), duration
            );
        });
        $scope.preventExit = true; //user should be warned before leaving page by default

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
                                xAPIStatementHelper.resume_self_evaluation_question(
                                    $scope.comment, $scope.tracking.getRegistration()
                                );
                            } else {
                                // else generate new self-evaulation comment
                                var params = {
                                    courseId: courseId,
                                    assignmentId: assignmentId,
                                    answerId: answer.id
                                };
                                $scope.comment.comment_type = AnswerCommentType.evaluation;
                                $scope.comment.draft = true;
                                AnswerCommentResource.save(params, $scope.comment).$promise.then(
                                    function(ret) {
                                        $scope.comment = ret;
                                        xAPIStatementHelper.initialize_self_evaluation_question(
                                            $scope.comment, $scope.tracking.getRegistration()
                                        );
                                    }
                                );
                            }
                        }
                    );
                },
                function (ret) {
                    Toaster.reqerror("Unable To Retrieve Answer", ret);
                }
            );
        });

        $scope.trackExited = function() {
            xAPIStatementHelper.exited_self_evaluation_question(
                $scope.comment, $scope.tracking.getRegistration(), $scope.tracking.getDuration()
            );
        };

        $scope.commentSubmit = function () {
            $scope.submitted = true;
            $scope.comment.comment_type = AnswerCommentType.self_evaluation;
            var params = {
                courseId: courseId,
                assignmentId: assignmentId,
                answerId: $scope.parent.id,
                commentId: _.get($scope.comment, 'id')
            };
            $scope.comment.tracking = $scope.tracking.toParams()
            AnswerCommentResource.save(params, $scope.comment).$promise.then(
                function (ret) {
                    $scope.submitted = false;
                    $scope.preventExit = false; //user has saved self-evaluation, does not need warning when leaving page

                    if (ret.draft) {
                        Toaster.success("Saved Draft Successfully!", "Remember to submit your self-evaluation before the deadline.");
                        $location.path('/course/' + courseId + '/assignment/' + assignmentId + '/self_evaluation');
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
