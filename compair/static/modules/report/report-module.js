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
    [ "$q", "$routeParams", "$log", "$resource",
    function($q, $routeParams, $log, $resource)
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
             "GroupResource", "AssignmentResource", "Session", "Toaster",
    function($scope, $log, CourseResource, ReportResource, UserResource,
             GroupResource, AssignmentResource, Session, Toaster)
    {
        $scope.report = {
            'type': 'participation',
            'group_name': 'all'
        };
        $scope.courses = {};
        $scope.assignments = [];
        $scope.groups = [];

        var all = {'id': 'all', 'name': 'All Assignments'};
        var allGroups = {'name': 'All Groups', 'value': 'all'};
        $scope.types = [
            {'id': 'participation', 'name': 'Participation Report (Regular)'},
            {'id': 'participation_stat', 'name': 'Participation Report (Research)'}
        ];

        UserResource.getTeachingUserCourses().$promise.then(
            function(ret) {
                $scope.courses = ret.courses;
            },
            function (ret) {
                Toaster.reqerror("Unable to retrieve your courses.", ret);
            }
        );

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
                    $scope.report.group_name = 'all';
                    $scope.groups = [];
                    _.each(ret.objects, function(value) {
                        $scope.groups.push({
                            'name': value,
                            'value': value
                        })
                    });
                    if ($scope.groups.length > 0) {
                        $scope.groups.push(allGroups);
                    }
                },
                function(ret) {
                    Toaster.reqerror('Unable to retrieve groups', ret);
                }
            );
            AssignmentResource.get({'courseId': $scope.report.course_id}).$promise.then(
                function (ret) {
                    $scope.report.assignment = null;
                    if (ret.objects.length > 0) {
                        ret.objects.push(all);
                    }
                    $scope.assignments = ret.objects;
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve course assignments: " + courseId, ret);
                }
            );
        };

        $scope.reportSubmit = function() {
            $scope.reportFile = null;
            $scope.submitted = true;
            var report = angular.copy($scope.report);
            if (report.assignment == 'all')
                delete report.assignment;
            if (report.group_name == 'all')
                delete report.group_name;
            ReportResource.save({'id': report.course_id}, report).$promise.then(
                function (ret) {
                    $scope.reportFile = ret.file;
                    $scope.submitted = false;
                },
                function (ret) {
                    $scope.submitted = false;
                    Toaster.reqerror("Export Report Failed.", ret);
                }
            );
        };
    }
]);

// End anonymous function
})();
