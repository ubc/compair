// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.course',
	[
		'angularMoment',
		'ngResource',
		'ngRoute',
		'ckeditor',
		'ui.bootstrap',
		'ubc.ctlt.acj.comment',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.interceptor',
		'ubc.ctlt.acj.comparison',
		'ubc.ctlt.acj.assignment',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory('CourseResource',
	["$q", "$routeParams", "$log", "$resource", "Interceptors",
	function($q, $routeParams, $log, $resource, Interceptors)
{
	var url = '/api/courses/:id';
	var ret = $resource('/api/courses/:id', {id: '@id'},
		{
			// would enable caching for GET but there's no automatic cache
			// invalidation, I don't want to deal with that manually
			'get': {url: url, cache: true},
			'save': {method: 'POST', url: url, interceptor: Interceptors.cache},
			'delete': {method: 'DELETE', url: url, interceptor: Interceptors.cache},
			'getComparisonCount': {url: '/api/courses/:id/comparisons/count'},
			'getComparisonAvailable': {url: '/api/courses/:id/comparisons/available'},
			'getAnswered': {url: '/api/courses/:id/answered'},
			'getInstructorsLabels': {url: '/api/courses/:id/users/instructors/labels'},
			'getStudents': {url: '/api/courses/:id/users/students'}
		}
	);
	ret.MODEL = "Course"; // add constant to identify the model
		// being used, this is for permissions checking
		// and should match the server side model name
	return ret;
}]);

/***** Controllers *****/
module.controller(
	'CourseAssignmentsController',
	["$scope", "$log", "$routeParams", "CourseResource", "AssignmentResource", "Authorize",
			 "AuthenticationService", "required_rounds", "Toaster",
	function($scope, $log, $routeParams, CourseResource, AssignmentResource, Authorize,
			 AuthenticationService, required_rounds, Toaster)
	{
		// get course info
		var courseId = $scope.courseId = $routeParams['courseId'];
		$scope.answered = {};
		$scope.count = {};
		$scope.filters = [];
		Authorize.can(Authorize.CREATE, AssignmentResource.MODEL, courseId).then(function(result) {
				$scope.canCreateAssignments = result;
		});
		Authorize.can(Authorize.EDIT, CourseResource.MODEL, courseId).then(function(result) {
				$scope.canEditCourse = result;
		});
		Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, courseId).then(function(result) {
				$scope.canManageAssignment = result;
				$scope.filters.push('All course assignments');
				if ($scope.canManageAssignment) {
					$scope.filters.push('Assignments being answered', 'Assignments being compared', 'Upcoming assignments');
				} else {
					$scope.filters.push('My pending assignments');
				}
				$scope.filter = $scope.filters[0];
		});
		CourseResource.get({'id': courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Course Not Found For ID "+ courseId, ret);
			}
		);

		CourseResource.getComparisonAvailable({'id': courseId}).$promise.then(
			function (ret) {
				$scope.comparisonAvailable = ret.available;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the answer pairs availablilty.", ret);
			}
		);

		// get course assignments
		AssignmentResource.get({'courseId': courseId}).$promise.then(
			function (ret)
			{
				$scope.assignments = ret.objects;
				CourseResource.getComparisonCount({'id': courseId}).$promise.then(
					function (ret) {
						var compared = ret.comparisons;
						for (var key in $scope.assignments) {
							assignment = $scope.assignments[key];
							var required = assignment.number_of_comparisons;
							if (!(assignment.id in compared)) {
								compared[assignment.id] = 0;
                            }
							assignment['left'] = compared[assignment.id] <= required ?
								required - compared[assignment.id] : 0;
							// if evaluation period is set answers can be seen after it ends
							if (assignment['compare_end']) {
								assignment['answers_available'] = assignment['after_comparing'];
							// if an evaluation period is NOT set - answers can be seen after req met
							} else {
								assignment['answers_available'] = assignment['after_comparing'] && assignment['left'] < 1;
							}
						}
					},
					function (ret) {
						Toaster.reqerror("Evaluations Not Found", ret)
					}
				);

                CourseResource.getComparisonAvailable({'id': courseId}).$promise.then(
                    function (ret) {
                        var replies = ret.available;
                        for (var key in $scope.assignments) {
                            assignment = $scope.assignments[key];
                            assignment['self_evaluation_left'] = 0;
                            /*
                            Assumptions made:
                            - only one self-evaluation type per assignment
                            - if self-evaluation is required but not one is submitted --> 1 needs to be completed
                            */
                            if (assignment.enable_self_evaluation && !replies[assignment.id]) {
                                assignment['self_evaluation_left'] = 1;
                            }
                        }
                    },
                    function (ret) {
                        Toaster.reqerror("Self-Evaluation records Not Found.", ret);
                    }
                );
			},
			function (ret)
			{
				Toaster.reqerror("Assignments Not Found For Course ID " +
					courseId, ret);
			}
		);
		CourseResource.getAnswered({'id': courseId}).$promise.then(
			function(ret) {
				$scope.answered = ret.answered;
			},
			function (ret) {
				Toaster.reqerror("Answers Not Found", ret);
			}
		);

		$scope.deleteAssignment = function(key, course_id, assignment_id) {
			AssignmentResource.delete({'courseId': course_id, 'assignmentId': assignment_id}).$promise.then(
				function (ret) {
					$scope.assignments.splice(key, 1);
					Toaster.success("Successfully deleted assignment " + ret.id);
				},
				function (ret) {
					Toaster.reqerror("Assignment deletion failed", ret);
				}
			);
		};

		$scope.assignmentFilter = function(filter) {
			return function(assignment) {
				switch(filter) {
					// return all assignments
					case "All course assignments":
						return true;
					// INSTRUCTOR: return all assignments in answer period
					case "Assignments being answered":
						return assignment.answer_period;
					// INSTRUCTOR: return all assignments in comparison period
					case "Assignments being compared":
						return assignment.compare_period;
					// INSTRUCTOR: return all assignments that are unavailable to students at the moment
					case "Upcoming assignments":
						return !assignment.available;
					// STUDENTS: return all assignments that need to be answered or compared
					case "My pending assignments":
						return (assignment.answer_period && !$scope.answered[assignment.id]) ||
							(assignment.compare_period && (assignment.left || assignment.self_evaluation_left));
					default:
						return false;
				}
			}
		}
	}
]);

