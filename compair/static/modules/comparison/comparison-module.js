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
        'ubc.ctlt.compair.common.attachment',
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

module.constant('WinningAnswer', {
    answer1: "answer1",
    answer2: "answer2",
    draw: "draw"
});

/***** Constants *****/
module.constant('required_rounds', 6);

/***** Controllers *****/
module.controller(
    'ComparisonController',
    ['$location', '$route', '$scope', '$timeout', '$routeParams', '$anchorScroll', 'AssignmentResource', 'AnswerResource',
        'ComparisonResource', 'AnswerCommentResource', 'Toaster', 'AnswerCommentType',
        'EditorOptions', "xAPI", "xAPIStatementHelper", "WinningAnswer", "resolvedData",
    function($location, $route, $scope, $timeout, $routeParams, $anchorScroll, AssignmentResource, AnswerResource,
        ComparisonResource, AnswerCommentResource, Toaster, AnswerCommentType,
        EditorOptions, xAPI, xAPIStatementHelper, WinningAnswer, resolvedData)
    {
        $scope.courseId = $routeParams.courseId;
        $scope.assignmentId = $routeParams.assignmentId;

        $scope.course = resolvedData.course;
        $scope.assignment = resolvedData.assignment;
        $scope.canManageAssignment = resolvedData.canManageAssignment;
        $scope.loggedInUserId = resolvedData.loggedInUser.id;

        $scope.submitted = false;
        $scope.isDraft = false;
        $scope.preventExit = true; //user should be warned before leaving page by default
        $scope.tracking = xAPI.generateTracking();
        $scope.WinningAnswer = WinningAnswer;

        $scope.editor1Options =  xAPI.ckeditorContentTracking(EditorOptions.basic, function(duration) {
            xAPIStatementHelper.interacted_answer_comment($scope.answer1.comment, $scope.tracking.getRegistration(), duration);
        });
        $scope.editor2Options =  xAPI.ckeditorContentTracking(EditorOptions.basic, function(duration) {
            xAPIStatementHelper.interacted_answer_comment($scope.answer2.comment, $scope.tracking.getRegistration(), duration);
        });

        $scope.total = $scope.assignment.total_steps_required;

        // if there is a comparison end date, check if timer is needed
        var due_date = new Date($scope.assignment.compare_end);
        if (due_date && $scope.assignment.compare_end != null) {
            var current_time = resolvedData.timer.date;
            var trigger_time = due_date.getTime() - current_time - 600000; //(10 mins)
            if (trigger_time < 86400000) { //(1 day)
                $timeout(function() {
                    $scope.showCountDown = true;
                }, trigger_time);
            }
        }

        // get an comparisons to be compared from the server
        $scope.comparisonError = false;
        $scope.answer1 = {};
        $scope.answer2 = {};
        $scope.comparison = {};

        ComparisonResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId},
            function (ret) {
                // check if there is any existing comments from current user
                var newPair = ret.new_pair;
                $scope.comparison = ret.comparison;
                $scope.answer1 = angular.copy($scope.comparison.answer1);
                $scope.answer1.comment = {};
                $scope.answer2 = angular.copy($scope.comparison.answer2);
                $scope.answer2.comment = {};

                $scope.current = ret.current;
                $scope.firstAnsNum = ($scope.current * 2) - 1;
                $scope.secondAnsNum = ($scope.current * 2);

                var answer_ids = [$scope.answer1.id, $scope.answer2.id].sort().join(',');
                AnswerCommentResource.query({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId,
                        'answer_ids': answer_ids, 'user_ids': $scope.loggedInUserId, 'evaluation':'only', 'draft':'true'},
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
                                    courseId: $scope.courseId,
                                    assignmentId: $scope.assignmentId,
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

                if (newPair) {
                    xAPIStatementHelper.initialize_comparison_question(
                        $scope.comparison, $scope.current, $scope.assignment.pairing_algorithm,
                        $scope.tracking.getRegistration()
                    );
                } else {
                    xAPIStatementHelper.resume_comparison_question(
                        $scope.comparison, $scope.current, $scope.assignment.pairing_algorithm,
                        $scope.tracking.getRegistration()
                    );
                }
            }, function (ret) {
                //TODO: double check messages
                $scope.comparisonError = true;
                if (ret.status == 403 && ret.data && ret.data.message) {
                    Toaster.info(ret.data.message);
                } else if (ret.status == 400 && ret.data && ret.data.title && ret.data.message)  {
                    Toaster.info(ret.data.title, ret.data.message);
                }
                $scope.preventExit = false; //no work done. its safe to exit
            }
        );

        $scope.trackExited = function() {
            xAPIStatementHelper.exited_comparison_question(
                $scope.comparison, $scope.current, $scope.assignment.pairing_algorithm,
                $scope.tracking.getRegistration(), $scope.tracking.getDuration()
            );
        };

        $scope.trackComparisonCriterionWinner = function(comparison_criterion) {
            xAPIStatementHelper.interacted_comparison_criterion_solution(
                $scope.comparison, comparison_criterion, $scope.tracking.getRegistration()
            );
        };

        // save comparison to server
        $scope.comparisonSubmit = function(comparisonForm) {
            $scope.submitted = true;
            // save comments for each individual answer
            angular.forEach([$scope.answer1, $scope.answer2], function(answer) {
                var params = {
                    courseId: $scope.courseId,
                    assignmentId: $scope.assignmentId,
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
            var comparison_criteria = []
            var comparisons = []
            angular.forEach($scope.comparison.comparison_criteria, function(comparison_criterion) {
                comparison_criteria.push({
                    criterion_id: comparison_criterion.criterion_id,
                    content: comparison_criterion.content,
                    winner: comparison_criterion.winner
                });
            });

            $data = {
                draft: $scope.isDraft,
                comparison_criteria: comparison_criteria,
                tracking: $scope.tracking.toParams()
            };

            ComparisonResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $data).$promise.then(
                function(ret) {
                    $scope.submitted = false;
                    if (!$scope.isDraft) {
                        if(!$scope.canManageAssignment) {
                            AssignmentResource.getCurrentUserStatus({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId},
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
                                        $location.path('/course/' + $scope.courseId + '/assignment/' + $scope.assignmentId + '/self_evaluation');
                                    } else {
                                        Toaster.success("Your Comparison Saved Successfully", "Your assignment is now complete. Good work!");
                                        $scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
                                        $location.path('/course/' + $scope.courseId);
                                    }
                                },
                                function(ret) {
                                    Toaster.success("Your Comparison Saved Successfully");
                                    $scope.preventExit = false; //user has saved comparison, does not need warning when leaving page
                                    $location.path('/course/' + $scope.courseId);
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
                            $scope.comparison, $scope.current, $scope.assignment.pairing_algorithm,
                            $scope.tracking.getRegistration()
                        );
                        Toaster.success("Saved Draft Successfully!", "Remember to submit your comparison before the deadline.");
                    }
                },
                function(ret) {
                    $scope.submitted = false;
                }
            );
        };

        // flag answer for instructor
        $scope.toggleAnswerFlag = function(answer) {
            var params = {
                flagged: !answer.flagged,
                tracking: $scope.tracking.toParams()
            };
            var resultMsg = answer.flagged ?
                "Answer has been unflagged." :
                "Answer has been flagged as inappropriate or incomplete.";

            AnswerResource.flagged({'courseId':courseId,'assignmentId': $scope.assignmentId,
                'answerId': answer['id']}, params).$promise.then(
                function() {
                    answer.flagged = params['flagged'];
                    Toaster.success(resultMsg);
                }
            );
        };
    }]
);

module.controller(
    'ComparisonSelfEvalController',
    ['$location', '$scope', '$routeParams', 'AnswerResource', 'AssignmentResource', 'AnswerCommentResource',
     'Toaster', 'AnswerCommentType', 'EditorOptions', "xAPI", "xAPIStatementHelper", "resolvedData",
    function($location, $scope, $routeParams, AnswerResource, AssignmentResource, AnswerCommentResource,
             Toaster, AnswerCommentType, EditorOptions, xAPI, xAPIStatementHelper, resolvedData)
    {
        $scope.courseId = $routeParams.courseId;
        $scope.assignmentId = $routeParams.assignmentId;

        $scope.course = resolvedData.course;
        $scope.assignment = resolvedData.assignment;
        $scope.assignmentStatus = resolvedData.assignmentStatus;
        $scope.loggedInUserId = resolvedData.loggedInUser.id;

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
        $scope.total = $scope.assignmentStatus.status.comparisons.count + 1;

        $scope.answerId = undefined;
        if (!resolvedData.userAnswers.objects.length) {
            Toaster.error("No Answer Found", "Your answer for this assignment was not found, so the self-evaluation is unavailable.");
            $location.path('/course/' + $scope.courseId);
        } else {
            var answer = ret.objects[0];
            $scope.answerId = answer.id;
            $scope.parent = answer;
        }
        AnswerCommentResource.query({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId,
                'answer_ids': $scope.answerId, 'user_ids': $scope.loggedInUserId, 'self_evaluation':'only', 'draft':'only'},
            function(ret) {
                if (ret.length > 0) {
                    $scope.comment = ret[0];
                    xAPIStatementHelper.resume_self_evaluation_question(
                        $scope.comment, $scope.tracking.getRegistration()
                    );
                } else {
                    // else generate new self-evaluation comment
                    var params = {
                        courseId: $scope.courseId,
                        assignmentId: $scope.assignmentId,
                        answerId: $scope.answerId
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

        $scope.trackExited = function() {
            xAPIStatementHelper.exited_self_evaluation_question(
                $scope.comment, $scope.tracking.getRegistration(), $scope.tracking.getDuration()
            );
        };

        $scope.commentSubmit = function () {
            $scope.submitted = true;
            $scope.comment.comment_type = AnswerCommentType.self_evaluation;
            var params = {
                courseId: $scope.courseId,
                assignmentId: $scope.assignmentId,
                answerId: $scope.answerId,
                commentId: _.get($scope.comment, 'id')
            };
            $scope.comment.tracking = $scope.tracking.toParams()
            AnswerCommentResource.save(params, $scope.comment).$promise.then(
                function (ret) {
                    $scope.preventExit = false; //user has saved self-evaluation, does not need warning when leaving page

                    if (ret.draft) {
                        Toaster.success("Saved Draft Successfully!", "Remember to submit your self-evaluation before the deadline.");
                        $location.path('/course/' + $scope.courseId + '/assignment/' + $scope.assignmentId + '/self_evaluation');
                    } else {
                        Toaster.success("Your Self-Evaluation Saved Successfully", "Your assignment is now complete. Good work!");
                        $location.path('/course/' + $scope.courseId);
                    }
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }]
);

module.controller(
    "ComparisonViewController",
    ['$scope', '$routeParams', 'breadcrumbs', 'CourseResource', 'AssignmentResource', "WinningAnswer",
        'AnswerResource', 'AnswerCommentResource', 'GroupResource', 'Toaster', "xAPIStatementHelper", "resolvedData",
    function ($scope, $routeParams, breadcrumbs, CourseResource, AssignmentResource, WinningAnswer,
        AnswerResource, AnswerCommentResource, GroupResource, Toaster, xAPIStatementHelper, resolvedData)
    {
        $scope.courseId = $routeParams.courseId;
        $scope.assignmentId = $routeParams.assignmentId;

        $scope.course = resolvedData.course;
        $scope.assignment = resolvedData.assignment;
        $scope.students = resolvedData.students.objects;
        $scope.groups = resolvedData.groups.objects;

        $scope.listFilters = {
            page: 1,
            perPage: 20,
            group: null,
            author: null
        };
        $scope.answers = [];
        $scope.WinningAnswer = WinningAnswer;
        breadcrumbs.options = {'Course assignments': $scope.course.name};

        $scope.loadAnswerByAuthor = function(author_id) {
            if (_.find($scope.answers, {user_id: author_id})) return;
            AnswerResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId, 'author': author_id}, function(response) {
                var answer = response.objects[0];
                $scope.answers.push(answer);
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
            xAPIStatementHelper.filtered_page($scope.listFilters);
            $scope.updateList();
        });

        $scope.updateList = function() {
            var params = angular.merge({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $scope.listFilters);

            AnswerResource.comparisons(params, function(ret) {
                $scope.comparisons = ret;
                $scope.comparisons.grouped = _.groupBy($scope.comparisons.objects, 'user_id');
            });
        };
        $scope.updateList();
    }]
);


// End anonymous function
})();
