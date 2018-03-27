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
    ["$scope", "$window", "$routeParams", "CourseResource", "GradebookResource",
        "GroupResource", "AssignmentResource", "Authorize", "Toaster",
        "xAPIStatementHelper", "$filter",
    function($scope, $window, $routeParams, CourseResource, GradebookResource,
        GroupResource, AssignmentResource, Authorize, Toaster,
        xAPIStatementHelper, $filter)
    {
        $scope.users = [];
        $scope.gradebookFilters = {
            student: null,
            group: null
        };
        var userIds = {};
        $scope.isNumber = angular.isNumber;
        $scope.gradebook = [];

        $scope.updateUserIds = function(students) {
            userIds = {};
            angular.forEach(students, function(s){
                userIds[s.id] = 1;
            });
        };

        CourseResource.getStudents({'id': $scope.courseId}).$promise.then(
            function (ret) {
                $scope.allStudents = ret.objects;
                $scope.users = ret.objects;
                $scope.updateUserIds(ret.objects);
            }
        );

        GradebookResource.get({'courseId': $scope.courseId,'assignmentId': $scope.assignmentId}).$promise.then(
            function(ret)
            {
                $scope.gradebook = ret['gradebook'];
                $scope.showAttachments = false;
                $scope.gradebook.forEach(function(entry) {
                    if (entry.file) {
                        $scope.showAttachments = true;
                    }
                    // download file name is student number + full name (if student number is set)
                    entry.download_file_name = ""
                    if (entry.user.student_number) {
                        entry.download_file_name = entry.user.student_number + " ";
                    }
                    entry.download_file_name += entry.user.fullname;
                });
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
                    }
                );
            }
        });

        $scope.groupFilter = function() {
            return function (entry) {
                return entry.user && userIds[entry.user.id];
            }
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;

            if (oldValue.group != newValue.group) {
                $scope.gradebookFilters.student = null;
                if ($scope.gradebookFilters.group == null) {
                    $scope.updateUserIds($scope.allStudents);
                } else {
                    GroupResource.get({'courseId': $scope.courseId, 'groupName': $scope.gradebookFilters.group}).$promise.then(
                        function (ret) {
                            $scope.updateUserIds(ret.objects);
                        }
                    );
                }
            }
            if (oldValue.student != newValue.student) {
                userIds = {};
                if ($scope.gradebookFilters.student == null) {
                    $scope.updateUserIds($scope.users);
                } else {
                    userIds[$scope.gradebookFilters.student.id] = 1;
                }
            }
            xAPIStatementHelper.filtered_page_section("participation tab", $scope.gradebookFilters);

            $scope.updateAnswerList();
        };
        $scope.$watchCollection('gradebookFilters', filterWatcher);

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
