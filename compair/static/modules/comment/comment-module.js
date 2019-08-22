// Handles comment creation and editing.

(function() {

var module = angular.module('ubc.ctlt.compair.comment',
    [
        'ngResource',
        'localytics.directives',
        'ubc.ctlt.compair.answer',
        'ubc.ctlt.compair.classlist',
        'ubc.ctlt.compair.learning_records.learning_record',
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

        $scope.editorOptions = EditorOptions.simplified;
        $scope.answerComment = true;
        $scope.AnswerCommentType = AnswerCommentType;
        $scope.saveFeedbackAttempted = false;

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
                            Toaster.error("Feedback Not Saved", "Sorry, feedback is not allowed for answers in this assignment.");
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

        // decide on showing inline errors
        $scope.showErrors = function($event, commentContent) {

            // show errors if no feedback written
            if (!commentContent) {

                // don't save
                $event.preventDefault();

                // set helper text and Toast
                $scope.helperMsg = "Sorry, this feedback couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this feeback couldn't be saved yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";

                // display messages
                $scope.saveFeedbackAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);

            } else {
                
                $scope.commentSubmit();
                
            }//closes if valid

        };//closes showErrors
        
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
                    Toaster.success("Feedback Saved");

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
