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
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"AnswerResource",
	function ($resource, Interceptors)
	{
		var url = '/api/courses/:courseId/questions/:questionId/answers/:answerId';
		var ret = $resource(
			url, {answerId: '@id'},
			{
				'get': {url: url, cache: true},
				'save': {method: 'POST', url: url, interceptor: Interceptors.cache},
				'delete': {method: 'DELETE', url: url, interceptor: Interceptors.cache},
				flagged: {
					method: 'POST', 
					url: '/api/courses/:courseId/questions/:questionId/answers/:answerId/flagged',
					interceptor: Interceptors.cache
				},
				user: {url: '/api/courses/:courseId/questions/:questionId/answers/user'},
				view: {url: '/api/courses/:courseId/questions/:questionId/answers/view', cache: true}
			}
		);
		ret.MODEL = "PostsForAnswers";
		return ret;
	}
);

/***** Controllers *****/
module.controller(
	"AnswerCreateController",
	function ($scope, $log, $location, $routeParams, AnswerResource, ClassListResource,
		QuestionResource, TimerResource, Toaster, Authorize, attachService, Session, $timeout)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		$scope.create = true;

		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();

		var countDown = function() {
			$scope.showCountDown = true;
		};

		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL, $scope.courseId).then(function(canManagePosts){
			$scope.canManagePosts = canManagePosts;
			if ($scope.canManagePosts) {
				// get list of users in the course
				ClassListResource.get({'courseId': $scope.courseId}).$promise.then(
					function (ret) {
						$scope.classlist = ret.objects;
					},
					function (ret) {
						Toaster.reqerror("No Users Found For Course ID "+$scope.courseId, ret);
					}
				);
			}
		});

		$scope.question = {};
		QuestionResource.get({'courseId': $scope.courseId, 'questionId': questionId}).
			$promise.then(
				function (ret)
				{
					$scope.question = ret.question;
					var due_date = new Date(ret.question.answer_end);
					if (!$scope.canManagePosts) {
						TimerResource.get(
							function (ret) {
								var current_time = ret.date;
								var trigger_time = due_date.getTime() - current_time  - 600000; //(10 mins)
								$timeout(countDown, trigger_time);
							},
							function (ret) {
								Toaster.reqerror("Unable to get the current time", ret);
							}
						);
					}
				},
				function (ret)
				{
					Toaster.reqerror("Unable to load question.", ret);
				}
			);

		$scope.answer = {};
		$scope.preventExit = true; //user should be warned before leaving page by default
		Session.getUser().then(function(user) {
			$scope.answer.user = user.id
		});
		$scope.answerSubmit = function () {
			$scope.submitted = true;
			$scope.answer.name = attachService.getName();
			$scope.answer.alias = attachService.getAlias();
			AnswerResource.save({'courseId': $scope.courseId, 'questionId': questionId},
				$scope.answer).$promise.then(
					function (ret)
					{
						$scope.submitted = false;
						Toaster.success("New answer posted!");
						$scope.preventExit = false; //user has saved answer, does not need warning when leaving page
						$location.path('/course/' + $scope.courseId + '/question/' +
							questionId);
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
);

module.controller(
	"AnswerEditController",
	function ($scope, $log, $location, $routeParams, AnswerResource, $timeout,
		QuestionResource, TimerResource, AttachmentResource, attachService, Toaster, Authorize)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		$scope.answerId = $routeParams['answerId'];

		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();
		
		$scope.question = {};
		$scope.answer = {};
		var countDown = function() {
			$scope.showCountDown = true;
		};

		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL, $scope.courseId).then(function(canManagePosts){
			$scope.canManagePosts = canManagePosts;
		});

		$scope.deleteFile = function(post_id, file_id) {
			AttachmentResource.delete({'postId': post_id, 'fileId': file_id}).$promise.then(
				function (ret) {
					Toaster.success('Attachment deleted successfully');
					$scope.answer.uploadedFile = false;
				},
				function (ret) {
					Toaster.reqerror('Attachment deletion failed', ret);
				}
			);
		};

		QuestionResource.get({'courseId': $scope.courseId, 'questionId': questionId}).$promise.then(
			function (ret) {
				$scope.question = ret.question;
				due_date = new Date(ret.question.answer_end);
				if (!$scope.canManagePosts) {
					TimerResource.get(
						function (ret) {
							var current_time = ret.date;
							var trigger_time = due_date.getTime() - current_time  - 600000; //(10 mins)
							$timeout(countDown, trigger_time);
						},
						function (ret) {
							Toaster.reqerror("Unable to get the current time", ret);
						}
					);
				}
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve question "+questionId, ret);
			}
		);
		AnswerResource.get({'courseId': $scope.courseId, 'questionId': questionId, 'answerId': $scope.answerId}).$promise.then(
			function (ret) {
				$scope.answer = ret;
				AttachmentResource.get({'postId': ret.posts_id}).$promise.then(
					function (ret) {
						$scope.answer.uploadedFile = ret.file;
					},
					function (ret) {
						Toaster.reqerror("Unable to retrieve attachment", ret);
					}
				);
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
			}
		);
		$scope.answerSubmit = function () {
			$scope.answer.name = attachService.getName();
			$scope.answer.alias = attachService.getAlias();
			$scope.submitted = true;
			AnswerResource.save({'courseId': $scope.courseId, 'questionId': questionId}, $scope.answer).$promise.then(
				function() {
					$scope.submitted = false;
					Toaster.success("Answer Updated!");
					$location.path('/course/' + $scope.courseId + '/question/' +questionId);
					
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
);

// End anonymous function
})();

