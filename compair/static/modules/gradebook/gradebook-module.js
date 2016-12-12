// Shows the instructor summary of student participations by assignment

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.gradebook',
    [
        'ngResource',
        'ngRoute',
        'localytics.directives',
        'ubc.ctlt.compair.common.xapi',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.group',
        'ubc.ctlt.compair.toaster'
    ]
);

/***** Providers *****/
module.factory(
    'GradebookResource',
    ['$resource',
    function($resource)
    {
        var ret = $resource('/api/courses/:courseId/assignments/:assignmentId/gradebook');
        return ret;
    }
]);

/***** Controllers *****/
module.controller("GradebookController",
    ["$scope", "$log", "$routeParams", "CourseResource", "GradebookResource",
        "GroupResource", "AssignmentResource", "Authorize", "Toaster", "AssignmentCriterionResource",
        "xAPIStatementHelper", "$filter",
    function($scope, $log, $routeParams, CourseResource, GradebookResource,
        GroupResource, AssignmentResource, Authorize, Toaster, AssignmentCriterionResource,
        xAPIStatementHelper, $filter)
    {
        $scope.users = [];
        $scope.gradebookFilters = {
            student: null,
            group: null,
            sortby: null
        };
        var userIds = {};
        $scope.isNumber = angular.isNumber;

        CourseResource.getStudents({'id': $scope.courseId}).$promise.then(
            function (ret) {
                $scope.allStudents = ret.objects;
                $scope.users = ret.objects;
                userIds = $scope.getUserIds(ret.objects);
            },
            function (ret) {
                Toaster.reqerror("Class list retrieval failed", ret);
            }
        );

        GradebookResource.get({'courseId': $scope.courseId,'assignmentId': $scope.assignmentId}).$promise.then(
            function(ret)
            {
                $scope.gradebook = ret['gradebook'];
                $scope.totalComparisonsRequired=ret['total_comparisons_required'];
                $scope.includeScores = ret['include_scores'];
                $scope.includeSelfEval = ret['include_self_evaluation'];
            },
            function (ret)
            {
                $scope.gradebook = [];
            }
        );

        Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId).then(function(result) {
            $scope.canManageAssignment = result;
            if ($scope.canManageAssignment) {
                GroupResource.get({'courseId': $scope.courseId}).$promise.then(
                    function (ret) {
                        $scope.groups = ret.objects;
                    },
                    function (ret) {
                        Toaster.reqerror("Unable to retrieve the groups in the course.", ret);
                    }
                );
            }
        });

        AssignmentCriterionResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}).$promise.then(
            function (ret) {
                $scope.criteria = ret['objects'];
                $scope.gradebookFilters.sortby = ret['objects'][0]['id'];
                $scope.$watchCollection('gradebookFilters', filterWatcher);
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve the criteria.", ret);
            }
        );

        $scope.groupFilter = function() {
            return function (entry) {
                return entry.user_id in userIds;
            }
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;

            if (oldValue.group != newValue.group) {
                $scope.gradebookFilters.student = null;
                if ($scope.gradebookFilters.group == null) {
                    userIds = $scope.getUserIds($scope.allStudents);
                    $scope.users = $scope.allStudents;
                } else {
                    GroupResource.get({'courseId': $scope.courseId, 'groupName': $scope.gradebookFilters.group}).$promise.then(
                        function (ret) {
                            $scope.users = ret.students;
                            userIds = $scope.getUserIds(ret.students);
                        },
                        function (ret) {
                            Toaster.reqerror("Unable to retrieve the group members", ret);
                        }
                    );
                }
            }
            if (oldValue.student != newValue.student) {
                userIds = {};
                if ($scope.gradebookFilters.student == null) {
                    userIds = $scope.getUserIds($scope.users);
                } else {
                    userIds[$scope.gradebookFilters.student.id] = 1;
                }
            }
            xAPIStatementHelper.filtered_page_section("participation tab", $scope.gradebookFilters);

            $scope.updateAnswerList();
        };

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            var orderBy = $scope.predicate + " " + ($scope.reverse ? "desc" : "asc");
            xAPIStatementHelper.sorted_page_section("participation tab", orderBy);
        }
    }
]);

// End anonymous function
})();
