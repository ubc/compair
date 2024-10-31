// Provides the services and controllers for assignments.
//
(function() {
function combineDateTime(datetime) {
    var date = new Date(datetime.date);
    var time = new Date(datetime.time);
    date.setHours(time.getHours(), time.getMinutes(), time.getSeconds(), time.getMilliseconds());
    return date;
}

var module = angular.module('ubc.ctlt.compair.assignment',
    [
        'angularFileUpload',
        'ngResource',
        'ngclipboard',
        'ui.bootstrap',
        'localytics.directives',
        'ubc.ctlt.compair.answer',
        'ubc.ctlt.compair.authentication',
        'ubc.ctlt.compair.authorization',
        'ubc.ctlt.compair.attachment',
        'ubc.ctlt.compair.comment',
        'ubc.ctlt.compair.learning_records.learning_record',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.rich.content',
        'ubc.ctlt.compair.criterion',
        'ubc.ctlt.compair.group',
        'ubc.ctlt.compair.comparison',
        'ubc.ctlt.compair.toaster',
        'ubc.ctlt.compair.session'
    ]
);

var findEqualPartitions = function(items) {
    if (items.length <= 1) {
        return false;
    }
    return _findEqualPartitionsRecursive([], items);
};

var _findEqualPartitionsRecursive = function(partition1, partition2) {
    var sum1 = _.sum(partition1);
    var sum2 = _.sum(partition2);

    if (sum1 == sum2) {
        // found equal partitions
        return [partition1, partition2];
    } else if (sum1 > sum2 || partition2.length == 1) {
        // stop if sum1 is larger than sum2 (sum1 only grows)
        // or if last item in partition2
        return false;
    } else {
        // try moving every item from partition2 in partition1 recursively
        for(var index = 0; index < partition2.length; ++index) {
            var newPartition2 = angular.copy(partition2);
            newPartition1 = partition1.concat(newPartition2.splice(index, 1));
            var result = _findEqualPartitionsRecursive(newPartition1, newPartition2);
            if (result !== false) {
                return result;
            }
        }

        return false;
    }
};

module.constant('PairingAlgorithm', {
    adaptive: "adaptive",
    random: "random",
    adaptive_min_delta: "adaptive_min_delta"
});

/***** Directives *****/
module.directive(
    'confirmationNeeded',
    function () {
        return {
            priority: -100, //need negative priority to override ng-click
            restrict: 'A',
            link: function(scope, element, attrs){
                var msg = attrs.keyword ? " "+attrs.keyword : "";
                msg = "Do you want to permanently remove this"+msg+"?";
                if (attrs.confirmationWarning) {
                    msg += "\n"+attrs.confirmationWarning;
                }
                element.bind('click', function(e) {
                    if ( window.confirm(msg) ) {
                        scope.$eval(attrs.confirmationNeeded);
                        scope.$apply();
                    } else {
                        e.preventDefault();
                        e.stopImmediatePropagation();
                    }
                });
            }
        }
    }
);

module.directive(
    'getHeight',
    [ "$timeout",
    function($timeout) {
        return {
            restrict: 'A',
            link: function(scope, element) {
                // timeout creates delay letting text, images load into the div (answer content)
                $timeout(function(){
                    // find the element's scrollHeight (this tells us the full height regardless of max-height set)
                    scope.thisHeight = element.prop('scrollHeight');
                    // when this full height is outside the max-height, display the read more button to the user
                    if (scope.thisHeight >= 200) {
                        scope.showReadMore = true;
                    }
                }, 0);  // use a timeout of 0. will be evaluated at the next digest cycle
            }
        };
    }
]);

module.directive('comparisonPreview', function() {
    return {
        /* this template is our simple text with button to launch the preview */
        templateUrl: 'modules/assignment/preview-inline-template-comparison.html',
        controller:
                ["$scope", "$uibModal", "EditorOptions", "LearningRecordStatementHelper",
                function ($scope, $uibModal, EditorOptions, LearningRecordStatementHelper) {
            /* need to pass to comparison template all expected properties to complete the preview */
            $scope.previewComparisonPopup = function() {
                $scope.preview = true;
                /* set current round #, answer #s, and total round # for preview */
                $scope.current = 1;
                $scope.total = 0;
                $scope.forcePreventExit = true;
                if ($scope.assignment.number_of_comparisons > 0) {
                    $scope.total = $scope.assignment.number_of_comparisons;
                }
                if ($scope.assignment.addPractice) {
                    $scope.total++;
                }
                if ($scope.assignment.enable_self_evaluation) {
                    $scope.total++;
                }
                /* answer pair shown is dummy content, no files */
                $scope.answer1 = {
                    content: "<p>The first student answer in the pair will appear here, in text and/or file attachment, depending on how the answer was originally submitted.</p>",
                    file: null,
                    evaluation_number: 1
                }
                $scope.answer2 = {
                    content: "<p>The second student answer in the pair will appear here, in text and/or file attachment, depending on how the answer was originally submitted.</p>",
                    file: null,
                    evaluation_number: 2
                }
                $scope.comparison = {
                    comparison_criteria: []
                };
                $scope.comparison.id = '123';
                $scope.editor1Options = EditorOptions.simplified;
                $scope.editor2Options = EditorOptions.simplified;
                angular.forEach($scope.assignment.criteria, function(criterion) {
                    $scope.comparison.comparison_criteria.push({
                        'criterion_id': criterion.id,
                        'criterion': criterion,
                        'content': '',
                        'winner' : ''
                    });
                });

                //// default to showing answer pair at 50-50 split
                //$scope.expand = "none";
                //$scope.expandAnswer = function(whichOne) {
                //    
                //    //show the left or right answer full-width or go back to 50-50 default
                //    switch (whichOne) {
                //        case 'left':
                //            $scope.expand = "left";
                //            break;
                //        case 'right':
                //            $scope.expand = "right";
                //            break;
                //        default:
                //            $scope.expand = "none";
                //            break;
                //    }
                //    
                //};
                //
                ///* enable answer pair height buttons to start */
                //$scope.noShrink = false;
                //$scope.noGrow = false;
                //
                ///* to change answer pair height, find current height and add or substract set amount */
                //$scope.changeHeight = function(direction) {
                //    
                //    var answersList = document.getElementsByClassName('scrollable-answer');
                //    angular.forEach(answersList, function(elem) {
                //        
                //        var style = window.getComputedStyle(elem, null);
                //        var currentHeight = (style.getPropertyValue('height')).slice(0, -2);
                //        var growBy = 150;
                //        
                //        if (direction == "up") {
                //            newHeight = parseInt(currentHeight)+growBy;
                //            $scope.adjustHeight = { "height": newHeight + "px" };
                //        }
                //        if (direction == "down" && currentHeight > 200) {
                //            newHeight = parseInt(currentHeight)-growBy;
                //            $scope.adjustHeight = { "height": newHeight + "px" };
                //        }
                //        
                //        /* area cannot be less than 200px or more than 950p */
                //        if (newHeight <= 200) {
                //            $scope.noShrink = true;
                //            $scope.noGrow = false;
                //        } else {
                //            $scope.noShrink = false;
                //            $scope.noGrow = false;
                //        }
                //        if (newHeight >= 950) {
                //            $scope.noGrow = true;
                //        }
                //   
                //    });
                //
                //};

                /* student view preview is comparison template */
                $scope.modalInstance = $uibModal.open({
                    animation: true,
                    templateUrl: 'modules/comparison/comparison-modal-partial.html',
                    scope: $scope
                });
                $scope.modalInstance.opened.then(function() {
                    LearningRecordStatementHelper.opened_modal("Preview Comparison");
                });
                $scope.modalInstance.result.finally(function() {
                    LearningRecordStatementHelper.closed_modal("Preview Comparison");
                });
            }
        }]
    };
});

module.directive('selfEvalPreview', function() {
    return {
        /* this template is our simple text with button to launch the preview */
        templateUrl: 'modules/assignment/preview-inline-template-self-eval.html',
        controller:
                ["$scope", "$uibModal", "EditorOptions", "LearningRecordStatementHelper",
                function ($scope, $uibModal, EditorOptions, LearningRecordStatementHelper) {
            /* need to pass to self-eval template all expected properties to complete the preview */
            $scope.previewSelfEvalPopup = function() {
                $scope.selfEvalComment = true;
                $scope.preview = true;
                $scope.editorOptions = EditorOptions.simplified;
                $scope.instructions = $scope.assignment.self_eval_instructions ? $scope.assignment.self_eval_instructions:"Now write an evaluation of your own answer and <strong>give feedback to yourself</strong>, considering the other answers you've seen. What did you do well? Where might you improve?";
                $scope.parent = {
                    name: $scope.assignment.name ? $scope.assignment.name : "Assignment name will go here",
                    description: $scope.assignment.description ? $scope.assignment.description : "Assignment description will go here",
                    content: "The student's own answer will be provided here, in text and/or file attachment, depending on how the answer was originally submitted."
                }
                /* student view preview is self-eval template */
                $scope.modalInstance = $uibModal.open({
                    animation: true,
                    templateUrl: 'modules/comparison/comparison-self_evaluation-partial.html',
                    scope: $scope
                });
            }
        }]
    };
});


module.directive('assignmentActionButton', function() {

    return {
        restrict : 'E',
        scope: true,
        templateUrl: 'modules/common/element-button-template.html',
        replace: true,
        link: function ($scope, $element, $attributes) {
            $scope.actionElementName = $attributes.name;
        },
        controller: ["$scope", "$filter", "AssignmentPermissions",
            function ($scope, $filter, AssignmentPermissions) {
                $scope.$watchCollection("[assignment, assignment.status, actionElementName]", function(newStatus){

                    var permissions = AssignmentPermissions.getAll($scope.assignment, $scope.canManageAssignment, $scope.loggedInUserId);

                    if ($scope.assignment.status !== undefined) {

                        var assignmentId = $scope.assignment.id;
                        var assignmentStatus = $scope.assignment.status;
                        var assignment = $scope.assignment;
                        var courseId = $scope.course.id;
                        var course = $scope.course;

                        var allButtons = {
                            'answer' : {
                                'label' : "Answer",
                                'click' : $scope.openAnswerModal,
                                'clickargs' : {'assignment':assignment},
                                'title' : "Answer Assignment",
                                'show' : {
                                    'user'  : permissions.canAnswer && permissions.needsAnswer && !permissions.hasDraftAnswer,
                                    'instructor' : !permissions.hasDraftAnswer,
                                }
                            },
                            'finishAnswer' : {
                                'label' : "Finish Answer",
                                'click' : $scope.openAnswerModal,
                                'clickargs' : {'assignment':assignment, 'answerId':assignmentStatus.answers.draft_ids[0]},
                                'title' : "Finish Answering Assignment",
                                'show' : {
                                    'user'  : permissions.canAnswer && permissions.needsAnswer && permissions.hasDraftAnswer,
                                    'instructor' : permissions.hasDraftAnswer,
                                }
                            },
                            'compare' : {
                                'label' : ($scope.canManageAssignment || !permissions.hasDraftComparison) ? "Compare Pairs" : "Finish Comparison",
                                'href'  : "#/course/" + courseId +"/assignment/" + assignmentId + "/compare",
                                'title' : !permissions.hasComparisonsAvailable ? "No comparisons available" : ($scope.canManageAssignment || !permissions.hasDraftComparison) ? "Compare Pairs" : "Finish Comparison",
                                'disabled' : !permissions.hasComparisonsAvailable,
                                'show' : {
                                    'user' : permissions.canCompare && permissions.needsCompare,
                                    'instructor' : permissions.canCompare,
                                }
                            },
                            'selfEval' : {
                                'label' : !permissions.hasDraftSelfEval ? "Self-Evaluate" : "Finish Self-Eval",
                                'href'  : "#/course/" + courseId +"/assignment/" + assignmentId + "/self_evaluation",
                                'title' : !permissions.hasDraftSelfEval ? "Self-Evaluate" : "Finish Self-Eval",
                                'disabled' : !permissions.canSelfEval,
                                'show' : {
                                    'user' : permissions.needsSelfEval,
                                    'instructor' : false
                                }
                            },
                            'viewResults' : {
                                'label' : "See Results",
                                'href'  : "#/course/" + courseId +"/assignment/" + assignmentId,
                                'title' : "View Results",
                                'show' : {
                                    'user' : permissions.canViewAnswers,
                                    'instructor' : false
                                }
                            },
                        };

                        if (allButtons[$scope.actionElementName]) {
                            if ($scope.canManageAssignment && allButtons[$scope.actionElementName].show.instructor) {
                                $scope.button = allButtons[$scope.actionElementName];
                            }
                            else if (!$scope.canManageAssignment && allButtons[$scope.actionElementName].show.user) {
                                $scope.button = allButtons[$scope.actionElementName];
                            }
                            else {
                                $scope.button = { 'hide': true };
                            }
                        }
                    }
                    else {
                        $scope.button = { 'hide': true };
                    }
                });
            }
        ]
    };
});

module.directive('assignmentText', function() {

    return {
        restrict : 'E',
        scope: true,
        templateUrl: 'modules/common/element-text-template.html',
        replace: false,
        link: function ($scope, $element, $attributes) {
            $scope.textElementName = $attributes.name;
        },
        controller: ["$scope", "$filter", "AssignmentPermissions",
            function ($scope, $filter, AssignmentPermissions) {
                $scope.$watchCollection("[assignment, assignment.status, textElementName]", function(newStatus){

                    var permissions = AssignmentPermissions.getAll($scope.assignment, $scope.canManageAssignment, $scope.loggedInUserId);

                    if ($scope.assignment.status !== undefined) {

                        var assignment = $scope.assignment;

                        var allDirText = {
                            'answerDue' : {
                                'label' : "<em>Answer due </em> " + $filter('date')(assignment.answer_end, 'MMM d'),
                                'show' : {
                                    'user' : permissions.canAnswer && permissions.needsAnswer && assignment.answer_end,
                                    'instructor' : false
                                }
                            },
                            'comparisonsDue' : {
                                'label': "<em>Comparisons due </em> " + $filter('date')(assignment.compare_end, 'MMM d'),
                                'show' : {
                                    'user' : permissions.canCompare && permissions.needsCompare && assignment.compare_end,
                                    'instructor' : false
                                }
                            },
                            'selfEvalDue' : {
                                'label': "<em>Self-evaluation due </em> " + $filter('date')(assignment.self_eval_end, 'MMM d'),
                                'show' : {
                                    'user' : permissions.needsSelfEval && assignment.self_eval_end,
                                    'instructor' : false
                                }
                            },
                            'notEnoughAnswers'  : {
                                'label' : "Not enough answers to compare<br />(Refresh the page to check again)",
                                'show' : {
                                    'user' : permissions.canCompare && permissions.needsCompare && !permissions.hasComparisonsAvailable,
                                    'instructor' : permissions.canCompare && permissions.needsCompare && !permissions.hasComparisonsAvailable,
                                }
                            },
                            'noSelfEval' : {
                                'label': "Self-evaluation unavailable because you did not answer",
                                'show' : {
                                    'user' : permissions.needsSelfEval && !permissions.canSelfEval,
                                    'instructor' : false
                                }
                            },
                        };

                        if (allDirText[$scope.textElementName]) {
                            if ($scope.canManageAssignment && allDirText[$scope.textElementName].show.instructor) {
                                $scope.dirText = allDirText[$scope.textElementName];
                            }
                            else if (!$scope.canManageAssignment && allDirText[$scope.textElementName].show.user) {
                                $scope.dirText = allDirText[$scope.textElementName];
                            }
                            else {
                                $scope.dirText = { 'hide': true };
                            }
                        }
                    }
                    else {
                        $scope.dirText = { 'hide': true };
                    }
                });
            }
        ]
    };
});

module.directive('assignmentMetadata', function() {

    return {
        restrict : 'E',
        scope: true,
        templateUrl: 'modules/common/element-metadata-template.html',
        replace: true,
        link: function ($scope, $element, $attributes) {
            $scope.metadataName = $attributes.name;
        },
        controller: ["$scope", "$filter", "AssignmentPermissions",
            function ($scope, $filter, AssignmentPermissions) {
                $scope.$watchCollection("[assignment, assignment.status, metadataName]", function(newStatus){

                    var permissions = AssignmentPermissions.getAll($scope.assignment, $scope.canManageAssignment, $scope.loggedInUserId);

                    if ($scope.assignment.status !== undefined) {

                        var assignmentId = $scope.assignment.id;
                        var assignmentStatus = $scope.assignment.status;
                        var assignment = $scope.assignment;
                        var courseId = $scope.course.id;
                        var course = $scope.course;

                        var allMetadata = {
                            'editLink' : {
                                'label' : "Edit",
                                'href'  : "#/course/" + courseId + "/assignment/" + assignment.id + "/edit",
                                'show' : {
                                    'user'  : permissions.isOwner,
                                    'instructor'  : true,
                                }
                            },
                            'duplicateLink' : {
                                'label': "Duplicate",
                                'href' : "#/course/" + courseId + "/assignment/" + assignment.id + "/duplicate",
                                'show' : {
                                    'user'  : false,
                                    'instructor' : true,
                                }
                            },
                            'answerCount' : {
                                'label': assignment.answer_count + " answer" + (assignment.answer_count != 1 ? "s" : "") + " &raquo;",
                                'href' : "#/course/" + courseId + "/assignment/" + assignment.id +"/?tab=answers#answers",
                                'show' : {
                                    'user' : permissions.canViewAnswers,
                                    'instructor' : true
                                }
                            },
                            'answeringDates' : {
                                'label': "<em>Answering:</em> " + function() {
                                    if (assignment.answer_start) {
                                        return $filter('date')(assignment.answer_start, 'MMM d @ h:mm a') + " - " + $filter('date')(assignment.answer_end, 'MMM d @ h:mm a');
                                    }
                                    return "NOT SET";
                                }(),
                                'show' : {
                                    'user'  : false,
                                    'instructor' : true,
                                }
                            },
                            'comparingDates' : {
                                'label': "<em>Comparing:</em> " + function() {
                                    if (assignment.compare_start) {
                                        return $filter('date')(assignment.compare_start, 'MMM d @ h:mm a') + " - " + $filter('date')(assignment.compare_end, 'MMM d @ h:mm a');
                                    }
                                    else if (assignment.answer_end) {
                                        return "starting " + $filter('date')(assignment.answer_end, 'MMM d @ h:mm a');
                                    }
                                    return "NOT SET";
                                }(),
                                'show' : {
                                    'user'  : false,
                                    'instructor' : true,
                                }
                            },
                            'selfEvalDates' : {
                                'label': "<em>Self-Evaluating:</em> " + function() {
                                    if (assignment.self_eval_start) {
                                        return $filter('date')(assignment.self_eval_start, 'MMM d @ h:mm a') + " - " + $filter('date')(assignment.self_eval_end, 'MMM d @ h:mm a');
                                    }
                                    else if (assignment.compare_start) {
                                        return "starting " + $filter('date')(assignment.compare_start, 'MMM d @ h:mm a');
                                    }
                                    else if (assignment.answer_end) {
                                        return "starting " + $filter('date')(assignment.answer_end, 'MMM d @ h:mm a');
                                    }
                                    return "NOT SET";
                                }(),
                                'show' : {
                                    'user'  : false,
                                    'instructor' : assignment.enable_self_evaluation,
                                }
                            },
                            'answerCountEmpty' : {
                                'label': "Answers not yet available",
                                'show' : {
                                    'user' : !permissions.canViewAnswers,
                                    'instructor'  : false,
                                }
                            },
                            'compareCount' : {
                                'label': assignment.evaluation_count + " comparison" + (assignment.evaluation_count != 1 ? "s" : "") + " &raquo;",
                                'href' : "#/course/" + courseId + "/assignment/" + assignment.id +"/?tab=comparisons#comparisons",
                                'show' : {
                                    'user'  : false,
                                    'instructor' : true,
                                }
                            },
                            'feedbackCount' : {
                                'label': assignment.status.answers.feedback + " feedback comment" + (assignment.status.answers.feedback != 1 ? "s" : "") + " &raquo;",
                                'href' : "#/course/" + courseId + "/assignment/" + assignment.id +"/?tab=your_feedback",
                                'show' : {
                                    'user' : permissions.hasFeedback,
                                    'instructor'  : false,
                                }
                            },
                            'feedbackCountBelow' : {
                                'label': "<strong>" + assignment.status.answers.feedback + " feedback comment" + (assignment.status.answers.feedback != 1 ? "s" : "") + "</strong> below",
                                'show' : {
                                    'user' : permissions.hasFeedback,
                                    'instructor'  : false,
                                }
                            },
                            'feedbackCountEmpty' : {
                                'label': "No feedback received",
                                'show' : {
                                    'user' : !permissions.hasFeedback,
                                    'instructor'  : false,
                                }
                            },
                            'completedFeedback' : {
                                'label': function(){
                                    var completed = [];
                                    if (!permissions.needsAnswer) {
                                        completed.push("<strong>answered</strong>");
                                    }
                                    if (permissions.hasCompared) {
                                        completed.push("<strong>compared " + assignment.status.comparisons.count + " pair" + (assignment.status.comparisons.count != 1 ? "s" : "") + "</strong>");
                                    }
                                    if (assignment.enable_self_evaluation && permissions.hasSelfEvaluated) {
                                        completed.push((completed.length > 1 ? "and " : "") + "<strong>self-evaluated</strong>");
                                    }
                                    return "You " + completed.join(completed.length > 2 ? ", " : " and ");
                                }(),
                                'show' : {
                                    'user' : permissions.hasCompared || !permissions.needsAnswer || (assignment.enable_self_evaluation && permissions.hasSelfEvaluated),
                                    'instructor'  : false,
                                }
                            },
                            'missedFeedback' : {
                                'label': function(){
                                    var missed = [];
                                    if (permissions.hasMissedAnswer) {
                                        missed.push("answering");
                                    }
                                    if (permissions.hasMissedCompare) {
                                        missed.push("comparing " + (permissions.needsCompare ? assignment.status.comparisons.left + " pair" + (assignment.status.comparisons.left != 0 ? "s" : "") : ""));
                                    }
                                    if (assignment.enable_self_evaluation && permissions.hasMissedSelfEval) {
                                        missed.push((missed.length > 1 ? "and " : "") + "self-evaluating");
                                    }
                                    return "You missed " + missed.join(missed.length > 2 ? ", " : " and ");
                                }(),
                                'show' : {
                                    'user' : permissions.hasMissedAnswer || permissions.hasMissedCompare || (assignment.enable_self_evaluation && permissions.hasMissedSelfEval),
                                    'instructor'  : false,
                                }
                            },
                            'missingFeedback' : {
                                'label': function(){
                                    var missing = [];
                                    if (permissions.canAnswer && permissions.needsAnswer) {
                                        missing.push("1 answer");
                                    }
                                    if (permissions.isComparePeriod && permissions.needsCompare) {
                                        missing.push(assignment.status.comparisons.left + " comparison" + (assignment.status.comparisons.left != 1 ? "s" : ""));
                                    }
                                    if (permissions.canSelfEval && permissions.needsSelfEval) {
                                        missing.push((missing.length > 1 ? "and a " : "") + "self-evaluation");
                                    }
                                    return missing.join(missing.length > 2 ? ", " : " and ") + " needed";
                                }(),
                                'class': 'label label-warning',
                                'show' : {
                                            // suggested: (canAnswer && needsAnswer) || (>>>> canCompare <<<< && needsCompare)
                                    'user' : (permissions.canAnswer && permissions.needsAnswer) ||
                                             (permissions.isComparePeriod && permissions.needsCompare) ||
                                             (permissions.canSelfEval && permissions.needsSelfEval),
                                    'instructor'  : false,
                                }
                            },
                            'missingComparisonsFeedback' : {
                                'label': assignment.status.comparisons.left + " comparison" + (assignment.status.comparisons.left != 1 ? "s" : "") + " needed",
                                'class': 'label label-warning',
                                'show' : {
                                            // suggested: >>>> canCompare <<<< && needsCompareOrSelfEval && !hasCompareDueDate
                                    'user' : permissions.isComparePeriod && permissions.needsCompare && !permissions.hasCompareDueDate,
                                    'instructor'  : false,
                                }
                            },
                            'missingSelfEvalFeedback' : {
                                'label': "Self-evaluation needed",
                                'class': 'label label-warning',
                                'show' : {
                                    'user' : !permissions.isComparePeriod && permissions.isSelfEvalPeriod && permissions.needsSelfEval && !permissions.hasSelfEvalDueDate,
                                    'instructor'  : false,
                                }
                            },
                            'answerDue' : {
                                'label': assignment.answer_end ? "Answer due: " + $filter('date')(assignment.answer_end, 'MMM d @ h:mm a') : "",
                                'class': 'label label-warning',
                                'show' : {
                                    'user' : permissions.canAnswer && permissions.needsAnswer,
                                    'instructor'  : false,
                                }
                            },
                            'comparisonsDue' : {
                                'label': assignment.compare_end ? "Comparisons due: " + $filter('date')(assignment.compare_end, 'MMM d @ h:mm a') : "",
                                'class': 'label label-warning',
                                'show' : {
                                            // suggested: >>>> canCompare <<<< && needsCompare && hasCompareDueDate
                                    'user' : permissions.isComparePeriod && permissions.needsCompare && permissions.hasCompareDueDate,
                                    'instructor'  : false,
                                }
                            },
                            'selfEvalDue' : {
                                'label': assignment.self_eval_end ? "Self-evaluation due: " + $filter('date')(assignment.self_eval_end, 'MMM d @ h:mm a') : "",
                                'class': 'label label-warning',
                                'show' : {
                                    'user' : permissions.isSelfEvalPeriod && permissions.needsSelfEval && permissions.hasSelfEvalDueDate,
                                    'instructor'  : false,
                                }
                            },
                            'assignmentScheduled' : {
                                'label': function(){
                                    var selfEvalAfterCompare = assignment.compare_start < assignment.self_eval_start && (assignment.compare_start < assignment.self_eval_start);
                                    if (permissions.isAfterAnswerDue) {
                                        if (permissions.hasCompareDueDate && (selfEvalAfterCompare || !permissions.hasSelfEvalDueDate)) {
                                            return "Comparing scheduled for " + $filter('date')(assignment.compare_start, 'MMM d');
                                        }
                                        else if (permissions.hasSelfEvalDueDate) {
                                            return "Self-evaluation scheduled for " + $filter('date')(assignment.self_eval_start, 'MMM d');
                                        }
                                        return "Comparing not scheduled";
                                    }
                                    else {
                                        return "Scheduled for " + $filter('date')(assignment.answer_start, 'MMM d');
                                    }
                                }(),
                                'show' : {
                                    'user'  : false,
                                    'instructor' : !permissions.isAnswerPeriod && !permissions.isComparePeriod && !permissions.isSelfEvalPeriod && !permissions.canViewAnswers,
                                }
                            },
                            'periodLabel' : {
                                'label': function(){
                                    var periods = [];
                                    if (permissions.isAnswerPeriod) {
                                        periods.push("Answer");
                                    }
                                    if (permissions.isComparePeriod) {
                                        periods.push("Comparison");
                                    }
                                    if (permissions.isSelfEvalPeriod) {
                                        periods.push("Self-Evaluation");
                                    }
                                    return periods.join(" / ") + " period";
                                }(),
                                'class': 'label label-warning',
                                'show' : {
                                    'user'  : false,
                                    'instructor' : permissions.isAnswerPeriod || permissions.isComparePeriod,
                                }
                            },
                            'assignmentCompleted' : {
                                'label': "Completed on " + $filter('date')(assignment.compare_end, 'MMM d'),
                                'show' : {
                                    'user'  : false,
                                    'instructor' : !permissions.isAnswerPeriod && !permissions.isComparePeriod && permissions.canViewAnswers,
                                }
                            },
                            'deleteLink' : {
                                'label': 'Delete',
                                'title' : "Delete",
                                'class' : 'pointer',
                                'confirmationNeeded' : 'deleteAssignment(assignment)' ,
                                'confirmationWarning': assignment.delete_warning,
                                'keyword' : "assignment",
                                'show' : {
                                    'user'  : permissions.isOwner,
                                    'instructor'  : true,
                                }
                            }
                        };

                        if (allMetadata[$scope.metadataName]) {
                            if ($scope.canManageAssignment && allMetadata[$scope.metadataName].show.instructor) {
                                $scope.meta = allMetadata[$scope.metadataName];
                            }
                            else if (!$scope.canManageAssignment && allMetadata[$scope.metadataName].show.user) {
                                $scope.meta = allMetadata[$scope.metadataName];
                            }
                            else {
                                $scope.meta = { 'hide': true };
                            }
                        }
                    }
                    else {
                        $scope.meta = { 'hide': true };
                    }
                });
            }
        ]
    };
});

/***** Providers *****/
module.factory(
    "AssignmentResource",
    [ "$resource", "Interceptors",
    function ($resource, Interceptors)
    {
        var url = '/api/courses/:courseId/assignments/:assignmentId';
        var ret = $resource(url, {assignmentId: '@id'},
            {
                'get': {url: url}, //, cache: true},
                'save': {method: 'POST', url: url, interceptor: Interceptors.cache},
                'delete': {method: 'DELETE', url: url, interceptor: Interceptors.cache},
                'getCurrentUserStatus': {url: '/api/courses/:courseId/assignments/:assignmentId/status'},
                'getCurrentUserComparisons': {url: '/api/courses/:courseId/assignments/:assignmentId/user/comparisons'},
                'getUserComparisons': {url: '/api/courses/:courseId/assignments/:assignmentId/users/comparisons'}
            }
        );
        ret.MODEL = "Assignment";
        return ret;
    }
]);

module.factory(
    "ComparisonExampleResource",
    [ "$resource",
    function ($resource)
    {
        var url = '/api/courses/:courseId/assignments/:assignmentId/comparisons/examples/:comparisonExampleId';
        var ret = $resource(url, {comparisonExampleId: '@id'},
            {
                'get': {url: url},
                'save': {method: 'POST', url: url},
                'delete': {method: 'DELETE', url: url}
            }
        );
        ret.MODEL = "ComparisonExample";
        return ret;
    }
]);

module.factory( "AssignmentPermissions", function (){

    return {
        'getAll' : function(assignment, canManageAssignment, loggedInUserId) {
            var permissions = {};

            if (assignment.status) {

                // ensure dates are formatted properly for date comparison
                if (!(assignment.answer_end instanceof Date) && assignment.answer_end) {
                    assignment.answer_end = new Date(assignment.answer_end);
                }
                if (!(assignment.compare_end instanceof Date) && assignment.compare_end) {
                    assignment.compare_end = new Date(assignment.compare_end);
                }
                if (!(assignment.self_eval_end instanceof Date) && assignment.self_eval_end) {
                    assignment.self_eval_end = new Date(assignment.self_eval_end);
                }

                // used below
                var isAfterAnswer = (
                    // either (the answer period is active AND the assignment has been answered) OR the answer period is not active
                    (assignment.answer_period && assignment.status.answers.answered) || !assignment.answer_period );

                permissions = {

                    // answer
                    'isAnswerPeriod'    : assignment.answer_period,
                    'canAnswer'         : assignment.answer_period,
                    'canViewAnswers'    : assignment.see_answers,
                    'needsAnswer'       : !assignment.status.answers.answered,
                    'hasDraftAnswer'    : assignment.status.answers.has_draft,
                    'hasFeedback'       : assignment.status.answers.feedback,
                    'isAfterAnswerDue'  : !assignment.answer_period && assignment.answer_end && assignment.answer_end < new Date(),

                    // compare
                    'isComparePeriod'   : assignment.compare_period,
                    'canCompare'        : assignment.compare_period &&
                                          (
                                            // regular users
                                            (!canManageAssignment && isAfterAnswer) ||
                                            // instructors
                                            (canManageAssignment && assignment.educators_can_compare)
                                          ),
                    'needsCompare'      : assignment.status.comparisons.left > 0,
                    'hasDraftComparison': assignment.status.comparisons.has_draft,
                    'hasComparisonsAvailable': assignment.status.comparisons.available,
                    'hasCompared'       : assignment.status.comparisons.count > 0,
                    'isAfterCompareDue' : !assignment.compare_period && assignment.compare_end && assignment.compare_end < new Date(),
                    'hasCompareDueDate' : assignment.compare_end,

                    // self-eval (some additions defined below)
                    'isSelfEvalPeriod'  : assignment.self_eval_period,
                    'canSelfEval'       : assignment.status.answers.answered,
                    'needsSelfEval'     : assignment.enable_self_evaluation && assignment.self_eval_period && !canManageAssignment
                                            && !assignment.status.comparisons.self_evaluation_completed, // conditional additions below
                    'hasDraftSelfEval'  : assignment.status.comparisons.self_evaluation_draft,
                    'hasSelfEvaluated'  : assignment.status.self_evaluation_completed,
                    'hasSelfEvalDate'   : assignment.self_eval_start,
                    'hasSelfEvalDueDate': assignment.self_eval_end,
                    'isAfterSelfEvalDue': false, // defined below

                    // general / mixed
                    'isOwner': (assignment.user_id == loggedInUserId),
                    'isAvailable': assignment.available,
                }

                if (permissions.hasSelfEvalDate) {
                    permissions.isAfterSelfEvalDue = assignment.self_eval_end < new Date();
                }
                else {
                    permissions.isAfterSelfEvalDue = permissions.isAfterCompareDue;

                    if (permissions.hasCompareDueDate && permissions.isComparePeriod) {
                        permissions.needsSelfEval &= assignment.status.comparisons.left == 0;
                    }
                }

                permissions.hasMissedAnswer = permissions.isAfterAnswerDue && permissions.needsAnswer;
                permissions.hasMissedCompare = permissions.isAfterCompareDue && permissions.needsCompare;
                permissions.hasMissedSelfEval = assignment.enable_self_evaluation && permissions.isAfterSelfEvalDue && !assignment.status.comparisons.self_evaluation_completed;
            }

            return permissions;
        }
    }
});

/***** Filters *****/
module.filter("excludeInstr", function() {
    return function(items, instructors) {
        var filtered = [];
        angular.forEach(items, function(item) {
            // exclude instructor answer unless it is comparable
            if (!_.find(instructors, {id: item.user_id}) || item.comparable) {
                filtered.push(item);
            }
        });
        return filtered;
    };
});

module.filter("notScoredEnd", function () {
    return function (array) {
        if (!angular.isArray(array)) return;
        var scored = [];
        var not_scored = [];
        angular.forEach(array, function(item) {
            if (item.score) {
                scored.push(item);
            } else {
                not_scored.push(item);
            }
        });
        return scored.concat(not_scored);
    }
});

/***** Assignment Search EndDate Controllers *****/
module.controller("AssignmentSearchEndDateController",
    ["$scope", function($scope){

            $scope.searchDate = function() {
                var formatDate = new Date($scope.dt);
                getObjectDate(formatDate.toLocaleDateString('en-ca', { year: 'numeric' }) + "-" + formatDate.toLocaleDateString('en-ca', { month: '2-digit' }) + "-" + formatDate.toLocaleDateString('en-ca', { day: '2-digit' }));
            };

}]);


/***** Controllers *****/
module.controller("AssignmentViewController",
    ["$scope", "$routeParams", "$location", "AnswerResource", "AssignmentResource", "$anchorScroll",
             "ComparisonResource", "CourseResource", "Toaster", "AnswerCommentResource", "resolvedData", "$route",
             "GroupResource", "GroupUserResource", "AnswerCommentType", "PairingAlgorithm", "$uibModal",
             "LearningRecordStatementHelper", "WinningAnswer",
    function($scope, $routeParams, $location, AnswerResource, AssignmentResource, $anchorScroll,
             ComparisonResource, CourseResource, Toaster, AnswerCommentResource, resolvedData, $route,
             GroupResource, GroupUserResource, AnswerCommentType, PairingAlgorithm, $uibModal,
             LearningRecordStatementHelper, WinningAnswer)
    {
        $scope.courseId = $routeParams.courseId;
        $scope.assignmentId = $routeParams.assignmentId;

        $scope.loggedInUserId = resolvedData.loggedInUser.id;
        $scope.course = resolvedData.course;
        $scope.assignment = resolvedData.assignment;
        $scope.canManageAssignment = resolvedData.canManageAssignment;
        $scope.allStudents = resolvedData.students.objects;
        $scope.allInstructors = resolvedData.instructors.objects;
        $scope.currentUserGroup = resolvedData.currentUserGroup;
        $scope.users = [];

        $scope.AnswerCommentType = AnswerCommentType;
        $scope.PairingAlgorithm = PairingAlgorithm;
        var params = {
            courseId: $scope.courseId,
            assignmentId: $scope.assignmentId
        };
        $scope.totalNumAnswers = 0;
        $scope.answerFilters = {
            page: 1,
            perPage: 20,
            group: null,
            author: null,
            top: null,
            anonymous: null,
            orderBy: null
        };
        $scope.totalNumComparisonsShown = {
            count: $scope.assignment.evaluation_count
        };
        $scope.comparisonFilters = {
            page: 1,
            perPage: 5,
            group: null,
            author: null
        };
        $scope.rankLimit = null;
        $scope.WinningAnswer = WinningAnswer;
        var tab = $location.search().tab || 'answers';

        // setup assignment data
        $scope.assignment.answer_start = new Date($scope.assignment.answer_start);
        $scope.assignment.answer_end = new Date($scope.assignment.answer_end);
        if ($scope.assignment.compare_start != null) {
            $scope.assignment.compare_start = new Date($scope.assignment.compare_start);
        }
        if ($scope.assignment.compare_end != null) {
            $scope.assignment.compare_end = new Date($scope.assignment.compare_end);
        }
        if ($scope.assignment.self_eval_start != null) {
            $scope.assignment.self_eval_start = new Date($scope.assignment.self_eval_start);
        }
        if ($scope.assignment.self_eval_end != null) {
            $scope.assignment.self_eval_end = new Date($scope.assignment.self_eval_end);
        }
        if ($scope.assignment.rank_display_limit) {
            $scope.rankLimit = $scope.assignment.rank_display_limit;
        }
        $scope.readDate = Date.parse($scope.assignment.created);
        if ($scope.assignment.compare_end) {
            $scope.answerAvail = $scope.assignment.compare_end;
        } else {
            $scope.answerAvail = $scope.assignment.answer_end;
        }

        $scope.openAnswerModal = function($args) {

            var modalScope = $scope.$new();
            modalScope.assignment = $args.assignment;
            modalScope.courseId = angular.copy($scope.courseId);
            modalScope.assignmentId = angular.copy($args.assignment.id);

            modalScope.course = $scope.course;
            modalScope.answer = {};
            modalScope.loggedInUserId = resolvedData.loggedInUser.id;
            modalScope.canManageAssignment = resolvedData.canManageAssignment;

            if ($args.answerId) {
                modalScope.answerId = $args.answerId;
                AnswerResource.get({'courseId': modalScope.courseId, 'assignmentId': modalScope.assignmentId, 'answerId': modalScope.answerId}).$promise.then(
                    function (ret) {
                        modalScope.answer = ret;
                        $scope.modalInstance = $uibModal.open({
                            animation: true,
                            backdrop: 'static',
                            controller: "AnswerWriteModalController",
                            templateUrl: 'modules/answer/answer-modal-partial.html',
                            scope: modalScope
                        });
                    }
                );
            }
            else {
                $scope.modalInstance = $uibModal.open({
                    animation: true,
                    backdrop: 'static',
                    controller: "AnswerWriteModalController",
                    templateUrl: 'modules/answer/answer-modal-partial.html',
                    scope: modalScope
                });
            }

        }

        AssignmentResource.getCurrentUserStatus({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}).$promise.then(
            function(ret) {
                $scope.assignment.status = ret.status;

                $scope.comparisons_left = $scope.assignment.status.comparisons.left;

                if ($scope.assignment.compare_end) {
                    // if comparison period is set answers can be seen after it ends
                    $scope.see_answers = $scope.assignment.after_comparing;
                } else {
                    // if an comparison period is NOT set - answers can be seen after req met
                    $scope.see_answers = $scope.assignment.after_comparing && $scope.comparisons_left == 0;
                }
            }
        )

        if ($scope.canManageAssignment) {
            GroupResource.get({'courseId': $scope.courseId}, function (ret) {
                $scope.groups = ret.objects;
            });
        }

        $scope.adminFilter = function() {
            return function (answer) {
                // true for non-comparable instructor/TA answer
                return _.find($scope.allInstructors, {id: answer.user_id}) && !answer.comparable;
            }
        };

        $scope.isInstructor = function(user_id) {
            return _.find($scope.allInstructors, {id: user_id});
        }

        $scope.instructorLabel = function(user_id) {
            var instructor = _.find($scope.allInstructors, {id: user_id});
            return instructor ? instructor.role : "";
        }

        //TODO: this filter should be implemented in backend
        $scope.commentFilter = function(answer) {
            return function (comment) {
                // can see if canManageAssignment OR their own answer OR public
                return $scope.canManageAssignment ||
                    answer.user_id == $scope.loggedInUserId ||
                    ($scope.currentUserGroup && answer.group_id == $scope.currentUserGroup.id) ||
                    comment.comment_type == AnswerCommentType.public;
            }
        };

        $scope.setTab = function(name) {
            $scope.highlightAnswer = undefined; // no need to highlight again when switching tabs
            $location.search('tab', name);
            LearningRecordStatementHelper.closed_page_section(tab + " tab");
        };

        $scope.showTab = function(name) {
            return tab == name;
        };

        // Handle $location.search as a soft reload
        // $routeProvider reloadOnSearch: false for this controller
        $scope.$on('$routeUpdate',function(e) {
            tab = $location.search().tab || 'answers';
            $scope.loadTabData();
        });

        // Highlight the answer if it's in the URL
        $scope.highlightAnswer = $location.search().highlightAnswer;
        if ($scope.highlightAnswer) {
            $location.hash('answers');
            $anchorScroll();
        }

        $scope.loadTabData = function() {
            // tabs: answers, participation, your_feedback, your_comparisons, comparisons
            if (tab == "your_feedback") {
                var answer_params = angular.extend({}, params, {author: $scope.loggedInUserId});
                $scope.user_answers = AnswerResource.get(answer_params,
                    function (ret) {
                        ret.objects.forEach(function(answer) {
                            $scope.loadComments(answer);
                        });
                    }
                );
            } else if (tab == "your_comparisons") {
                $scope.comparison_set = AssignmentResource.getCurrentUserComparisons(params);
            }
            LearningRecordStatementHelper.opened_page_section(tab + " tab");
        };
        $scope.loadTabData();

        // revealContent function shows full answer content for abbreviated answers (determined by getHeight directive)
        $scope.revealContent = function(contentItem) {
            var thisClass = '.' + contentItem.id + ' .content';      // class for the content item to show is the content item's ID plus "content"
            $(thisClass).css({'max-height' : 'none'}); // now remove height restriction for this content item
            this.showReadMore = false;                 // and hide the read more button for this content item
        };

        $scope.deleteAnswer = function(answer) {
            AnswerResource.delete({'courseId': answer.course_id, 'assignmentId': answer.assignment_id, 'answerId':answer.id},
                function (ret) {
                    var authorId = answer['user_id'];
                    var groupId = answer['group_id'];
                    $scope.assignment.answer_count -= 1;
                    if ($scope.loggedInUserId == authorId || ($scope.currentUserGroup && $scope.currentUserGroup.id == groupId)) {
                        $scope.assignment.status.answers.count--;
                        $scope.assignment.status.answers.answered = $scope.assignment.status.answers.count > 0;
                    }
                    $scope.updateAnswerList();
                    $scope.loadTabData();
                    Toaster.success("Answer Deleted");
                }
            );
        };

        // toggle top_answer state for answer
        $scope.setTopAnswer = function(answer, topAnswer) {
            var params = {'top_answer': topAnswer};
            AnswerResource.topAnswer({'courseId': answer.course_id, 'assignmentId': answer.assignment_id, 'answerId':answer.id}, params).$promise.then(
                function () {
                    answer.top_answer = topAnswer;
                    if (topAnswer) {
                        Toaster.success("Answer Added To Top Answers", "Students will see this in the list of instructor-picked answers.");
                    } else {
                        Toaster.success("Answer Removed From Top Answers", "Students will no longer see this in the list of instructor-picked answers.");
                    }
                    if ($scope.answerFilters.author == "top-picks") {
                        $scope.updateAnswerList();
                    }
                }
            );
        };

        $scope.editAnswer = function(answer) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignmentId;
            modalScope.assignment = angular.copy($scope.assignment);
            modalScope.answer = angular.copy(answer);

            $scope.modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "AnswerWriteModalController",
                templateUrl: 'modules/answer/answer-modal-partial.html',
                scope: modalScope
            });
            $scope.modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal("Edit Answer");
            });
            $scope.modalInstance.result.then(function (answerUpdated) {
                _.each($scope.answers.objects, function(answer, index) {
                    if (answer.id == answerUpdated.id) {
                        // copy answer comments over to updated answer before
                        // overwriting answer with update
                        answerUpdated.comments = answer.comments;
                        $scope.answers.objects[index] = answerUpdated;
                    }
                });
                LearningRecordStatementHelper.closed_modal("Edit Answer");
            }, function() {
                LearningRecordStatementHelper.closed_modal("Edit Answer");
            });
        };

        $scope.createAnswerComment = function(answer) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignmentId;
            modalScope.answerId = answer.id;

            $scope.modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "AnswerCommentModalController",
                templateUrl: 'modules/comment/comment-answer-modal-partial.html',
                scope: modalScope
            });
            $scope.modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal("Create Answer Comment");
            });
            $scope.modalInstance.result.then(function (newComment) {
                answer.comments = typeof(answer.comments) != 'undefined' ? answer.comments : [];
                answer.comments.unshift(newComment)
                if (newComment.comment_type == AnswerCommentType.public) {
                    answer.public_comment_count++;
                } else {
                    answer.private_comment_count++;
                }
                answer.comment_count++;
                LearningRecordStatementHelper.closed_modal("Create Answer Comment");
            }, function() {
                LearningRecordStatementHelper.closed_modal("Create Answer Comment");
            });
        };

        $scope.editAnswerComment = function(answer, comment) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignmentId;
            modalScope.answerId = answer.id;
            modalScope.comment = angular.copy(comment);

            $scope.modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "AnswerCommentModalController",
                templateUrl: 'modules/comment/comment-answer-modal-partial.html',
                scope: modalScope
            });
            $scope.modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal("Edit Answer Comment");
            });
            $scope.modalInstance.result.then(function (updatedComment) {
                // update comment counts
                if (comment.comment_type == AnswerCommentType.public) {
                    answer.public_comment_count--;
                } else {
                    answer.private_comment_count--;
                }
                if (updatedComment.comment_type == AnswerCommentType.public) {
                    answer.public_comment_count++;
                } else {
                    answer.private_comment_count++;
                }

                // update comment
                _.each(answer.comments, function(comment, index) {
                    if (comment.id == updatedComment.id) {
                        answer.comments[index] = updatedComment;
                    }
                });
                LearningRecordStatementHelper.closed_modal("Edit Answer Comment");
            }, function() {
                LearningRecordStatementHelper.closed_modal("Edit Answer Comment");
            });
        };

        $scope.toggleReplies = function(showReplies, answer) {
            if (showReplies) {
                $scope.loadComments(answer);
                LearningRecordStatementHelper.opened_answer_replies_section(answer);
            } else {
                LearningRecordStatementHelper.closed_answer_replies_section(answer);
            }
        };

        $scope.loadComments = function(answer) {
            answer.comments = AnswerCommentResource.query({
                courseId: $scope.courseId,
                assignmentId: $scope.assignmentId,
                answer_ids: answer.id
            });
        };

        $scope.deleteReply = function(answer, commentKey, course_id, assignment_id, answer_id, comment_id) {
            AnswerCommentResource.delete({'courseId': course_id, 'assignmentId': assignment_id, 'answerId': answer_id, 'commentId': comment_id},
                function (ret) {
                    Toaster.success("Reply Deleted");
                    var comment = answer['comments'].splice(commentKey, 1)[0];
                    if (comment.comment_type == AnswerCommentType.public) {
                        answer.public_comment_count--;
                    } else {
                        answer.private_comment_count--;
                    }
                    answer.comment_count--;
                }
            );
        };

        $scope.resetUsers = function(instructors, students, addTopPicks) {
            addTopPicks = addTopPicks !== undefined ? addTopPicks : true;
            instructors = _.sortBy(instructors, 'name');
            students = _.sortBy(students, 'name');
            $scope.users = [].concat(instructors, students);
            if (addTopPicks) {
                $scope.users.unshift({
                    id: "top-picks",
                    name: "Instructor's top picks"
                });
            }
        };

        $scope.updateAnswerList = function() {
            var params = angular.merge({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $scope.answerFilters);
            $scope.answerFiltersName = $("#answers-filter option:selected").text();
            delete params.anonymous;
            if (params.author == "top-picks") {
                delete params.author;
            }
            $scope.answers = AnswerResource.get(params, function(response) {
                $scope.totalNumAnswers = response.total;

                $scope.rankCount = {};
                angular.forEach(response.objects, function(answer) {
                    if (answer.score && $scope.answerFilters.orderBy=='score') {
                        if ($scope.rankCount[answer.score.rank] == undefined) {
                            $scope.rankCount[answer.score.rank] = 1;
                        } else {
                            ++$scope.rankCount[answer.score.rank];
                        }
                    };
                });
            });
        };
        $scope.updateAnswerList();
        $scope.resetUsers($scope.allInstructors, $scope.allStudents);

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.group != newValue.group) {
                if ($scope.answerFilters.author != "top-picks") {
                    $scope.answerFilters.author = null;
                }
                if ($scope.answerFilters.group == null) {
                    $scope.resetUsers($scope.allInstructors, $scope.allStudents);
                } else {
                    GroupUserResource.get({'courseId': $scope.courseId, 'groupId': $scope.answerFilters.group},
                        function (ret) {
                            $scope.resetUsers([], ret.objects, false);
                        }
                    );
                }
                $scope.answerFilters.page = 1;
            }
            if (oldValue.author != newValue.author) {
                $scope.answerFilters.top = null;
                if ($scope.answerFilters.author == "top-picks") {
                    $scope.answerFilters.top = true;
                    $scope.answerFilters.orderBy = null;
                }
                $scope.answerFilters.page = 1;
            }
            if (oldValue.top != newValue.top || oldValue.orderBy != newValue.orderBy) {
                $scope.answerFilters.page = 1;
            }

            if ($scope.answerFilters.anonymous == true) {
                if (_.includes(["top-picks", '', null], $scope.answerFilters.author )) {
                    $('#answers_filter_chosen .chosen-single span').show();
                } else {
                    $('#answers_filter_chosen .chosen-single span').hide();
                }
            } else {
                $('#answers_filter_chosen .chosen-single span').show();
            }

            LearningRecordStatementHelper.filtered_page_section(tab+" tab", $scope.answerFilters);

            $scope.updateAnswerList();
        };
        // register watcher here so that we start watching when all filter values are set
        $scope.$watchCollection('answerFilters', filterWatcher);
    }
]);
module.controller("AssignmentWriteController",
    [ "$scope", "$q", "$location", "$routeParams", "$route", "AssignmentResource", "$uibModal",
             "CriterionResource", "required_rounds", "Toaster", "attachService", "UploadValidator",
             "EditorOptions", "PairingAlgorithm", "ComparisonExampleResource",
             "AnswerResource", "LearningRecordStatementHelper", "resolvedData", "moment",
             "embeddableRichContent", "$http", "answerAttachService",
    function($scope, $q, $location, $routeParams, $route, AssignmentResource, $uibModal,
             CriterionResource, required_rounds, Toaster, attachService, UploadValidator,
             EditorOptions, PairingAlgorithm, ComparisonExampleResource,
             AnswerResource, LearningRecordStatementHelper, resolvedData, moment,
             embeddableRichContent, $http, answerAttachService)
    {
        $scope.courseId = $routeParams.courseId;
        $scope.assignmentId = $routeParams.assignmentId || undefined;
        $scope.saveAssignmentAttempted = false;

        $scope.course = resolvedData.course;
        $scope.assignment = resolvedData.assignment || {};
        $scope.loggedInUserId = resolvedData.loggedInUser.id;
        $scope.canManageAssignment = resolvedData.canManageAssignment;
        $scope.availableCriteria = resolvedData.criteria.objects;
        $scope.groups = resolvedData.groups.objects;
        $scope.possible_group_comparisons = $scope.groups.length == 0 ?
            0 : Math.floor(($scope.groups.length - 1) / 2);

        // add default weight of 1 to all criterion
        _.forEach($scope.availableCriteria, function(criterion) {
            criterion.weight = 1;
        });

        $scope.method = $scope.assignment.id ? "edit" : "create";
        if ($route.current.method == "copy") {
           $scope.method = "copy";
        }

        $scope.UploadValidator = UploadValidator;
        $scope.editorOptions = EditorOptions.basic;
        $scope.PairingAlgorithm = PairingAlgorithm;
        $scope.uploader = attachService.getUploader();
        $scope.resetFileUploader = attachService.reset;
        $scope.recommended_comparisons = Math.floor(required_rounds / 2);

        $scope.canSupportPreview = attachService.canSupportPreview;
        $scope.assignment.rotated = false;

        // download the file and inject it to uploader
        $scope.reuploadAssignmentFile = function(file) {
            var content = embeddableRichContent.generateAttachmentContent(file);
            var url = content.url? content.url : '';
            if (url && $scope.canSupportPreview(file)) {
                $http.get(url, { responseType: "blob" }).success(function(image) {
                    // IE / Edge can't create new File objects. need alternate approach
                    // var imageFile = new File([image], file.alias, { type: file.mimetype });
                    // $scope.uploader.addToQueue(imageFile);
                    image.name = file.alias;
                    $scope.uploader.addToQueue(image);
                    // uploader is using a FileLikeObject for the _file. replace it with our blob.
                    $scope.uploader.queue[$scope.uploader.queue.length-1]._file = image;
                });
            } else {
                Toaster.error("Cannot adjust attachment", "Please remove the attachment and upload again.");
            }
        };

        $scope.rankLimitOptions = [
            {value: 10, label: 'Answers ranked 10th and higher'},
            {value: 20, label: 'Answers ranked 20th and higher'},
        ];

        // DATETIMES
        // declaration
        var today = new Date();
        $scope.format = 'dd-MMMM-yyyy';
        $scope.date = {
            'astart': {'date': new Date(), 'time': new Date().setHours(0, 0, 0, 0)},
            'aend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
            'cstart': {'date': new Date(), 'time': new Date().setHours(0, 0, 0, 0)},
            'cend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
            'sestart': {'date': new Date(), 'time': new Date().setHours(0, 0, 0, 0)},
            'seend': {'date': null, 'time': new Date().setHours(23, 59, 0, 0)}
        };

        $scope.comparison_example = {
            answer1: {},
            answer2: {}
        };

        // initialization method data
        if ($scope.method == "create") {
            $scope.assignment = {
                // add default criteria
                criteria: [
                    _.find($scope.availableCriteria, {public: true})
                ],
                // students replies disabled by default
                students_can_reply: false,
                // instructor comparisons disabled by default
                educators_can_compare: false,
                number_of_comparisons: $scope.recommended_comparisons,
                pairing_algorithm: PairingAlgorithm.adaptive_min_delta,
                rank_display_limit: null,
                answer_grade_weight: 1,
                comparison_grade_weight: 1,
                self_evaluation_grade_weight: 1,
                existingFile: false
            }

            // no default date set when creating a new assignment
            $scope.date.astart.date = null;
            $scope.date.aend.date = null;
            $scope.date.cstart.date = null;
            $scope.date.cend.date = null;
            $scope.date.sestart.date = null;
            $scope.date.seend.date = null;

        } else if ($scope.method == "edit") {
            if ($scope.assignment.file) {
                $scope.assignment.uploadedFile = true;
                $scope.assignment.existingFile = true;
            }

            $scope.date.astart.date = new Date($scope.assignment.answer_start);
            $scope.date.astart.time = new Date($scope.assignment.answer_start);
            $scope.date.aend.date = new Date($scope.assignment.answer_end);
            $scope.date.aend.time = new Date($scope.assignment.answer_end);

            if ($scope.assignment.compare_start && $scope.assignment.compare_end) {
                $scope.assignment.availableCheck = true;
                $scope.date.cstart.date = new Date($scope.assignment.compare_start);
                $scope.date.cstart.time = new Date($scope.assignment.compare_start);
                $scope.date.cend.date = new Date($scope.assignment.compare_end);
                $scope.date.cend.time = new Date($scope.assignment.compare_end)
            } else {
                $scope.date.cstart.date = new Date($scope.date.aend.date);
                $scope.date.cstart.time = new Date($scope.date.aend.time);
                $scope.date.cend.date = new Date();
                $scope.date.cend.date.setDate($scope.date.cstart.date.getDate()+7);
                $scope.date.cend.time = new Date($scope.date.aend.time);
            }

            if ($scope.assignment.self_eval_start) {
                $scope.assignment.selfEvalCheck = true;
                $scope.date.sestart.date = new Date($scope.assignment.self_eval_start);
                $scope.date.sestart.time = new Date($scope.assignment.self_eval_start);
                if ($scope.assignment.self_eval_end) {
                    $scope.date.seend.date = new Date($scope.assignment.self_eval_end);
                    $scope.date.seend.time = new Date($scope.assignment.self_eval_end);
                }
            } else {
                $scope.date.sestart.date = new Date($scope.date.cend.date);
                $scope.date.sestart.time = new Date($scope.date.cend.time);
            }

            $scope.assignment.addPractice = resolvedData.assignmentComparisonExamples.objects.length > 0;
            if ($scope.assignment.addPractice) {
                $scope.comparison_example = resolvedData.assignmentComparisonExamples.objects[0];
            }

        } else if ($scope.method == "copy") {
            var originalAssignment = $scope.assignment;
            $scope.originalAssignment = originalAssignment;

            $scope.assignment = {
                // copy criteria
                criteria: originalAssignment.criteria,
                // copy assignment data
                name: originalAssignment.name,
                description: originalAssignment.description,
                number_of_comparisons: originalAssignment.number_of_comparisons,
                students_can_reply: originalAssignment.students_can_reply,
                enable_self_evaluation: originalAssignment.enable_self_evaluation,
                enable_group_answers: originalAssignment.enable_group_answers,
                pairing_algorithm: originalAssignment.pairing_algorithm,
                scoring_algorithm: originalAssignment.scoring_algorithm,
                educators_can_compare: originalAssignment.educators_can_compare,
                answer_grade_weight: originalAssignment.answer_grade_weight,
                comparison_grade_weight: originalAssignment.comparison_grade_weight,
                self_evaluation_grade_weight: originalAssignment.self_evaluation_grade_weight,
                peer_feedback_prompt: originalAssignment.peer_feedback_prompt,
                rank_display_limit: originalAssignment.rank_display_limit,

                // copy assignment attachment
                file: originalAssignment.file,
                uploadedFile: originalAssignment.file ? true : undefined
            }

            // copy assignment dates
            $scope.date.astart.date = new Date(originalAssignment.answer_start);
            $scope.date.astart.time = new Date(originalAssignment.answer_start);
            $scope.date.aend.date = new Date(originalAssignment.answer_end);
            $scope.date.aend.time = new Date(originalAssignment.answer_end);

            if (originalAssignment.compare_start && originalAssignment.compare_end) {
                $scope.assignment.availableCheck = true;
                $scope.date.cstart.date = new Date(originalAssignment.compare_start);
                $scope.date.cstart.time = new Date(originalAssignment.compare_start);
                $scope.date.cend.date = new Date(originalAssignment.compare_end);
                $scope.date.cend.time = new Date(originalAssignment.compare_end)
            } else {
                $scope.date.cstart.date = new Date($scope.date.aend.date);
                $scope.date.cstart.time = new Date($scope.date.aend.time);
                $scope.date.cend.date = new Date();
                $scope.date.cend.date.setDate($scope.date.cstart.date.getDate()+7);
                $scope.date.cend.time = new Date($scope.date.aend.time);
            }

            if (originalAssignment.self_eval_start) {
                $scope.assignment.selfEvalCheck = true;
                $scope.date.sestart.date = new Date(originalAssignment.self_eval_start);
                $scope.date.sestart.time = new Date(originalAssignment.self_eval_start);
                if ( originalAssignment.self_eval_end) {
                    $scope.date.seend.date = new Date(originalAssignment.self_eval_end);
                    $scope.date.seend.time = new Date(originalAssignment.self_eval_end);
                }
            } else {
                $scope.date.sestart.date = new Date($scope.date.cend.date);
                $scope.date.sestart.time = new Date($scope.date.cend.time);
            }

            // copy assignment comparison examples
            $scope.assignment.addPractice = resolvedData.assignmentComparisonExamples.objects.length > 0;
            if ($scope.assignment.addPractice) {
                var comparison_example = resolvedData.assignmentComparisonExamples.objects[0];

                $scope.comparison_example = {
                    answer1: {
                        content: comparison_example.answer1.content,
                        file: comparison_example.answer1.file,
                        file_id: comparison_example.answer1.file ? comparison_example.answer1.file.id : undefined
                    },
                    answer2: {
                        content: comparison_example.answer2.content,
                        file: comparison_example.answer2.file,
                        file_id: comparison_example.answer2.file ? comparison_example.answer2.file.id : undefined
                    }
                };
            }
        }

        $scope.datePickerOpen = function($event, object) {
            $event.preventDefault();
            $event.stopPropagation();

            object.opened = true;
        };

        $scope.datePickerMinDate = function() {
            var dates = Array.prototype.slice.call(arguments).filter(function(val) {
                return typeof val !== 'undefined' && val !== null;
            });
            if (dates.length == 0) {
                return null;
            }
            return moment(dates.reduce(function (left, right) {
                return moment(left) > moment(right) ? left : right;
            }, dates[0])).toDate();
        };

        $scope.datePickerMaxDate = function() {
            var dates = Array.prototype.slice.call(arguments).filter(function(val) {
                return typeof val !== 'undefined' && val !== null;
            });
            if (dates.length == 0) {
                return null;
            }
            return moment(dates.reduce(function (left, right) {
                return moment(left) < moment(right) ? left : right;
            }, dates[0])).toDate();
        };

        $scope.getMinDate = function(startDate) {
            minDate = null;
            if ($scope.course.start_date) {
                minDate = $scope.course.start_date;
            }
            if (startDate) {
                minDate = startDate;
            }
            return minDate;
        };

        $scope.criteriaCanDraw = function() {
            var items = [];
            $scope.assignment.criteria.forEach(function(criterion) {
                items.push(criterion.weight);
            });
            var result = findEqualPartitions(items);
            return result !== false;
        };

        $scope.deleteFile = function(file) {
            $scope.assignment.file = null;
            $scope.assignment.uploadedFile = false;
        };

        var removeAssignmentCriteriaFromAvailable = function() {
            // we need to remove the existing assignment criteria from available list
            $scope.availableCriteria = _.filter($scope.availableCriteria, function(c) {
                return !_.find($scope.assignment.criteria, {id: c.id});
            });
        };
        removeAssignmentCriteriaFromAvailable();

        $scope.add = function(key) {
            // not proceed if empty option is being added
            if (key === undefined || key === null || key < 0 || key >= $scope.availableCriteria.length)
                return;
            $scope.assignment.criteria.push($scope.availableCriteria[key]);
            $scope.availableCriteria.splice(key, 1);
        };

        // remove criterion from assignment - eg. make it inactive
        $scope.remove = function(key) {
            var criterion = $scope.assignment.criteria[key];
            $scope.assignment.criteria.splice(key, 1);
            if (criterion.default) {
                $scope.availableCriteria.push(criterion);
            }
            $scope.droppedCriteria = true;
        };

        $scope.changeCriterion = function(criterion) {
            criterion = criterion || {};

            var modalScope = $scope.$new();
            modalScope.criterion = angular.copy(criterion);
            if (criterion && criterion.public) {
                modalScope.criterion.default = false;
                modalScope.criterion.compared = false;
            }
            var method = criterion.id ? 'edit' : 'create';
            var modalName = criterion.id ? 'Edit Criterion' : 'Create Criterion';

            $scope.modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "CriterionModalController",
                templateUrl: 'modules/criterion/criterion-modal-partial.html',
                scope: modalScope
            });
            $scope.modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal(modalName);
            });
            $scope.modalInstance.result.then(function (c) {
                if (method == 'edit') {
                    var weight = criterion.weight;
                    angular.copy(c, criterion);
                    criterion.weight = weight;
                } else {
                    c.weight = 1;
                    $scope.assignment.criteria.push(c);
                }
                LearningRecordStatementHelper.closed_modal(modalName);
            }, function() {
                LearningRecordStatementHelper.closed_modal(modalName);
            });
        };

        $scope.changeAnswer = function(answer, isAnswer1) {
            var modalScope = $scope.$new();
            modalScope.answerName = isAnswer1 ? 'Answer A' : 'Answer B';
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignment.id;
            modalScope.answer = angular.copy(answer);
            var modalName = modalScope.answer.id ?
                'Edit Comparison Example' : 'Create Comparison Example';

            $scope.modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "ComparisonExampleModalController",
                templateUrl: 'modules/answer/answer-modal-partial.html',
                scope: modalScope
            });
            $scope.modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal(modalName);
            });
            $scope.modalInstance.result.then(function (answer) {
                if (isAnswer1) {
                    $scope.comparison_example.answer1 = answer;
                    if (answer.id) {
                        $scope.comparison_example.answer1_id = answer.id
                    }
                } else {
                    $scope.comparison_example.answer2 = answer;
                    if (answer.id) {
                        $scope.comparison_example.answer2_id = answer.id
                    }
                }
                LearningRecordStatementHelper.closed_modal(modalName);
            }, function() {
                LearningRecordStatementHelper.closed_modal(modalName);
            });
        };

        $scope.getCriterionWeightAsPercent = function(weight) {
            var total = 0;
            $scope.assignment.criteria.forEach(function(criterion) {
                total += criterion.weight;
            });
            var calculatedPercentage = (weight * 100) / total;
            if (calculatedPercentage) {
                var passedPercentage = calculatedPercentage;
            } else {
                var passedPercentage = 0;
            }
            return passedPercentage;
        }

        $scope.getGradeWeightAsPercent = function(weight) {
            var total = $scope.assignment.answer_grade_weight + $scope.assignment.comparison_grade_weight;
            if ($scope.assignment.enable_self_evaluation) {
                total += $scope.assignment.self_evaluation_grade_weight;
            }
            var calculatedPercentage = (weight * 100) / total;
            if (calculatedPercentage) {
                var passedPercentage = calculatedPercentage;
            } else {
                var passedPercentage = 0;
            }
            return passedPercentage;
        };
        
        
        // check dates against one another for inline error display
        $scope.dateMismatch = function(firstDate, secondDate, canBeEqual, firstNewOrCombined, secondNewOrCombined) {
            
            if (firstDate && firstDate !== undefined && secondDate && secondDate !== undefined) {
                
                // need to match the formats between database and form inputs
                switch (firstNewOrCombined) {
                    case 'new':
                        firstDate = firstDate ? new Date(firstDate) : null; //course end date is optional
                        break;
                    case 'combined':
                        firstDate = combineDateTime(firstDate);
                        break;
                    default:
                        break;
                }
                switch (secondNewOrCombined) {
                    case 'new':
                        secondDate = secondDate ? new Date(secondDate) : null; //course end date is optional
                        break;
                    case 'combined':
                        secondDate = combineDateTime(secondDate);
                        break;
                    default:
                        break;
                }
                
                // is the date the same?
                if (firstDate.toDateString() === secondDate.toDateString()) {

                    // can the start and end time be the same?
                    if (canBeEqual) {
                        // does the end time follow or equal the start time?
                        if (firstDate.toTimeString().split(' ')[0] <= secondDate.toTimeString().split(' ')[0]) {
                            return false; 
                        } else {
                            return true; // show errors
                        }
                    } else {
                        // does the end time follow the start time?
                        if (firstDate.toTimeString().split(' ')[0] < secondDate.toTimeString().split(' ')[0]) {
                            return false;
                        } else {
                            return true; // show errors
                        }
                    }
                         
                } else {
                         
                    // does the end date follow the start date?
                    if (Date.parse(firstDate) < Date.parse(secondDate)) {
                        return false;
                    } else {
                        return true; // show errors
                    }
     
                }//closes if equal
             
            }//closes if date/time
            
        };
        
        // decide on showing other inline errors
        $scope.showAssignmentErrors = function($event, formValid) {
            
            // check for number of criteria entered
            existingCriteria = $scope.assignment.criteria.length;
            
            // assume no date errors, no practice answers missing
            $scope.dateError = false;
            $scope.missingPracticeAnswers = false;
            
            // need to match the formats between database and form inputs
            course_sdate = new Date($scope.course.start_date);
            course_edate = $scope.course.end_date ? new Date($scope.course.end_date): null; //course end is optional
            answer_sdate = $scope.date.astart.date ? combineDateTime($scope.date.astart) : null;
            answer_edate = $scope.date.aend.date ? combineDateTime($scope.date.aend) : null;
            compare_sdate = $scope.date.cstart.date ? combineDateTime($scope.date.cstart) : null;
            compare_edate = $scope.date.cend.date ? combineDateTime($scope.date.cend) : null;
            selfeval_sdate = $scope.date.sestart.date ? combineDateTime($scope.date.sestart) : null;
            selfeval_edate = $scope.date.seend.date ? combineDateTime($scope.date.seend) : null;
            
            // even if entered, don't apply comparison dates if unchecked
            if ($scope.assignment.availableCheck === false || $scope.assignment.availableCheck === undefined) {
                compare_sdate = null;
                compare_edate = null;
            }
            
            // even if entered, don't apply self-eval dates if unchecked
            if ($scope.assignment.selfEvalCheck === false || $scope.assignment.selfEvalCheck === undefined) {
                selfeval_sdate = null;
                selfeval_edate = null;
            }
            
            // if assignment has start/end date but no matching time or
            // assignment ends before it starts or
            // assignment starts before the course starts or
            // assignment ends after the course ends or
            // comparison has start/end date but no matching time or
            // comparison ends before it starts or
            // comparison starts before answer starts or
            // comparison ends after the course ends or
            // self-eval has start/end date but no matching time or
            // self-eval ends before it starts or
            // self-eval starts before answer starts or
            // self-eval starts before compare starts or
            // self-eval ends after the course ends
            if ( (answer_sdate && !$scope.date.astart.time) || (answer_edate && !$scope.date.aend.time) ||
                 (answer_sdate && answer_edate &&
                   ( Date.parse(answer_sdate) > Date.parse(answer_edate) ||
                     (answer_sdate.toDateString() === answer_edate.toDateString() && answer_sdate.toTimeString().split(' ')[0] >= answer_edate.toTimeString().split(' ')[0]) ) )  ||
                 (answer_sdate && course_sdate &&
                   ( Date.parse(answer_sdate) < Date.parse(course_sdate) ||
                     (answer_sdate.toDateString() === course_sdate.toDateString() && answer_sdate.toTimeString().split(' ')[0] < course_sdate.toTimeString().split(' ')[0]) ) ) ||
                 (answer_edate && course_edate &&
                   ( Date.parse(answer_edate) > Date.parse(course_edate) ||
                     (answer_edate.toDateString() === course_edate.toDateString() && $scope.date.aend.time.toTimeString().split(' ')[0] > course_edate.toTimeString().split(' ')[0]) ) ) ||
                 (compare_sdate && !$scope.date.cstart.time) || (compare_edate && !$scope.date.cend.time) ||
                 (compare_sdate && compare_edate &&
                   ( Date.parse(compare_sdate) > Date.parse(compare_edate) ||
                     (compare_sdate.toDateString() === compare_edate.toDateString() && compare_sdate.toTimeString().split(' ')[0] >= compare_edate.toTimeString().split(' ')[0]) ) ) ||
                 (answer_sdate && compare_sdate &&
                   ( Date.parse(answer_sdate) > Date.parse(compare_sdate) ||
                     (answer_sdate.toDateString() === compare_sdate.toDateString() && answer_sdate.toTimeString().split(' ')[0] > compare_sdate.toTimeString().split(' ')[0]) ) ) ||
                 (course_edate && compare_edate &&
                   ( Date.parse(compare_edate) > Date.parse(course_edate) ||
                     (compare_edate.toDateString() === course_edate.toDateString() && compare_edate.toTimeString().split(' ')[0] > course_edate.toTimeString().split(' ')[0]) ) ) ||
                 (selfeval_sdate && !$scope.date.sestart.time) || (selfeval_edate && !$scope.date.seend.time) ||
                 (selfeval_sdate && selfeval_edate &&
                   ( Date.parse(selfeval_sdate) > Date.parse(selfeval_edate) ||
                     (selfeval_sdate.toDateString() === selfeval_edate.toDateString() && selfeval_sdate.toTimeString().split(' ')[0] >= selfeval_edate.toTimeString().split(' ')[0]) ) ) ||
                 (answer_sdate && selfeval_sdate &&
                   ( Date.parse(answer_sdate) > Date.parse(selfeval_sdate) ||
                     (answer_sdate.toDateString() === selfeval_sdate.toDateString() && answer_sdate.toTimeString().split(' ')[0] > selfeval_sdate.toTimeString().split(' ')[0]) ) ) ||
                 (compare_sdate && selfeval_sdate &&
                   ( Date.parse(compare_sdate) > Date.parse(selfeval_sdate) ||
                     (compare_sdate.toDateString() === selfeval_sdate.toDateString() && compare_sdate.toTimeString().split(' ')[0] > selfeval_sdate.toTimeString().split(' ')[0]) ) ) ||
                 (course_edate && selfeval_edate &&
                   ( Date.parse(selfeval_edate) > Date.parse(course_edate) ||
                     (selfeval_edate.toDateString() === course_edate.toDateString() && selfeval_edate.toTimeString().split(' ')[0] > course_edate.toTimeString().split(' ')[0]) ) )
               ) {
                    $scope.dateError = true;
            }//closes if dateError
            
            // check for practice answers, if this option is selected
            if ($scope.assignment.addPractice) {
                
                var answer1 = $scope.comparison_example.answer1;
                var answer2 = $scope.comparison_example.answer2;

                if ((!answer1.content || answer1.content.trim() === "") && !answer1.file && (!answer1.file_alias || answer1.file_alias === "")) {
                    $scope.missingPracticeAnswers = true;
                    $scope.whichMissingAnswer = "Answer A";
                }
                
                if ((!answer2.content || answer2.content.trim() === "") && !answer2.file  && (!answer2.file_alias || answer2.file_alias === "")) {
                    $scope.missingPracticeAnswers = true;
                    $scope.whichMissingAnswer = "Answer B";
                }
                
                if ( ((!answer1.content || answer1.content.trim() === "") && !answer1.file && (!answer1.file_alias || answer1.file_alias === "")) && ((!answer2.content || answer2.content.trim() === "") && !answer2.file  && (!answer2.file_alias || answer2.file_alias === "")) ) {
                    $scope.missingPracticeAnswers = true;
                    $scope.whichMissingAnswer = "both answers";
                }

            }//closes if addPractice

            // show errors if invalid form (includes checking for practice answers) or no criteria set or date error found
            if (!formValid || existingCriteria === 0 || $scope.dateError === true) {

                // don't submit
                $event.preventDefault();
                
                // set which action to use in messages
                var actionTaken = "saved";
                if ($scope.method == "copy") {
                    actionTaken = "duplicated";
                }
                
                // set helper text and Toast
                $scope.helperMsg = "Sorry, this assignment couldn't be "+actionTaken+" yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this assignment couldn't be "+actionTaken+" yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";
                
                // display messages
                $scope.saveAssignmentAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);
            
            }
            
        };//closes showErrors

        $scope.assignmentSubmit = function () {
            $scope.submitted = true;

            // second-tier error catching
            if ($scope.date.astart.date == null || $scope.date.astart.time == null ||
                $scope.date.aend.date == null || $scope.date.aend.time == null) {
                Toaster.warning('Assignment Not Saved', 'Please specify the start date and end date of answering period.');
                $scope.submitted = false;
                return;
            }

            $scope.assignment.answer_start = combineDateTime($scope.date.astart);
            $scope.assignment.answer_end = combineDateTime($scope.date.aend);
            $scope.assignment.compare_start = $scope.assignment.availableCheck ? combineDateTime($scope.date.cstart) : null;
            $scope.assignment.compare_end = $scope.assignment.availableCheck ? combineDateTime($scope.date.cend) : null;
            $scope.assignment.self_eval_start = $scope.assignment.enable_self_evaluation && $scope.assignment.selfEvalCheck ? combineDateTime($scope.date.sestart) : null;
            $scope.assignment.self_eval_end = $scope.assignment.enable_self_evaluation && $scope.assignment.selfEvalCheck ? combineDateTime($scope.date.seend) : null;
            
            if (!$scope.assignment.enable_self_evaluation) {
                $scope.assignment.selfEvalCheck = false;
                $scope.assignment.self_eval_instructions = null;
            }

            // second-tier error catching
            // answer end datetime has to be after answer start datetime
            if ($scope.assignment.answer_start >= $scope.assignment.answer_end) {
                Toaster.warning('Assignment Not Saved', 'Please set answer end time after answer start time and save again.');
                $scope.submitted = false;
                return;
            } else if ($scope.assignment.availableCheck && $scope.assignment.answer_start > $scope.assignment.compare_start) {
                Toaster.warning("Assignment Not Saved", 'Please double-check the answer and comparison start and end times for mismatches and save again.');
                $scope.submitted = false;
                return;
            } else if ($scope.assignment.availableCheck && $scope.assignment.compare_start >= $scope.assignment.compare_end) {
                Toaster.warning("Assignment Not Saved", 'Please set comparison end time after comparison start time and save again.');
                $scope.submitted = false;
                return;
            } else if ($scope.assignment.availableCheck && $scope.assignment.selfEvalCheck && $scope.assignment.self_eval_start <= $scope.assignment.compare_start) {
                Toaster.warning("Assignment Not Saved", 'Please set self-evaluation start time after compare start time and save again.');
                $scope.submitted = false;
                return;
            } else if (!$scope.assignment.availableCheck && $scope.assignment.selfEvalCheck && $scope.assignment.self_eval_start <= $scope.assignment.answer_end) {
                Toaster.warning("Assignment Not Saved", 'Please set self-evaluation start time after answer end time and save again.');
                $scope.submitted = false;
                return;
            } else if ($scope.assignment.selfEvalCheck && $scope.assignment.self_eval_start >= $scope.assignment.self_eval_end) {
                Toaster.warning("Assignment Not Saved", 'Please set self-evaluation end time after self-evaluation start time and save again.');
                $scope.submitted = false;
                return;
            }
            
            // second-tier error catching
            if ($scope.assignment.addPractice) {
                var answer1 = $scope.comparison_example.answer1;
                var answer2 = $scope.comparison_example.answer2;

               if ( ((!answer1.content || answer1.content.trim() == "") && !answer1.file && (!answer1.file_alias || answer1.file_alias == "")) && ((!answer2.content || answer2.content.trim() == "") && !answer2.file  && (!answer2.file_alias || answer2.file_alias == "")) ) {
                    Toaster.warning("Assignment Not Saved", 'Please add content for answers in your practice pair and save again.');
                    $scope.submitted = false;
                    return;
                }
                if ((!answer1.content || answer1.content.trim() == "") && !answer1.file && (!answer1.file_alias || answer1.file_alias == "")) {
                    Toaster.warning("Assignment Not Saved", 'Please add content for the first answer in your practice pair and save again.');
                    $scope.submitted = false;
                    return;
                }
                if ((!answer2.content || answer2.content.trim() == "") && !answer2.file  && (!answer2.file_alias || answer2.file_alias == "")) {
                    Toaster.warning("Assignment Not Saved", 'Please add content for the second answer in your practice pair and save again.');
                    $scope.submitted = false;
                    return;
                }
            }

            var promises = [];
            // save duplicate version of public criteria for new assignments
            if (!$scope.assignment.id) {
                _.forEach($scope.assignment.criteria, function(criterion) {
                    if (criterion.public) {
                        var weight = criterion.weight;
                        var criterionDuplicate = angular.copy(criterion);
                        criterionDuplicate.id = null;
                        criterionDuplicate.public = false;
                        criterionDuplicate.default = false;

                        promises.push($q(function(resolve, reject) {
                            CriterionResource.save({}, criterionDuplicate).$promise.then(
                                function (ret) {
                                    angular.copy(ret, criterion);
                                    criterion.weight = weight;
                                    resolve();
                                },
                                function (ret) {
                                    reject();
                                }
                            );
                        }));
                    }
                });
            }

            // see if need to re-upload the attachment
            promises.push.apply(promises, answerAttachService.reUploadPromises($scope.uploader));

            $q.all(promises).then(function() {
                // if option is not checked; make sure no compare dates are saved.
                if (!$scope.assignment.availableCheck) {
                    $scope.assignment.compare_start = null;
                    $scope.assignment.compare_end = null;
                }
                var file = attachService.getFile();
                if (file) {
                    $scope.assignment.file = file;
                    $scope.assignment.file_id = file.id
                } else if ($scope.assignment.file) {
                    $scope.assignment.file_id = $scope.assignment.file.id;
                } else {
                    $scope.assignment.file_id = null;
                }
                AssignmentResource.save({'courseId': $scope.courseId}, $scope.assignment)
                    .$promise.then(function (ret) {
                        var assignmentId = ret.id;
                        $scope.assignment.id = ret.id;
                        var promises = [];

                        // only save comparison example changes if assignment hasn't been compared yet
                        if (!$scope.assignment.compared) {
                            if ($scope.assignment.addPractice) {
                                promises.push(saveComparisonsExample(assignmentId, $scope.comparison_example));
                            } else {
                                promises.push(deleteComparisonsExample(assignmentId, $scope.comparison_example));
                            }
                        }

                        $q.all(promises).then(function() {
                            $scope.submitted = false;
                            if ($scope.method == "copy") {
                                Toaster.success("Assignment Duplicated");
                            } else {
                                Toaster.success("Assignment Saved");
                            }
                            $location.path('/course/' + $scope.courseId);
                        }, function() {
                            $scope.submitted = false;
                        });
                    },
                    function (ret) {
                        $scope.submitted = false;
                    }
                );
            });
        };

        var deleteComparisonsExample = function(assignmentId, comparison_example) {
            return $q(function(resolve, reject) {
                if (comparison_example.id) {
                    ComparisonExampleResource.delete({'courseId': $scope.courseId, 'assignmentId': assignmentId}, comparison_example)
                    .$promise.then(
                        function (ret) {
                            comparison_example.id = null;
                            resolve();
                        },
                        function (ret) {
                            reject();
                        }
                    );
                } else {
                    resolve();
                }
            });
        };

        var saveComparisonsExample = function(assignmentId, comparison_example) {
            return $q(function(resolve, reject) {
                var promises = [];

                // save answers
                promises.push(saveNewComparisonsExampleAnswer(assignmentId, comparison_example, comparison_example.answer1, true));
                promises.push(saveNewComparisonsExampleAnswer(assignmentId, comparison_example, comparison_example.answer2, false));

                // after answers are saved, save comparison example
                $q.all(promises).then(function() {
                    ComparisonExampleResource.save({'courseId': $scope.courseId, 'assignmentId': assignmentId}, comparison_example)
                    .$promise.then(
                        function (ret) {
                            comparison_example.id = ret.id;
                            resolve();
                        },
                        function (ret) {
                            reject();
                        }
                    );
                }, function() {
                    // cannot save comparison example due to errors with answers
                    reject();
                });
            });
        };

        var saveNewComparisonsExampleAnswer = function(assignmentId, comparison_example, answer, isAnswer1) {
            return $q(function(resolve, reject) {
                // only save the answer if new (saved automatically in modal if already exists)
                if (answer.id == null) {
                    AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': assignmentId}, answer)
                    .$promise.then(
                        function (ret) {
                            if (isAnswer1) {
                                comparison_example.answer1_id = ret.id;
                                comparison_example.answer1 = ret;
                            } else {
                                comparison_example.answer2_id = ret.id;
                                comparison_example.answer2 = ret;
                            }
                            resolve();
                        },
                        function (ret) {
                            reject();
                        }
                    );
                } else {
                    resolve();
                }
            });
        };
    }
]);

// End anonymous function
})();
