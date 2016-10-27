// Handles comment creation and editing.

(function() {

var module = angular.module('ubc.ctlt.acj.comment',
    [
        'ngResource',
        'localytics.directives',
        'ubc.ctlt.acj.answer',
        'ubc.ctlt.acj.classlist',
        'ubc.ctlt.acj.common.form',
        'ubc.ctlt.acj.common.mathjax',
        'ubc.ctlt.acj.common.highlightjs',
        'ubc.ctlt.acj.common.interceptor',
        'ubc.ctlt.acj.course',
        'ubc.ctlt.acj.criterion',
        'ubc.ctlt.acj.comparison',
        'ubc.ctlt.acj.assignment',
        'ubc.ctlt.acj.toaster'
    ]
);

/***** Providers *****/
module.factory("AssignmentCommentResource", ['$resource', function ($resource) {
    var ret = $resource(
        '/api/courses/:courseId/assignments/:assignmentId/comments/:commentId',
        {commentId: '@id'}
    );
    ret.MODEL = "AssignmentComment";
    return ret;
}]);

module.factory("AnswerCommentResource", ['$resource', 'Interceptors', function ($resource, Interceptors) {
    var url = '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId/comments/:commentId';
    var ret = $resource(
        url, {commentId: '@id'},
        {
            'get': {cache: true},
            'save': {method: 'POST', url: url, interceptor: Interceptors.answerCommentCache},
            'delete': {method: 'DELETE', url: url, interceptor: Interceptors.answerCommentCache},
            query: {url: '/api/courses/:courseId/assignments/:assignmentId/answer_comments', isArray: true}
        }
    );
    ret.MODEL = "AnswerComment";
    return ret;
}]);

module.constant('AnswerCommentType', {
    public: "Public",
    private: "Private",
    evaluation: "Evaluation",
    self_evaluation: "Self Evaluation"
});



module.filter('author', function() {
    return function(input, authorId) {
        if (angular.isObject(input)) {
            input = _.values(input);
        }
        return _.find(input, {'user_id': authorId});
    };
});

module.directive('acjStudentAnswer', function() {
    return {
        scope: {
            answer: '='
        },
        templateUrl: 'modules/comment/answer.html'
    }
});

module.directive('acjAnswerContent', function() {
    return {
        scope: {
            answer: '=',
            name: '@',
            isChosen: '=',
            criterion: '=',
            showScore: '='
        },
        templateUrl: 'modules/comment/answer-content.html'
    }
});

/***** Controllers *****/
module.controller(
    "AssignmentCommentModalController",
    ['$scope', 'AssignmentCommentResource', 'AssignmentResource', 'Toaster',
     'EditorOptions', "$modalInstance",
    function ($scope, AssignmentCommentResource, AssignmentResource, Toaster,
              EditorOptions, $modalInstance)
    {
        //$scope.courseId
        //$scope.assignmentId
        $scope.comment = typeof($scope.comment) != 'undefined' ? $scope.comment : {};
        $scope.method = $scope.comment.id ? 'edit' : 'new';
        $scope.modalInstance = $modalInstance;
        $scope.editorOptions = EditorOptions.basic;

        $scope.parent = AssignmentResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId});

        if ($scope.method == 'edit') {
            AssignmentCommentResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId, 'commentId': $scope.comment.id}).$promise.then(
                function(ret) {
                    $scope.comment = ret;
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve comment "+$scope.comment.id, ret);
                }
            );
        }
        $scope.commentSubmit = function () {
            $scope.submitted = true;

            AssignmentCommentResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $scope.comment)
            .$promise.then(
                function (ret) {
                    $scope.comment = ret;
                    $scope.submitted = false;

                    if ($scope.method == 'new') {
                        Toaster.success("New Comment Created!");
                    } else {
                        Toaster.success("Comment Updated!");
                    }

                    $modalInstance.close($scope.comment);
                },
                function (ret)
                {
                    $scope.submitted = false;
                    Toaster.reqerror("Comment Save Failed.", ret);
                }
            );
        };
    }]
);

