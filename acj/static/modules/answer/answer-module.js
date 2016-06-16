// Handles answer creation and editing.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.answer',
	[
		'ngResource',
		'timer',
		'ubc.ctlt.acj.classlist',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.interceptor',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.common.timer',
		'ubc.ctlt.acj.assignment',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory("AnswerResource", ['$resource', '$cacheFactory', function ($resource, $cacheFactory) {
		var url = '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId';
		// keep a list of answer list query URLs so that we can invalidate caches for those later
		var listCacheKeys = [];
		var cache = $cacheFactory.get('$http');

		function invalidListCache(url) {
			// remove list caches. As list query may contain pagination and query parameters
			// we have to invalidate all.
			_.forEach(listCacheKeys, function(key, index, keys) {
				if (url == undefined || _.startsWith(key, url)) {
					cache.remove(key);
					keys.splice(index, 1);
				}
			});
		}

		var cacheInterceptor = {
			response: function(response) {
				cache.remove(response.config.url);	// remove cached GET response
				// removing the suffix of some of the actions - eg. flagged
				var url = response.config.url.replace(/\/(flagged)/g, "");
				cache.remove(url);
				url = url.replace(/\/\d+$/g, "");

				invalidListCache(url);

				return response.data;
			}
		};
		// this function is copied from angular $http to build request URL
		function buildUrl(url, serializedParams) {
			if (serializedParams.length > 0) {
				url += ((url.indexOf('?') == -1) ? '?' : '&') + serializedParams;
			}
			return url;
		}

		// store answer list query URLs
		var cacheKeyInterceptor = {
			response: function(response) {
				var url = buildUrl(response.config.url, response.config.paramSerializer(response.config.params));
				if (url.match(/\/api\/courses\/\d+\/assignments\/\d+\/answers\?.*/)) {
					listCacheKeys.push(url);
				}

				return response.data;
			}
		};

		var ret = $resource(
			url, {answerId: '@id'},
			{
				get: {url: url, cache: true, interceptor: cacheKeyInterceptor},
				save: {method: 'POST', url: url, interceptor: cacheInterceptor},
				delete: {method: 'DELETE', url: url, interceptor: cacheInterceptor},
				flagged: {
					method: 'POST',
					url: '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId/flagged',
					interceptor: cacheInterceptor
				},
                comparisons: {url: '/api/courses/:courseId/assignments/:assignmentId/answers/comparisons'},
				user: {url: '/api/courses/:courseId/assignments/:assignmentId/answers/user'}
			}
		);
		ret.MODEL = "Answer";
		ret.invalidListCache = invalidListCache;
		return ret;
	}]
);

/***** Controllers *****/
module.controller(
	"AnswerCreateController",
	["$scope", "$log", "$location", "$routeParams", "AnswerResource", "ClassListResource",
		"AssignmentResource", "TimerResource", "Toaster", "Authorize", "attachService", "Session", "$timeout",
	function ($scope, $log, $location, $routeParams, AnswerResource, ClassListResource,
		AssignmentResource, TimerResource, Toaster, Authorize, attachService, Session, $timeout)
	{
		$scope.courseId = $routeParams['courseId'];
		var assignmentId = $routeParams['assignmentId'];
		$scope.create = true;

		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();

		var countDown = function() {
			$scope.showCountDown = true;
		};

		Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId).then(function(canManageAssignment){
			$scope.canManageAssignment = canManageAssignment;
			if ($scope.canManageAssignment) {
				// get list of users in the course
				ClassListResource.get({'courseId': $scope.courseId}).$promise.then(
					function (ret) {
						$scope.classlist = ret.objects;
					},
					function (ret) {
						Toaster.reqerror("No Users Found For Course ID "+$scope.courseId, ret);
					}
				);
                Session.getUser().then(function(user) {
                    $scope.answer.user_id = user.id
                });
			}
		});

		$scope.assignment = {};
		AssignmentResource.get({'courseId': $scope.courseId, 'assignmentId': assignmentId}).
			$promise.then(
				function (ret)
				{
					$scope.assignment = ret;
					var due_date = new Date($scope.assignment.answer_end);
					if (!$scope.canManageAssignment) {
						TimerResource.get(
							function (ret) {
								var current_time = ret.date;
								var trigger_time = due_date.getTime() - current_time  - 600000; //(10 mins)
								if (trigger_time < 86400000) { //(1 day)
									$timeout(countDown, trigger_time);
								}
							},
							function (ret) {
								Toaster.reqerror("Unable to get the current time", ret);
							}
						);
					}
				},
				function (ret)
				{
					Toaster.reqerror("Unable to load assignment.", ret);
				}
			);

		$scope.answer = {};
		$scope.preventExit = true; //user should be warned before leaving page by default
		$scope.answerSubmit = function () {
			$scope.submitted = true;
			$scope.answer.file_name = attachService.getName();
			$scope.answer.file_alias = attachService.getAlias();
			AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': assignmentId},
				$scope.answer).$promise.then(
					function (ret)
					{
						$scope.submitted = false;
						Toaster.success("New answer posted!");
						$scope.preventExit = false; //user has saved answer, does not need warning when leaving page
						$location.path('/course/' + $scope.courseId + '/assignment/' +
							assignmentId);
					},
					function (ret)
					{
						$scope.submitted = false;
						// if answer period is not in session
						if (ret.status == '403' && 'error' in ret.data) {
							Toaster.error(ret.data.error);
						} else {
							Toaster.reqerror("Answer Save Failed.", ret);
						}
					}
				);
		};
	}
]);

