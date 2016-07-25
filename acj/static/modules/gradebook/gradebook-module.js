// Shows the instructor summary of student participations by assignment

// Isolate this module's creation by putting it in an anonymous function
(function() {

// TODO
// Create the module with a unique name.
// The module needs a unique name that prevents conflicts with 3rd party modules
// We're using "ubc.ctlt.acj" as the project's prefix, followed by the module
// name.
var module = angular.module('ubc.ctlt.acj.gradebook',
    [
        'ngResource',
        'ngRoute',
        'ubc.ctlt.acj.course',
        'ubc.ctlt.acj.group',
        'ubc.ctlt.acj.toaster'
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
    function($scope, $log, $routeParams, CourseResource, GradebookResource,
        GroupResource, AssignmentResource, Authorize, Toaster, AssignmentCriterionResource)
    {
        $scope.users = [];
        $scope.gb = {};
        var userIds = {};

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

        AssignmentCriterionResource.get(
            {'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}).$promise.then(
            function (ret) {
                $scope.criteria = ret['objects'];
                $scope.gb['sortby'] = ret['objects'][0]['id'];
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve the criteria.", ret);
            }
        );

        $scope.groupChange = function() {
            $scope.gb.student = null;
            if ($scope.gb.group == null) {
                userIds = $scope.getUserIds($scope.allStudents);
                $scope.users = $scope.allStudents;
            } else {
                GroupResource.get({'courseId': $scope.courseId, 'groupName': $scope.gb.group}).$promise.then(
                    function (ret) {
                        $scope.users = ret.students;
                        userIds = $scope.getUserIds(ret.students);
                    },
                    function (ret) {
                        Toaster.reqerror("Unable to retrieve the group members", ret);
                    }
                );
            }
        };

        $scope.userChange = function() {
            userIds = {};
            if ($scope.gb.student == null) {
                userIds = $scope.getUserIds($scope.users);
            } else {
                userIds[$scope.gb.student.id] = 1;
            }
        };

        $scope.groupFilter = function() {
            return function (entry) {
                return entry.userid in userIds;
            }
        };

        $scope.sortScore = function() {
            $scope.predicate = 'scores['+$scope.gb.sortby+']';
        }

    }
]);

// End anonymous function
})();
