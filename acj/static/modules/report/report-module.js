// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.report',
	[
		'ngResource',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory('ReportResource', function($q, $routeParams, $log, $resource)
{
	var ret = $resource('/api/courses/:id/report', {id: '@id'});
	ret.MODEL = "Courses"; // add constant to identify the model
		// being used, this is for permissions checking
		// and should match the server side model name
	return ret;
});

/***** Controllers *****/
module.controller(
	'ReportCreateController',
	function($scope, $log, CourseResource, ReportResource, UserResource,
			 GroupResource, QuestionResource, Session, Toaster)
	{
		$scope.report = {
			'type': 'participation',
			'group_id': 'all'
		};
		$scope.courses = {};
		$scope.assignments = [];
		$scope.groups = [];

		var all = [{'id': 'all', 'title': 'All Assignments'}];
		var allGroups = [{'id': 'all', 'name': 'All Groups'}]
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
					$scope.report.group_id = 'all';
					if (ret.groups.length > 0) {
						ret.groups = ret.groups.concat(allGroups);
					}
					$scope.groups = ret.groups;
				},
				function(ret) {
					Toaster.reqerror('Unable to retrieve groups', ret);
				}
			);
			QuestionResource.get({'courseId': $scope.report.course_id}).$promise.then(
				function (ret) {
					$scope.report.assignment = null;
					if (ret.questions.length > 0) {
						ret.questions = ret.questions.concat(all);
					}
					$scope.assignments = ret.questions;
				},
				function (ret) {
					Toaster.reqerror("Unable to retrieve course questions: " + courseId, ret);
				}
			);
		};

		$scope.reportSubmit = function() {
			$scope.reportFile = null;
			$scope.submitted = true;
			var report = angular.copy($scope.report);
			if (report.assignment == 'all')
				delete report.assignment;
			if (report.group_id == 'all')
				delete report.group_id;
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
);

// End anonymous function
})();
