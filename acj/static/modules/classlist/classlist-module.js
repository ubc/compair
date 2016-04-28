// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.classlist',
	[
		'ngResource',
		'ubc.ctlt.acj.attachment',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.interceptor',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.group',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.user',
		'ui.bootstrap',
		'fileSaver'
	]
);

/***** Providers *****/
module.factory(
	"ClassListResource",
	["$resource", "$cacheFactory", "Interceptors",
	function ($resource, $cacheFactory, Interceptors)
	{
		var url = '/api/courses/:courseId/users/:userId';
		var cache = $cacheFactory('classlist');
		var ret = $resource(
			url, {userId: '@userId'},
			{
				get: {cache: cache},
				enrol: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
				unenrol: {method: 'DELETE', url: url, interceptor: Interceptors.enrolCache},
				export: {
					method: 'GET',
					url: url,
					headers: {Accept: 'text/csv'},
					transformResponse: function (data, headers) {
						// need to wrap response with object, otherwise $resource
						// will try to decode response as json
						return {content: data};
					}
				}
			}
		);
		ret.MODEL = "CoursesAndUsers";
		return ret;
	}
]);

/***** Controllers *****/
module.controller(
	'ClassViewController',
	["$scope", "$log", "$routeParams", "$route", "ClassListResource", "CourseResource",
			 "CourseRoleResource", "GroupResource", "Toaster", "Session", "SaveAs",
	function($scope, $log, $routeParams, $route, ClassListResource, CourseResource,
			 CourseRoleResource, GroupResource, Toaster, Session, SaveAs)
	{
		$scope.course = {};
		$scope.classlist = {};
		var courseId = $routeParams['courseId'];
		$scope.courseId = courseId;
		Session.getUser().then(function(user) {
			$scope.loggedInUserId = user.id;
		});
		CourseResource.get({'id':courseId},
			function (ret) {
				$scope.course_name = ret['name'];
			},
			function (ret) {
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);
		ClassListResource.get({'courseId':courseId},
			function (ret) {
				$scope.classlist = ret.objects;
			},
			function (ret) {
				Toaster.reqerror("No Users Found For Course ID "+courseId, ret);
			}
		);
		GroupResource.get({'courseId':courseId},
			function (ret) {
				$scope.groups = ret.groups;
			},
			function (ret) {
				Toaster.reqerror("Groups Retrieval Failed", ret);
			}
		);

		CourseRoleResource.query(
			function (ret) {
				$scope.roles = ret;
			},
			function (ret) {
				Toaster.reqerror("No Course Roles Found", ret);
			}
		);

		$scope.update = function(userId, groupId) {
			if (groupId) {
				GroupResource.enrol({'courseId': courseId, 'userId': userId, 'groupId': groupId}, {},
					function (ret) {
						Toaster.success("Successfully enroled the user into " + ret.groups_name);
					},
					function (ret) {
						Toaster.reqerror("Failed to enrol the user into the group.", ret);
					}
				);
			} else {
				GroupResource.unenrol({'courseId': courseId, 'userId': userId},
					function (ret) {
						Toaster.success("Successfully removed the user from the group.");
					},
					function (ret) {
						Toaster.reqerror("Failed to remove the user from the group.", ret);
					}
				);
			}
		};

		$scope.enrol = function(user, course_role) {
			var role = {'course_role': course_role};
			ClassListResource.enrol({'courseId': courseId, 'userId': user.id}, role,
				function (ret) {
					Toaster.success("User Added", 'Successfully changed '+ ret.fullname +'\'s course role to ' + ret.course_role);
				},
				function (ret) {
					Toaster.reqerror("User Add Failed For ID " + user.user.id, ret);
				}
			);
		};

		$scope.unenrol = function(userId) {
			ClassListResource.unenrol({'courseId': courseId, 'userId': userId},
				function (ret) {
					Toaster.success("Successfully unenroled " + ret.user.fullname + " from the course.");
					$route.reload();
				},
				function (ret) {
					Toaster.reqerror("Failed to unerol the user from the course.", ret);
				}
			)
		};

		$scope.export = function() {
			ClassListResource.export({'courseId': courseId}, function(ret) {
				SaveAs.download(ret.content, 'classlist_'+$scope.course_name+'.csv', {type: "text/csv;charset=utf-8"});
			});
		};
	}
]);

module.controller(
	'ClassImportController',
	["$scope", "$log", "$location", "$routeParams", "ClassListResource", "CourseResource", "Toaster", "importService",
	function($scope, $log, $location, $routeParams, ClassListResource, CourseResource, Toaster, importService)
	{
		$scope.course = {};
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id':courseId},
			function (ret) {
				$scope.course_name = ret['name'];
			},
			function (ret) {
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);
		$scope.uploader = importService.getUploader(courseId, 'users');
		$scope.uploader.onCompleteItem = function(fileItem, response, status, headers) {
			$scope.submitted = false;
			importService.onComplete(courseId, response);
		};
		$scope.uploader.onErrorItem = importService.onError();

		$scope.upload = function() {
			$scope.submitted = true;
			$scope.uploader.uploadAll();
		};
	}
]);

module.controller(
	'ClassImportResultsController',
	["$scope", "$log", "$routeParams", "ClassListResource", "Toaster", "importService",
	function($scope, $log, $routeParams, ClassListResource, Toaster, importService)
	{
		$scope.results = importService.getResults();

		$scope.course = {};
		$scope.courseId = $routeParams['courseId'];
		$scope.headers = ['Username', 'Student Number', 'First Name', 'Last Name', 'Email', 'Message'];
	}
]);

module.controller(
	'EnrolController',
	["$scope", "$log", "$routeParams", "$route", "$location", "ClassListResource", "Toaster", "UserResource",
	function($scope, $log, $routeParams, $route, $location, ClassListResource, Toaster, UserResource)
	{
		var courseId = $routeParams['courseId'];

		$scope.enrolSubmit = function() {
			$scope.submitted = true;
			ClassListResource.enrol({'courseId': courseId, 'userId': $scope.user.id}, $scope.user,
				function (ret) {
					$scope.submitted = false;
					Toaster.success("User Added", 'Successfully added '+ ret.fullname +' as ' + ret.course_role + ' to the course.');
					$route.reload();
				},
				function (ret) {
					$scope.submitted = false;
					Toaster.reqerror("User Add Failed For ID " + $scope.user.id, ret);
				}
			);
		};

		$scope.getUsersAhead = function(search) {
			// need return a real promise so can't use short form (without $promise.then)
			return UserResource.get({search: search}).$promise.then(function(response) {
				return response.objects;
			});
		}
	}
]);

// End anonymous function
})();