module.controller(
	"AnswerEditController",
	["$scope", "$log", "$location", "$routeParams", "AnswerResource", "$timeout",
		"AssignmentResource", "TimerResource", "AttachmentResource", "attachService", "Toaster", "Authorize",
	function ($scope, $log, $location, $routeParams, AnswerResource, $timeout,
		AssignmentResource, TimerResource, AttachmentResource, attachService, Toaster, Authorize)
	{
		$scope.courseId = $routeParams['courseId'];
		var assignmentId = $routeParams['assignmentId'];
		$scope.answerId = $routeParams['answerId'];

		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();

		$scope.assignment = {};
		$scope.answer = {};
		var countDown = function() {
			$scope.showCountDown = true;
		};

		Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId).then(function(canManageAssignment){
			$scope.canManageAssignment = canManageAssignment;
		});

		$scope.deleteFile = function(file_id) {
			AttachmentResource.delete({'fileId': file_id}).$promise.then(
				function (ret) {
					Toaster.success('Attachment deleted successfully');
					$scope.answer.uploadedFile = false;
				},
				function (ret) {
					Toaster.reqerror('Attachment deletion failed', ret);
				}
			);
		};

		AssignmentResource.get({'courseId': $scope.courseId, 'assignmentId': assignmentId}).$promise.then(
			function (ret) {
				$scope.assignment = ret;
				due_date = new Date($scope.assignment.answer_end);
				if (!$scope.canManageAssignment) {
					TimerResource.get(
						function (ret) {
							var current_time = ret.date;
							var trigger_time = due_date.getTime() - current_time  - 600000; //(10 mins)
							if (trigger_time < 86400000) { //(1 day)
								$timeout(countDown, trigger_time);
							}
						},
						function (ret) {
							Toaster.reqerror("Unable to get the current time", ret);
						}
					);
				}
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve assignment "+assignmentId, ret);
			}
		);
		AnswerResource.get({'courseId': $scope.courseId, 'assignmentId': assignmentId, 'answerId': $scope.answerId}).$promise.then(
			function (ret) {
				$scope.answer = ret;

                if (ret.file) {
                    AttachmentResource.get({'fileId': ret.file.id}).$promise.then(
                        function (ret) {
                            $scope.answer.uploadedFile = ret.file;
                        },
                        function (ret) {
                            Toaster.reqerror("Unable to retrieve attachment", ret);
                        }
                    );
                }
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);
		$scope.answerSubmit = function () {
			$scope.answer.file_name = attachService.getName();
			$scope.answer.file_alias = attachService.getAlias();
			$scope.submitted = true;
			AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': assignmentId}, $scope.answer).$promise.then(
				function() {
					$scope.submitted = false;
					Toaster.success("Answer Updated!");
					$location.path('/course/' + $scope.courseId + '/assignment/' +assignmentId);

				},
				function(ret) {
					$scope.submitted = false;
					// if answer period is not in session
					if (ret.status == '403' && 'error' in ret.data) {
						Toaster.error(ret.data.error);
					} else {
						Toaster.reqerror("Answer Save Failed.", ret);
					}
				}
			);
		};
	}
]);

// End anonymous function
})();

