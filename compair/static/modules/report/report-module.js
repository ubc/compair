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
            {'id': 'participation', 'name': 'Basic Participation (best for grading purposes)'},
            {'id': 'participation_stat', 'name': 'Advanced Participation (best for research purposes)'},
            {'id': 'peer_feedback', 'name': 'Compiled Peer Feedback'}
        ];

        $scope.changeReport = function() {
            $scope.reportFile = null;
        };

        $scope.getGroupsAssignments = function() {
            $scope.reportFile = null;
            if ($scope.report.course_id === null || !$scope.report.course_id) {
                $scope.assignments = [];
                $scope.groups = [];
                return;
            }
            AssignmentResource.get({'courseId': $scope.report.course_id}).$promise.then(
                function (ret) {
                    $scope.report.assignment = 'all';
                    if (ret.objects.length > 0) {
                        ret.objects.push(all);
                    }
                    $scope.assignments = ret.objects;
                }
            );
            GroupResource.get({'courseId': $scope.report.course_id}).$promise.then(
                function (ret) {
                    $scope.report.group_id = 'all';
                    $scope.groups = ret.objects;
                    if ($scope.groups && $scope.groups.length > 0) {
                        $scope.groups.push(allGroups);
                    } else {
                        $scope.groups = [];
                    }
                }
            );
        };

        // decide on showing inline errors for download report form
        $scope.showErrors = function($event, formValid, noAssignments) {

            // show error if invalid form
            if (!formValid || noAssignments) {
                
                // don't submit
                $event.preventDefault();
                
                // set helper text and Toast
                $scope.helperMsg = "Sorry, this report couldn't be run yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this report couldn't be run yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";
                
                // display messages
                $scope.saveAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);
            }
            
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
                $scope.saveAttempted = false;
            });
        };
    }
]);

// End anonymous function
})();
