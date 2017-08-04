// Handles comment creation and editing.

(function() {

var module = angular.module('ubc.ctlt.compair.comment',
    [
        'ngResource',
        'localytics.directives',
        'ubc.ctlt.compair.answer',
        'ubc.ctlt.compair.classlist',
        'ubc.ctlt.compair.common.xapi',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.rich.content',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.criterion',
        'ubc.ctlt.compair.comparison',
        'ubc.ctlt.compair.assignment',
        'ubc.ctlt.compair.toaster'
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

module.directive('compairStudentAnswer', function() {
    return {
        scope: {
            answer: '='
        },
        templateUrl: 'modules/comment/answer.html'
    }
});

module.directive('compairAnswerContent', function() {
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
     'EditorOptions', "$uibModalInstance",
    function ($scope, AssignmentCommentResource, AssignmentResource, Toaster,
              EditorOptions, $uibModalInstance)
    {
        //$scope.courseId
        //$scope.assignmentId
        $scope.comment = typeof($scope.comment) != 'undefined' ? $scope.comment : {};
        $scope.method = $scope.comment.id ? 'edit' : 'create';
        $scope.modalInstance = $uibModalInstance;
        $scope.editorOptions = EditorOptions.basic;

        $scope.parent = AssignmentResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId});

        if ($scope.method == 'edit') {
            AssignmentCommentResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId, 'commentId': $scope.comment.id}).$promise.then(
                function(ret) {
                    $scope.comment = ret;
                }
            );
        }
        $scope.commentSubmit = function () {
            $scope.submitted = true;

            AssignmentCommentResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $scope.comment)
            .$promise.then(
                function (ret) {
                    $scope.comment = ret;
                    if ($scope.method == 'create') {
                        Toaster.success("Comment Created");
                    } else {
                        Toaster.success("Comment Updated");
                    }

                    $uibModalInstance.close($scope.comment);
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }]
);

module.controller(
    "AnswerCommentModalController",
    ['$scope', 'AnswerCommentResource', 'AnswerResource', 'Toaster', 'Authorize',
     'AnswerCommentType', 'AssignmentResource', 'EditorOptions', "$uibModalInstance",
    function ($scope, AnswerCommentResource, AnswerResource, Toaster, Authorize,
              AnswerCommentType, AssignmentResource, EditorOptions, $uibModalInstance)
    {
        //$scope.courseId
        //$scope.assignmentId
        //$scope.answerId
        $scope.comment = typeof($scope.comment) != 'undefined' ? $scope.comment : {};
        $scope.method = $scope.comment.id ? 'edit' : 'create';
        $scope.modalInstance = $uibModalInstance;

        $scope.editorOptions = EditorOptions.basic;
        $scope.answerComment = true;
        $scope.AnswerCommentType = AnswerCommentType;

        if ($scope.method == 'create') {
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
                            $uibModalInstance.dismiss();
                        }
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

                    if ($scope.method == 'create') {
                        Toaster.success("Reply Created");
                    } else {
                        Toaster.success("Reply Updated");
                    }

                    $uibModalInstance.close($scope.comment);
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }]
);

// End anonymouse function
}) ();