module.controller(
    "AnswerCommentModalController",
    ['$scope', 'AnswerCommentResource', 'AnswerResource', 'Toaster', 'Authorize',
     'AnswerCommentType', 'AssignmentResource', 'EditorOptions', "$modalInstance",
    function ($scope, AnswerCommentResource, AnswerResource, Toaster, Authorize,
              AnswerCommentType, AssignmentResource, EditorOptions, $modalInstance)
    {
        //$scope.courseId
        //$scope.assignmentId
        //$scope.answerId
        $scope.comment = typeof($scope.comment) != 'undefined' ? $scope.comment : {};
        $scope.method = $scope.comment.id ? 'edit' : 'new';
        $scope.modalInstance = $modalInstance;

        $scope.editorOptions = EditorOptions.basic;
        $scope.answerComment = true;
        $scope.AnswerCommentType = AnswerCommentType;

        if ($scope.method == 'new') {
            $scope.comment = {
                'comment_type': AnswerCommentType.private
            }
            $scope.canManageAssignment = Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId);
            // only need to do this query if the user cannot manage users
            if (!$scope.canManageAssignment) {
                AssignmentResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId})
                .$promise.then(
                    function (ret) {
                        if (!ret.students_can_reply) {
                            Toaster.error("No replies can be made for answers in this assignment.");
                            $modalInstance.dismiss();
                        }
                    },
                    function (ret) {
                        Toaster.reqerror("Unable to retrieve the assignment.", ret);
                    }
                );
            }
        } else if($scope.method == 'edit') {
            // refresh the answer if already exists
            $scope.comment = AnswerCommentResource.get({
                'courseId': $scope.courseId,
                'assignmentId': $scope.assignmentId,
                'answerId': $scope.answerId,
                'commentId': $scope.comment.id
            });
        }
        $scope.parent = AnswerResource.get({
            'courseId': $scope.courseId,
            'assignmentId': $scope.assignmentId,
            'answerId': $scope.answerId
        });

        $scope.commentSubmit = function () {
            $scope.submitted = true;

            AnswerCommentResource.save({
                'courseId': $scope.courseId,
                'assignmentId': $scope.assignmentId,
                'answerId': $scope.answerId,
                'commentId': $scope.comment.id
            }, $scope.comment).$promise.then(
                function(ret) {
                    $scope.comment = ret;
                    $scope.submitted = false;

                    if ($scope.method == 'new') {
                        Toaster.success("Reply Created!");
                    } else {
                        Toaster.success("Reply Updated!");
                    }

                    $modalInstance.close($scope.comment);
                },
                function(ret) {
                    $scope.submitted = false;
                    if ($scope.method == 'new') {
                        Toaster.reqerror("Reply Not Created", ret);
                    } else {
                        Toaster.reqerror("Reply Not Updated", ret);
                    }
                }
            );
        };
    }]
);

module.controller(
    "ComparisonCommentController",
    ['$scope', '$log', '$routeParams', 'breadcrumbs', 'CourseResource', 'AssignmentResource',
        'AnswerResource', 'AnswerCommentResource', 'GroupResource', 'Toaster',
    function ($scope, $log, $routeParams, breadcrumbs, CourseResource, AssignmentResource,
        AnswerResource, AnswerCommentResource, GroupResource, Toaster)
    {
        var courseId = $routeParams['courseId'];
        var assignmentId = $routeParams['assignmentId'];
        $scope.courseId = courseId;
        $scope.assignmentId = assignmentId;
        $scope.listFilters = {
            page: 1,
            perPage: 20,
            group: null,
            author: null
        };
        $scope.answers = [];

        CourseResource.get({'id':courseId},
            function (ret) {
                breadcrumbs.options = {'Course assignments': ret['name']};
            },
            function (ret) {
                Toaster.reqerror("Course Not Found For ID "+ courseId, ret);
            }
        );

        $scope.students = CourseResource.getStudents({'id': courseId},
            function (ret) {},
            function (ret) {
                Toaster.reqerror("Class list retrieval failed", ret);
            }
        );

        AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId},
            function(ret) {
                $scope.parent = ret;
                $scope.criteria = {};
                angular.forEach(ret.criteria, function(criterion, key){
                    $scope.criteria[criterion['id']] = criterion['name'];
                });
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve the assignment "+assignmentId, ret);
            }
        );

        $scope.groups = GroupResource.get({'courseId': courseId},
            function (ret) {
                $scope.groups = ret.objects
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve the groups in the course.", ret);
            }
        );

        $scope.loadAnswerByAuthor = function(author_id) {
            if (_.find($scope.answers, {user_id: author_id})) return;
            AnswerResource.get({'courseId': courseId, 'assignmentId': assignmentId, 'author': author_id}, function(response) {
                var answer = response.objects[0];
                $scope.answers.push(convertScore(answer));
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
            $scope.updateList();
        });

        $scope.updateList = function() {
            var params = angular.merge({'courseId': $scope.courseId, 'assignmentId': assignmentId}, $scope.listFilters);

            AnswerResource.comparisons(params, function(ret) {
                $scope.comparisons = ret;
                $scope.comparisons.grouped = _.groupBy($scope.comparisons.objects, 'user_id');
            });
        };

        $scope.updateList();
    }]
);

function convertScore(answer) {
    var scores = answer.scores;
    answer.scores = _.reduce(scores, function(results, score) {
        results[score.criterion_id] = score.normalized_score;
        return results;
    }, {});

    return answer;
}
// End anonymouse function
}) ();