module.controller(
	'CourseController',
    ['$scope', '$log', '$route', '$routeParams', '$location', 'Session', 'Authorize',
	 'CourseResource', 'Toaster',
	function($scope, $log, $route, $routeParams, $location, Session, Authorize,
            CourseResource, Toaster) {
		var self = this;
        $scope.course = {};
		var messages = {
			new: {title: 'Course Created', msg: 'The course created successfully'},
			edit: {title: 'Course Successfully Updated', msg: 'Your course changes have been saved.'}
		};

		self.edit = function() {
			$scope.courseId = $routeParams['courseId'];
			$scope.course = CourseResource.get({'id':$scope.courseId});
		};

		Session.getUser().then(function(user) {
			$scope.loggedInUserId = user.id;
		});

		$scope.save = function() {
			$scope.submitted = true;
			CourseResource.save({id: $scope.course.id}, $scope.course, function (ret) {
				Toaster.success(messages[$scope.method].title, messages[$scope.method].msg);
				// refresh permissions
				Session.refreshPermissions();
				$location.path('/course/' + ret.id);
			}).$promise.finally(function() {
				$scope.submitted = false;
			});
		};

		//  Calling routeParam method
		if ($route.current !== undefined && $route.current.method !== undefined) {
			$scope.method = $route.current.method;
			if (self.hasOwnProperty($route.current.method)) {
				self[$scope.method]();
			}
		}
	}]
);

// End anonymous function
})();
