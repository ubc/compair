// Shows the instructor summary of student participations by question

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
	function($resource)
	{
		var ret = $resource('/api/courses/:courseId/questions/:questionId/gradebook');
		return ret;
	}
);

/***** Controllers *****/
module.controller("GradebookController",
	function($scope, $log, $routeParams, CourseResource, GradebookResource, 
		GroupResource, Toaster)
	{
		$scope.users = [];
		var userIds = {};

		CourseResource.getStudents({'id': $scope.courseId}).$promise.then(
			function (ret) {
				$scope.allStudents = ret.students;
				$scope.users = ret.students;
				userIds = $scope.getUserIds(ret.students);
			},
			function (ret) {
				Toaster.reqerror("Class list retrieval failed", ret);
			}
		);
		$scope.gb = {};
		GradebookResource.get(
			{'courseId': $scope.courseId,'questionId': $scope.questionId}).$promise.then(
			function(ret)
			{
				$scope.gradebook = ret['gradebook'];
				$scope.numJudgementsRequired=ret['num_judgements_required'];
				$scope.includeSelfEval = ret['include_self_eval'];
			},
			function (ret)
			{
				$scope.gradebook = [];
			}
		);

		$scope.groupChange = function() {
			$scope.gb.student = null;
			if ($scope.gb.group == null) {
				userIds = $scope.getUserIds($scope.allStudents);
				$scope.users = $scope.allStudents;
			} else {
				GroupResource.get({'courseId': $scope.courseId, 'groupId': $scope.gb.group.id}).$promise.then(
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
				userIds[$scope.gb.student.user.id] = 1;
			}
		};

		$scope.groupFilter = function() {
			return function (entry) {
				return entry.userid in userIds;
			}
		};

	}
);

// End anonymous function
})();
