// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.report',
    [
        'ngResource',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.toaster'
    ]
);

/***** Providers *****/
module.factory('ReportResource',
    [ "$q", "$routeParams", "$resource",
    function($q, $routeParams, $resource)
{
    var ret = $resource('/api/courses/:id/report', {id: '@id'});
    ret.MODEL = "Course"; // add constant to identify the model
        // being used, this is for permissions checking
        // and should match the server side model name
    return ret;
}]);

/***** Controllers *****/
module.controller(
    'ReportCreateController',
    [ "$scope", "$log", "CourseResource", "ReportResource", "UserResource",
             "GroupResource", "AssignmentResource", "Toaster", "resolvedData",
    function($scope, $log, CourseResource, ReportResource, UserResource,
             GroupResource, AssignmentResource, Toaster, resolvedData)
    {
        $scope.courses = resolvedData.coursesAsInstructor.courses;

        $scope.report = {};
        $scope.assignments = [];
        $scope.groups = [];

        var all = {'id': 'all', 'name': 'All Assignments'};
        var allGroups = {'name': 'All Groups', 'id': 'all'};
        $scope.types = [
            {'id': 'participation', 'name': 'Basic Participation Report'},
            {'id': 'participation_stat', 'name': 'Participation Report for Research Teams'},
            {'id': 'peer_feedback', 'name': 'Compiled Peer Feedback Report'}
        ];

        $scope.changeReport = function() {
            $scope.reportFile = null;
        };

        $scope.getAssignments = function() {
            $scope.reportFile = null;
            if ($scope.report.course_id == null) {
                $scope.assignments = [];
                return;
            }
            GroupResource.get({'courseId': $scope.report.course_id}).$promise.then(
                function (ret) {
                    $scope.report.group_id = 'all';
                    $scope.groups = ret.objects;
                    if ($scope.groups && $scope.groups.length > 0) {
                        $scope.groups.push(allGroups);
                    }
                }
            );
            AssignmentResource.get({'courseId': $scope.report.course_id}).$promise.then(
                function (ret) {
                    $scope.report.assignment = null;
                    if (ret.objects.length > 0) {
                        ret.objects.push(all);
                    }
                    $scope.assignments = ret.objects;
                }
            );
        };

        $scope.reportSubmit = function() {
            $scope.reportFile = null;
            $scope.submitted = true;
            var report = angular.copy($scope.report);
            if (report.assignment == 'all') {
                delete report.assignment;
            }
            if (report.group_id == 'all') {
                delete report.group_id;
            }

            ReportResource.save({'id': report.course_id}, report).$promise.then(
                function (ret) {
                    $scope.reportFile = ret.file;
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }
]);

// End anonymous function
})();
