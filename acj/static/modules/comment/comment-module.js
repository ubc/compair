// Handles comment creation and editing.

(function() {

var module = angular.module('ubc.ctlt.acj.comment',
    [
        'ngResource',
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
    "AssignmentCommentCreateController",
    ['$scope', '$log', '$location', '$routeParams', 'AssignmentCommentResource', 'AssignmentResource', 'Toaster',
     'EditorOptions',
    function ($scope, $log, $location, $routeParams, AssignmentCommentResource, AssignmentResource, Toaster,
              EditorOptions)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];

        $scope.editorOptions = EditorOptions.basic;

        $scope.comment = {};
        AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
            function(ret) {
                $scope.parent = ret;
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve the assignment "+assignmentId, ret);
            }
        );
        $scope.commentSubmit = function () {
            $scope.submitted = true;
            AssignmentCommentResource.save({'courseId': courseId, 'assignmentId': assignmentId},
                $scope.comment).$promise.then(
                    function (ret)
                    {
                        $scope.submitted = false;
                        Toaster.success("New comment posted!");
                        $location.path('/course/'+courseId+'/assignment/'+assignmentId);
                    },
                    function (ret)
                    {
                        $scope.submitted = false;
                        Toaster.reqerror("Unable to post new comment.", ret);
                    }
                );
        };
    }]
);

module.controller(
    "AssignmentCommentEditController",
    ['$scope', '$log', '$location', '$routeParams', 'AssignmentCommentResource', 'AssignmentResource', 'Toaster',
     'EditorOptions',
    function ($scope, $log, $location, $routeParams, AssignmentCommentResource, AssignmentResource, Toaster,
              EditorOptions)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        var commentId = $routeParams['commentId'];

        $scope.editorOptions = EditorOptions.basic;

        $scope.comment = {};
        $scope.parent = {}; // assignment
        AssignmentCommentResource.get({'courseId': courseId, 'assignmentId': assignmentId, 'commentId': commentId}).$promise.then(
            function(ret) {
                $scope.comment = ret;
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve comment "+commentId, ret);
            }
        );
        AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
            function(ret) {
                $scope.parent = ret;
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve the assignment "+assignmentId, ret);
            }
        );
        $scope.commentSubmit = function () {
            AssignmentCommentResource.save({'courseId': courseId, 'assignmentId': assignmentId}, $scope.comment).$promise.then(
                function() {
                    Toaster.success("Comment Updated!");
                    $location.path('/course/' + courseId + '/assignment/' +assignmentId);
                },
                function(ret) { Toaster.reqerror("Comment Save Failed.", ret);}
            );
        };
    }]
);

module.controller(
    "AnswerCommentCreateController",
    ['$scope', '$log', '$location', '$routeParams', 'AnswerCommentResource', 'AnswerResource',
        'AssignmentResource', 'Authorize', 'Toaster', 'AnswerCommentType', 'EditorOptions',
    function ($scope, $log, $location, $routeParams, AnswerCommentResource, AnswerResource,
              AssignmentResource, Authorize, Toaster, AnswerCommentType, EditorOptions)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        var answerId = $routeParams['answerId'];

        $scope.editorOptions = EditorOptions.basic;

        $scope.AnswerCommentType = AnswerCommentType;
        $scope.answerComment = true;
        $scope.canManageAssignment =
            Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, courseId);
        $scope.comment = {
            'comment_type': AnswerCommentType.private
        };

        $scope.parent = AnswerResource.get({'courseId': courseId, 'assignmentId': assignmentId, 'answerId': answerId});

        // only need to do this query if the user cannot manage users
        AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise.then(
            function (ret) {
                if (!$scope.canManageAssignment && !ret.students_can_reply) {
                    Toaster.error("No replies can be made for answers in this assignment.");
                    $location.path('/course/' + courseId + '/assignment/' + assignmentId);
                }
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve the assignment.", ret);
            });
        $scope.commentSubmit = function () {
            $scope.submitted = true;
            AnswerCommentResource.save({'courseId': courseId, 'assignmentId': assignmentId, 'answerId': answerId},
                $scope.comment).$promise.then(
                    function (ret)
                    {
                        $scope.submitted = false;
                        Toaster.success("New reply posted!");
                        $location.path('/course/'+courseId+'/assignment/'+assignmentId);
                    },
                    function (ret)
                    {
                        $scope.submitted = false;
                        Toaster.reqerror("Unable to post new reply.", ret);
                    }
                );
        };
    }]
);

module.controller(
    "AnswerCommentEditController",
    ['$scope', '$log', '$location', '$routeParams', 'AnswerCommentResource', 'AnswerResource', 'Toaster',
     'AnswerCommentType', 'EditorOptions',
    function ($scope, $log, $location, $routeParams, AnswerCommentResource, AnswerResource, Toaster, AnswerCommentType,
              EditorOptions)
    {
        var courseId = $scope.courseId = $routeParams['courseId'];
        var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
        var answerId = $routeParams['answerId'];
        var commentId = $routeParams['commentId'];

        $scope.editorOptions = EditorOptions.basic;

        $scope.answerComment = true;
        $scope.AnswerCommentType = AnswerCommentType;

        $scope.comment = AnswerCommentResource.get({'courseId': courseId, 'assignmentId': assignmentId, 'answerId': answerId, 'commentId': commentId});
        $scope.parent = AnswerResource.get({'courseId': courseId, 'assignmentId': assignmentId, 'answerId': answerId});
        $scope.commentSubmit = function () {
            AnswerCommentResource.save({'courseId': courseId, 'assignmentId': assignmentId, 'answerId': answerId, 'commentId': commentId}, $scope.comment).$promise.then(
                function() {
                    Toaster.success("Reply Updated!");
                    $location.path('/course/' + courseId + '/assignment/' +assignmentId);
                },
                function(ret) { Toaster.reqerror("Reply Not Updated", ret);}
            );
        };
    }]
);

module.controller(
    "ComparisonCommentController",
    ['$scope', '$log', '$routeParams', 'breadcrumbs', 'CourseResource', 'AssignmentResource',
        'AnswerResource', 'AnswerCommentResource', 'AttachmentResource', 'GroupResource', 'Toaster',
    function ($scope, $log, $routeParams, breadcrumbs, CourseResource, AssignmentResource,
        AnswerResource, AnswerCommentResource, AttachmentResource, GroupResource, Toaster)
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

        GroupResource.get({'courseId': courseId},
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
