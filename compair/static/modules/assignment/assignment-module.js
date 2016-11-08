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
        'ubc.ctlt.compair.comment',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.common.mathjax',
        'ubc.ctlt.compair.common.highlightjs',
        'ubc.ctlt.compair.common.pdf',
        'ubc.ctlt.compair.criterion',
        'ubc.ctlt.compair.group',
        'ubc.ctlt.compair.comparison',
        'ubc.ctlt.compair.toaster',
        'ubc.ctlt.compair.session'
    ]
);

module.constant('PairingAlgorithm', {
    adaptive: "adaptive",
    random: "random"
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
                msg = "Are you sure you want to remove this"+msg+"?";
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
                    if (scope.thisHeight > 200) {
                        scope.showReadMore = true;
                    }
                }, 7000);
            }
        };
    }
]);

module.directive(
    'toolTip',
    function() {
        return {
            restrict: 'A',
            link: function(scope, element) {
                $(element).hover(function(){
                    // on mouseenter
                    $(element).tooltip('show');
                }, function(){
                    // on mouseleave
                    $(element).tooltip('hide');
                });
            }
        };
    }
);

module.directive('comparisonPreview', function() {
    return {
        /* this template is our simple text with button to launch the preview */
        templateUrl: 'modules/assignment/preview-inline-template.html',
        controller: ["$scope", "$modal", function ($scope, $modal) {
            /* need to pass to comparison template all expected properties to complete the preview */
            $scope.previewPopup = function() {
                /* set current round #, answer #s, and total round # for preview */
                $scope.current = 1;
                $scope.firstAnsNum = 1;
                $scope.secondAnsNum = 2;
                $scope.total = 0;
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
                    content: "<p>The first student answer in the pair will appear here.</p>",
                    file: null
                }
                $scope.answer2 = {
                    content: "<p>The second student answer in the pair will appear here.</p>",
                    file: null
                }
                $scope.comparisons = [];
                angular.forEach($scope.assignment.criteria, function(criterion) {
                    $scope.comparisons.push({
                        'criterion_id': criterion.id,
                        'criterion': criterion,
                        'content': '',
                        'winner_id': null
                    });
                });
                /* student view preview is comparison template */
                $scope.thePreview = $modal.open({
                    templateUrl: 'modules/comparison/comparison-core.html',
                    scope: $scope
                });
            }
        }]
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
                'getCurrentUserStatus': {url: '/api/courses/:id/assignments/:assignmentId/status'}
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

module.factory(
    "AttachmentResource",
    [ "$resource",
    function ($resource)
    {
        var ret = $resource(
            '/api/attachment/:fileId',
            {fileId: '@file_id'}
        );
        ret.MODEL = "File";
        return ret;
    }
]);

/***** Services *****/
module.service('attachService',
        ["FileUploader", "$location", "Toaster",
        function(FileUploader, $location, Toaster) {
    var file = null;

    var getUploader = function() {
        var uploader = new FileUploader({
            url: '/api/attachment',
            queueLimit: 1,
            autoUpload: true,
            headers: {
                Accept: 'application/json'
            }
        });

        file = null;

        uploader.onCompleteItem = onComplete();
        uploader.onErrorItem = onError();

        uploader.filters.push({
            name: 'pdfFilter',
            fn: function(item) {
                var type = '|' + item.type.slice(item.type.lastIndexOf('/') + 1) + '|';
                var valid = '|pdf|'.indexOf(type) !== -1;
                if (!valid) {
                    Toaster.error("File Type Error", "Only PDF files are accepted.")
                }
                return valid;
            }
        });

        uploader.filters.push({
            name: 'sizeFilter',
            fn: function(item) {
                var valid = item.size <= 26214400; // 1024 * 1024 * 25 -> max 25MB
                if (!valid) {
                    var size = item.size / 1048576; // convert to MB
                    Toaster.error("File Size Error", "The file size is "+size.toFixed(2)+"MB. The maximum allowed is 25MB.")
                }
                return valid;
            }
        });

        return uploader;
    };

    var onComplete = function() {
        return function(fileItem, response) {
            if (response) {
                file = response['file'];
            }
        };
    };

    var onError = function() {
        return function(fileItem, response, status) {
            if (response == '413') {
                Toaster.error("File Size Error", "The file is larger than 25MB. Please upload a smaller file.");
            } else {
                Toaster.reqerror("Attachment Fail", status);
            }
        };
    };

    var reset = function() {
        return function() {
            file = null;
        }
    };

    var getFile = function() {
        return file;
    };

    return {
        getUploader: getUploader,
        getFile: getFile,
        reset: reset
    };
}]);

/***** Filters *****/
module.filter("excludeInstr", function() {
    return function(items, instructors) {
        var filtered = [];
        angular.forEach(items, function(item) {
            // if user id is NOT in the instructors array, keep it
            if (!instructors[item.user_id]) {
                filtered.push(item);
            }
        });
        return filtered;
    };
});

module.filter("notScoredEnd", function () {
    return function (array, key) {
        if (!angular.isArray(array)) return;
        var scored = [];
        var not_scored = [];
        angular.forEach(array, function(item) {
            if (key in item.scores) {
                scored.push(item);
            } else {
                not_scored.push(item);
            }
        });
        return scored.concat(not_scored);
    }
});

/***** Controllers *****/
module.controller("AssignmentViewController",
    ["$scope", "$routeParams", "$location", "AnswerResource", "Authorize", "AssignmentResource", "AssignmentCommentResource",
             "ComparisonResource", "CourseResource", "required_rounds", "Session", "Toaster", "AnswerCommentResource",
             "GroupResource", "AnswerCommentType", "PairingAlgorithm", "$modal",
    function($scope, $routeParams, $location, AnswerResource, Authorize, AssignmentResource, AssignmentCommentResource,
             ComparisonResource, CourseResource, required_rounds, Session, Toaster, AnswerCommentResource,
             GroupResource, AnswerCommentType, PairingAlgorithm, $modal)
    {
        $scope.courseId = $routeParams['courseId'];
        $scope.AnswerCommentType = AnswerCommentType;
        $scope.PairingAlgorithm = PairingAlgorithm;
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        var params = {
            courseId: $scope.courseId,
            assignmentId: assignmentId
        };
        $scope.allStudents = {};
        var userIds = {};
        $scope.totalNumAnswers = 0;
        $scope.answerFilters = {
            page: 1,
            perPage: 20,
            group_name: null,
            author: null,
            top: null,
            orderBy: null
        };
        $scope.self_evaluation_needed = false;
        $scope.rankLimit = null;

        Session.getUser().then(function(user) {
            $scope.loggedInUserId = user.id;

            AssignmentResource.get(params,
                function (ret) {
                    ret.answer_start = new Date(ret.answer_start);
                    ret.answer_end = new Date(ret.answer_end);
                    ret.compare_start = new Date(ret.compare_start);
                    ret.compare_end = new Date(ret.compare_end);
                    $scope.assignment = ret;

                    $scope.criteria = ret.criteria;
                    $scope.reverse = true;

                    if (ret.rank_display_limit) {
                        $scope.rankLimit = ret.rank_display_limit;
                    }

                    $scope.readDate = Date.parse(ret.created);

                    if ($scope.assignment.compare_end) {
                        $scope.answerAvail = $scope.assignment.compare_end;
                    } else {
                        $scope.answerAvail = $scope.assignment.answer_end;
                    }

                    AssignmentResource.getCurrentUserStatus({'id': $scope.courseId, 'assignmentId': assignmentId},
                        function (ret) {
                            $scope.assignment.status = ret.status;
                            $scope.comparisons_left = ret.status.comparisons.left;
                            $scope.self_evaluation_needed = $scope.assignment.enable_self_evaluation ?
                                !ret.status.comparisons.self_evaluation_completed : false;
                            $scope.steps_left = $scope.comparisons_left + ($scope.self_evaluation_needed ? 1 : 0);

                            if ($scope.assignment.compare_end) {
                                // if comparison period is set answers can be seen after it ends
                                $scope.see_answers = $scope.assignment.after_comparing;
                            } else {
                                // if an comparison period is NOT set - answers can be seen after req met
                                $scope.see_answers = $scope.assignment.after_comparing && $scope.comparisons_left == 0;
                            }
                            var diff = $scope.assignment.answer_count - ret.status.answers.count;
                            var possible_comparisons_left = ((diff * (diff - 1)) / 2);
                            $scope.warning = ret.status.comparisons.left > possible_comparisons_left;
                        },
                        function (ret) {
                            Toaster.reqerror("Assignment Status Not Found", ret);
                        }
                    );
                    // update the answer list
                    $scope.updateAnswerList();
                    // register watcher here so that we start watching when all filter values are set
                    $scope.$watchCollection('answerFilters', filterWatcher);
                },
                function (ret)
                {
                    Toaster.reqerror("Assignment Not Found For ID " + assignmentId, ret);
                }
            );
        });

        Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId).then(function(result) {
            $scope.canManageAssignment = result;
            if ($scope.canManageAssignment) {
                GroupResource.get({'courseId': $scope.courseId}, function (ret) {
                    $scope.groups = ret.objects;
                });
            }
        });
        $scope.students = {};
        CourseResource.getStudents({'id': $scope.courseId}, function (ret) {
            $scope.allStudents = ret.objects;
            $scope.students = ret.objects;
            userIds = $scope.getUserIds(ret.objects);
        });
        $scope.assignment = {};

        $scope.comments = AssignmentCommentResource.get(params);

        $scope.instructors = {};
        CourseResource.getInstructorsLabels({'id': $scope.courseId},
            function (ret) {
                $scope.instructors = ret.instructors;
            },
            function (ret) {
                Toaster.reqerror("Instructors Not Found", ret);
            }
        );

        $scope.getUserIds = function(students) {
            var users = {};
            angular.forEach(students, function(s){
                users[s.id] = 1;
            });
            return users;
        };

        $scope.adminFilter = function() {
            return function (answer) {
                // assume if any filter is applied - instructor/TAs answer will not meet requirement
                return !$scope.answerFilters.author && !$scope.answerFilters.group
            }
        };

        //TODO: this filter should be implemented in backend
        $scope.commentFilter = function(answer) {
            return function (comment) {
                // can see if canManageAssignment OR their own answer OR public
                return $scope.canManageAssignment ||
                    answer.user_id == $scope.loggedInUserId ||
                    comment.comment_type == AnswerCommentType.public;
            }
        };

        var tab = 'answers';
        // tabs: answers, help, participation, comparisons
        $scope.setTab = function(name) {
            tab = name;
            if (name == "comparisons") {
                $scope.comparisons = AnswerResource.comparisons(params);
				var answer_params = angular.extend({}, params, {author: $scope.loggedInUserId});
				$scope.user_answers = AnswerResource.get(answer_params);
            }
        };
        $scope.showTab = function(name) {
            return tab == name;
        };

        // revealAnswer function shows full answer content for abbreviated answers (determined by getHeight directive)
        $scope.revealAnswer = function(answerId) {
            var thisClass = '.content.'+answerId;      // class for the answer to show is "content" plus the answer's ID
            $(thisClass).css({'max-height' : 'none'}); // now remove height restriction for this answer
            this.showReadMore = false;                 // and hide the read more button for this answer
        };

        // assignment delete function
        $scope.deleteAssignment = function(course_id, assignment_id) {
            AssignmentResource.delete({'courseId': course_id, 'assignmentId': assignment_id},
                function (ret) {
                    Toaster.success("Assignment Delete Successful", "Successfully deleted assignment " + ret.id);
                    $location.path('/course/'+course_id);
                },
                function (ret) {
                    Toaster.reqerror("Assignment Delete Failed", ret);
                    $location.path('/course/'+course_id);
                }
            );
        };

        $scope.deleteAnswer = function(answer, course_id, assignment_id, answer_id) {
            AnswerResource.delete({'courseId':course_id, 'assignmentId':assignment_id, 'answerId':answer_id},
                function (ret) {
                    Toaster.success("Answer Delete Successful", "Successfully deleted answer "+ ret.id);
                    var authorId = answer['user_id'];
                    $scope.answers.objects.splice($scope.answers.objects.indexOf(answer), 1);
                    $scope.assignment.answer_count -= 1;
                    if ($scope.loggedInUserId == authorId) {
                        $scope.assignment.status.answers.count--;
                        $scope.assignment.status.answers.answered = $scope.assignment.status.answers.count > 0;
                    }
                },
                function (ret) {
                    Toaster.reqerror("Answer Delete Failed", ret);
                }
            );
        };

        // unflag a flagged answer
        $scope.unflagAnswer = function(answer, course_id, assignment_id, answer_id) {
            var params = {'flagged': false};
            AnswerResource.flagged({'courseId':course_id, 'assignmentId':assignment_id, 'answerId':answer_id}, params).$promise.then(
                function () {
                    answer['flagged'] = false;
                    Toaster.success("Answer Successfully Unflagged");
                },
                function (ret) {
                    Toaster.reqerror("Unable To Change Flag", ret);
                }
            );
        };

        // toggle top_answer state for answer
        $scope.setTopAnswer = function(answer, topAnswer) {
            var params = {'top_answer': topAnswer};
            AnswerResource.topAnswer({'courseId':answer.course_id, 'assignmentId':answer.assignment_id, 'answerId':answer.id}, params).$promise.then(
                function () {
                    answer.top_answer = topAnswer;
                    if (topAnswer) {
                        Toaster.success("Answer Successfully Added to Top Answers");
                    } else {
                        Toaster.success("Answer Successfully Removed from Top Answers");
                    }
                },
                function (ret) {
                    Toaster.reqerror("Unable To Change Top Answer", ret);
                }
            );
        };

        $scope.editAnswer = function(answer) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignmentId;
            modalScope.answer = angular.copy(answer);

            $scope.modalInstance = $modal.open({
                animation: true,
                controller: "AnswerModalController",
                templateUrl: 'modules/answer/answer-modal-partial.html',
                scope: modalScope
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
            });
        };

        $scope.createAnswerComment = function(answer) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignment.id;
            modalScope.answerId = answer.id;

            $scope.modalInstance = $modal.open({
                animation: true,
                controller: "AnswerCommentModalController",
                templateUrl: 'modules/comment/comment-answer-modal-partial.html',
                scope: modalScope
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
            });
        };

        $scope.editAnswerComment = function(answer, comment) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignment.id;
            modalScope.answerId = answer.id;
            modalScope.comment = angular.copy(comment);

            $scope.modalInstance = $modal.open({
                animation: true,
                controller: "AnswerCommentModalController",
                templateUrl: 'modules/comment/comment-answer-modal-partial.html',
                scope: modalScope
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
            });
        };

        $scope.createAssignmentComment = function() {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignment.id;

            $scope.modalInstance = $modal.open({
                animation: true,
                controller: "AssignmentCommentModalController",
                templateUrl: 'modules/comment/comment-assignment-modal-partial.html',
                scope: modalScope
            });

            $scope.modalInstance.result.then(function (newComment) {
                $scope.comments.objects.push(newComment)
            });
        };

        $scope.editAssignmentComment = function(comment) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.assignmentId = $scope.assignment.id;
            modalScope.comment = angular.copy(comment);

            $scope.modalInstance = $modal.open({
                animation: true,
                controller: "AssignmentCommentModalController",
                templateUrl: 'modules/comment/comment-assignment-modal-partial.html',
                scope: modalScope
            });

            $scope.modalInstance.result.then(function (updatedComment) {
                // update comment
                _.each($scope.comments.objects, function(comment, index) {
                    if (comment.id == updatedComment.id) {
                        $scope.comments.objects[index] = updatedComment;
                    }
                });
            });
        };

        $scope.loadComments = function(answer) {
            answer.comments = AnswerCommentResource.query(
                {courseId: $scope.courseId, assignmentId: assignmentId, answer_ids: answer.id})
        };

        $scope.deleteComment = function(key, course_id, assignment_id, comment_id) {
            AssignmentCommentResource.delete({'courseId': course_id, 'assignmentId': assignment_id, 'commentId': comment_id},
                function (ret) {
                    Toaster.success("Comment Delete Successful", "Successfully deleted comment " + ret.id);
                    $scope.comments.objects.splice(key, 1);
                    $scope.assignment.comment_count--;
                },
                function (ret) {
                    Toaster.reqerror("Comment Delete Failed", ret);
                }
            );
        };

        $scope.deleteReply = function(answer, commentKey, course_id, assignment_id, answer_id, comment_id) {
            AnswerCommentResource.delete({'courseId': course_id, 'assignmentId': assignment_id, 'answerId': answer_id, 'commentId': comment_id},
                function (ret) {
                    Toaster.success("Reply Delete Successful", "Successfully deleted reply.");
                    var comment = answer['comments'].splice(commentKey, 1)[0];
                    if (comment.comment_type == AnswerCommentType.public) {
                        answer.public_comment_count--;
                    } else {
                        answer.private_comment_count--;
                    }
                    answer.comment_count--;
                },
                function (ret) {
                    Toaster.reqerror("Reply Delete Failed", ret);
                }
            );
        };

        $scope.updateAnswerList = function() {
            var params = angular.merge({'courseId': $scope.courseId, 'assignmentId': assignmentId}, $scope.answerFilters);
            if (params.author == "top-picks") {
                params.author = null;
            }
            $scope.answerFiltersName = $("#answers-filter option:selected").text();
            $scope.answers = AnswerResource.get(params, function(response) {
                $scope.totalNumAnswers = response.total;

                $scope.rankCount = {};
                angular.forEach(response.objects, function(answer) {
                    angular.forEach(answer.scores, function(score) {
                        if (score.criterion_id == $scope.answerFilters.orderBy) {
                            if ($scope.rankCount[score.rank] == undefined) {
                                $scope.rankCount[score.rank] = 1;
                            } else {
                                ++$scope.rankCount[score.rank];
                            }
                        }
                    });
                });
            });
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.group != newValue.group) {
                $scope.answerFilters.author = null;
                if ($scope.answerFilters.group == null) {
                    userIds = $scope.getUserIds($scope.allStudents);
                    $scope.students = $scope.allStudents;
                } else {
                    GroupResource.get({'courseId': $scope.courseId, 'groupName': $scope.answerFilters.group},
                        function (ret) {
                            $scope.students = ret.students;
                            userIds = $scope.getUserIds(ret.students);
                        },
                        function (ret) {
                            Toaster.reqerror("Unable to retrieve the group members", ret);
                        }
                    );
                }
                $scope.answerFilters.page = 1;
            }
            if (oldValue.author != newValue.author) {
                userIds = {};
                $scope.answerFilters.top = null;
                if ($scope.answerFilters.author == null) {
                    userIds = $scope.getUserIds($scope.students);
                } else {
                    userIds[$scope.answerFilters.author] = 1;
                }
                if ($scope.answerFilters.author == "top-picks") {
                    $scope.answerFilters.top = true;
                    $scope.answerFilters.orderBy = null;
                }
                $scope.answerFilters.page = 1;
            }
            if (oldValue.top != newValue.top) {
                $scope.answerFilters.page = 1;
            }

            $scope.updateAnswerList();
        };
    }
]);
module.controller("AssignmentWriteController",
    [ "$scope", "$q", "$location", "$routeParams", "$route", "AssignmentResource", "$modal", "Authorize",
             "AssignmentCriterionResource", "CriterionResource", "required_rounds", "Toaster", "attachService",
             "AttachmentResource", "Session", "EditorOptions", "PairingAlgorithm", "ComparisonExampleResource",
             "AnswerResource",
    function($scope, $q, $location, $routeParams, $route, AssignmentResource, $modal, Authorize,
             AssignmentCriterionResource, CriterionResource, required_rounds, Toaster, attachService,
             AttachmentResource, Session, EditorOptions, PairingAlgorithm, ComparisonExampleResource,
             AnswerResource)
    {
        var courseId = $routeParams['courseId'];
        //initialize assignment so this scope can access data from included form
        $scope.assignment = {criteria: []};
        $scope.availableCriteria = [];
        $scope.editorOptions = EditorOptions.basic;
        $scope.PairingAlgorithm = PairingAlgorithm;

        $scope.uploader = attachService.getUploader();
        $scope.resetFileUploader = attachService.reset();
        $scope.recommended_comparisons = Math.floor(required_rounds / 2);
        $scope.comparison_example = {
            answer1: {},
            answer2: {}
        };

        Session.getUser().then(function(user) {
            $scope.loggedInUserId = user.id;
        });

        // DATETIMES
        // declaration
        var today = new Date();
        $scope.format = 'dd-MMMM-yyyy';
        $scope.date = {
            'astart': {'date': new Date(), 'time': new Date().setHours(0, 0, 0, 0)},
            'aend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
            'cstart': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
            'cend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)}
        };


        // initialization method data
        if ($route.current.method == "new") {
            // want default to disable discussion
            $scope.assignment.students_can_reply = false;
            // want default to only students comparing discussion
            $scope.assignment.educators_can_compare = false;
            // default the setting to the recommended # of comparisons
            $scope.assignment.number_of_comparisons = $scope.recommended_comparisons;
            $scope.assignment.pairing_algorithm = PairingAlgorithm.random;
            $scope.assignment.rank_display_limit = "0";

            $scope.date.astart.date.setDate(today.getDate()+1);
            $scope.date.aend.date.setDate(today.getDate()+8);
            $scope.date.cstart.date.setDate(today.getDate()+8);
            $scope.date.cend.date.setDate(today.getDate()+15);

        } else if ($route.current.method == "edit") {
            $scope.assignmentId = $routeParams['assignmentId'];
            AssignmentResource.get({'courseId': courseId, 'assignmentId': $scope.assignmentId}).$promise.then(
                function (ret) {
                    $scope.date.astart.date = new Date(ret.answer_start);
                    $scope.date.astart.time = new Date(ret.answer_start);
                    $scope.date.aend.date = new Date(ret.answer_end);
                    $scope.date.aend.time = new Date(ret.answer_end);

                    if (ret.compare_start && ret.compare_end) {
                        ret.availableCheck = true;
                        $scope.date.cstart.date = new Date(ret.compare_start);
                        $scope.date.cstart.time = new Date(ret.compare_start);
                        $scope.date.cend.date = new Date(ret.compare_end);
                        $scope.date.cend.time = new Date(ret.compare_end)
                    } else {
                        $scope.date.cstart.date = new Date($scope.date.aend.date);
                        $scope.date.cstart.time = new Date($scope.date.aend.time);
                        $scope.date.cend.date = new Date();
                        $scope.date.cend.date.setDate($scope.date.cstart.date.getDate()+7);
                        $scope.date.cend.time = new Date($scope.date.aend.time);
                        $scope.date.cstart.date = $scope.date.cstart.date;
                        $scope.date.cend.date = $scope.date.cend.date;
                    }
                    $scope.assignment = ret;
                    $scope.compared = ret.compared;
                    $scope.assignment.addPractice = false;
                    if ($scope.assignment.rank_display_limit != null) {
                        $scope.assignment.rank_display_limit = ret.rank_display_limit.toString();
                    } else {
                        $scope.assignment.rank_display_limit = "0";
                    }
                    // TODO: Remove temporary edit workaround when the pairing algorithm selection UI is in place
                    if ($scope.assignment.pairing_algorithm == null) {
                        $scope.assignment.pairing_algorithm = PairingAlgorithm.random;
                    }
                    if (ret.file) {
                        $scope.assignment.uploadedFile = ret.file;
                    }

                    ComparisonExampleResource.get({'courseId': courseId, 'assignmentId': $scope.assignmentId}).$promise.then(
                        function (ret) {
                            if (ret.objects.length > 0) {
                                $scope.comparison_example = ret.objects[0];
                                $scope.assignment.addPractice = true;
                            }
                        },
                        function () {
                            Toaster.reqerror("Assignment Practice Answers not Found", "No practice answers found for assignment with id "+$scope.assignmentId);
                        }
                    );
                },
                function () {
                    Toaster.reqerror("Assignment Not Found", "No assignment found for id "+$scope.assignmentId);
                }
            );
        }

        $scope.date.astart.open = function($event) {
            $event.preventDefault();
            $event.stopPropagation();

            $scope.date.astart.opened = true;
        };
        $scope.date.aend.open = function($event) {
            $event.preventDefault();
            $event.stopPropagation();

            $scope.date.aend.opened = true;
        };
        $scope.date.cstart.open = function($event) {
            $event.preventDefault();
            $event.stopPropagation();

            $scope.date.cstart.opened = true;
        };
        $scope.date.cend.open = function($event) {
            $event.preventDefault();
            $event.stopPropagation();

            $scope.date.cend.opened = true;
        };

        $scope.deleteFile = function(file) {
            AttachmentResource.delete({'fileId': file.id}).$promise.then(
                function () {
                    Toaster.success('Attachment Delete Successful', "This attachment was successfully deleted.");
                    $scope.assignment.file = null;
                    $scope.assignment.uploadedFile = false;
                },
                function (ret) {
                    Toaster.reqerror('Attachment Delete Failed', ret);
                }
            );
        };

        Authorize.can(Authorize.MANAGE, AssignmentCriterionResource.MODEL).then(function(result) {
            $scope.canManageCriteriaAssignment = result;
        });

        CriterionResource.get().$promise.then(function (ret) {
            $scope.availableCriteria = ret.objects;
            if (!$scope.assignment.criteria.length) {
                // if we don't have any criterion, e.g. new assignment, add a default one automatically
                $scope.assignment.criteria.push(_.find($scope.availableCriteria, {public: true}));
            }
            // we need to remove the existing assignment criteria from available list
            $scope.availableCriteria = _.filter($scope.availableCriteria, function(c) {
                return !_($scope.assignment.criteria).pluck('id').includes(c.id);
            });
        });

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
            if (criterion.default == true) {
                $scope.availableCriteria.push(criterion);
            }
        };

        $scope.changeCriterion = function(criterion) {
            var modalScope = $scope.$new();
            modalScope.criterion = angular.copy(criterion);
            modalScope.editorOptions = EditorOptions.basic;
            var modalInstance;
            var criterionUpdateListener = $scope.$on('CRITERION_UPDATED', function(event, c) {
                angular.copy(c, criterion);
                modalInstance.close();
            });
            var criterionAddListener = $scope.$on('CRITERION_ADDED', function(event, criterion) {
                $scope.assignment.criteria.push(criterion);
                modalInstance.close();
            });
            var criterionCancelListener = $scope.$on('CRITERION_CANCEL', function() {
                modalInstance.dismiss('cancel');
            });
            modalInstance = $modal.open({
                animation: true,
                template: '<criterion-form criterion=criterion editor-options=editorOptions></criterion-form>',
                scope: modalScope
            });
            // we need to remove the listener, otherwise on multiple click, multiple listeners will be registered
            modalInstance.result.finally(function(){
                criterionUpdateListener();
                criterionAddListener();
                criterionCancelListener();
            });
        };

        $scope.changeAnswer = function(answer, isAnswer1) {
            var modalScope = $scope.$new();
            modalScope.example = true;
            modalScope.answerName = isAnswer1 ? 'Answer A' : 'Answer B';
            modalScope.courseId = courseId;
            modalScope.assignmentId = $scope.assignment.id;
            modalScope.answer = angular.copy(answer);

            $scope.modalInstance = $modal.open({
                animation: true,
                controller: "AnswerModalController",
                templateUrl: 'modules/answer/answer-modal-partial.html',
                scope: modalScope
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
            });
        };

        // revealAnswer function shows full answer content for abbreviated answers (determined by getHeight directive)
        $scope.revealAnswer = function(answerId) {
            var thisClass = '.content.'+answerId;      // class for the answer to show is "content" plus the answer's ID
            $(thisClass).css({'max-height' : 'none'}); // now remove height restriction for this answer
            this.showReadMore = false;                 // and hide the read more button for this answer
        };

        $scope.assignmentSubmit = function () {
            $scope.submitted = true;
            $scope.assignment.answer_start = combineDateTime($scope.date.astart);
            $scope.assignment.answer_end = combineDateTime($scope.date.aend);
            $scope.assignment.compare_start = combineDateTime($scope.date.cstart);
            $scope.assignment.compare_end = combineDateTime($scope.date.cend);

            // answer end datetime has to be after answer start datetime
            if ($scope.assignment.answer_start >= $scope.assignment.answer_end) {
                Toaster.error('Answer Period Error', 'Answer end time must be after answer start time.');
                $scope.submitted = false;
                return;
            } else if ($scope.assignment.availableCheck && $scope.assignment.answer_start > $scope.assignment.compare_start) {
                Toaster.error("Time Period Error", 'Please double-check the answer and comparison period start and end times.');
                $scope.submitted = false;
                return;
            } else if ($scope.assignment.availableCheck && $scope.assignment.compare_start >= $scope.assignment.compare_end) {
                Toaster.error("Time Period Error", 'comparison end time must be after comparison start time.');
                $scope.submitted = false;
                return;
            }


            if ($scope.assignment.addPractice) {
                var answer1 = $scope.comparison_example.answer1;
                var answer2 = $scope.comparison_example.answer2;

                if ((!answer1.content || answer1.content.trim() == "") && !answer1.file && (!answer1.file_alias || answer1.file_alias == "")) {
                    Toaster.error("Practice Answer A Error", 'Practice answers needs to have content.');
                    $scope.submitted = false;
                    return;
                }
                if ((!answer2.content || answer2.content.trim() == "") && !answer2.file  && (!answer2.file_alias || answer2.file_alias == "")) {
                    Toaster.error("Practice Answer B Error", 'Practice answers needs to have content.');
                    $scope.submitted = false;
                    return;
                }
            }

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
            AssignmentResource.save({'courseId': courseId}, $scope.assignment)
                .$promise.then(function (ret) {
                    var assignmentId = ret.id;
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
                        if ($route.current.method == "new") {
                            Toaster.success("New Assignment Created",'"' + ret.name + '" should now be listed.');
                        } else {
                            Toaster.success("Assignment Updated");
                        }
                        $location.path('/course/' + courseId);
                    }, function() {
                        // error message handled elsewhere
                        $scope.submitted = false;
                    });
                },
                function (ret) {
                    $scope.submitted = false;
                    if ($route.current.method == "new") {
                        Toaster.reqerror("No New Assignment Created", ret);
                    } else {
                        Toaster.reqerror("Assignment Not Updated", ret);
                    }
                }
            );
        };

        var deleteComparisonsExample = function(assignmentId, comparison_example) {
            return $q(function(resolve, reject) {
                if (comparison_example.id) {
                    ComparisonExampleResource.delete({'courseId': courseId, 'assignmentId': assignmentId}, comparison_example)
                    .$promise.then(
                        function (ret) {
                            comparison_example.id = null;
                            resolve();
                        },
                        function (ret) {
                            Toaster.reqerror("Practice Answers Selete Failed.", ret);
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
                    ComparisonExampleResource.save({'courseId': courseId, 'assignmentId': assignmentId}, comparison_example)
                    .$promise.then(
                        function (ret) {
                            comparison_example.id = ret.id;
                            resolve();
                        },
                        function (ret) {
                            Toaster.reqerror("Practice Answers Save Failed.", ret);
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
                    AnswerResource.save({'courseId': courseId, 'assignmentId': assignmentId}, answer)
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
                            Toaster.reqerror("Practice Answer Save Failed.", ret);
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
