// Handles answer creation and editing.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.answer', 
	[
		'ngResource',
		'timer',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.interceptor',
		'ubc.ctlt.acj.common.mathjax',
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
	function ($scope, $log, $location, $routeParams, AnswerResource, 
		QuestionResource, Toaster, Authorize, attachService, $interval)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];

		var due_date = null;
		var timer = undefined;
		var date = new Date();

		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();

		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL, $scope.courseId).then(function(canManagePosts){
			$scope.canManagePosts = canManagePosts;
		});
		// check how close we are to the deadline
		var checkTime = function() {
			date = new Date();
			$scope.showCountDown = due_date.getTime() - date.getTime() <= 300000;    // 5 minutes
			// stop checking time once the timer starts appearing
			if ($scope.showCountDown) {
				stopTimer();
			}
		};
		// cancel the countdown timer
		var stopTimer = function() {
			if (angular.isDefined(timer)) {
				$interval.cancel(timer);
				timer = undefined;
			}
		};
		// listen to the user leaving the page
		$scope.$on('$destroy', stopTimer);

		$scope.question = {};
		QuestionResource.get({'courseId': $scope.courseId, 'questionId': questionId}).
			$promise.then(
				function (ret)
				{
					$scope.question = ret.question;
					due_date = new Date(ret.question.answer_end);
					if (!$scope.canManagePosts) {
						timer = $interval(checkTime, 1000);
					}
				},
				function (ret)
				{
					Toaster.reqerror("Unable to load question.", ret);
				}
			);

		$scope.answer = {};
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
	function ($scope, $log, $location, $routeParams, AnswerResource, $interval,
		QuestionResource, AttachmentResource, attachService, Toaster, Authorize)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		$scope.answerId = $routeParams['answerId'];

		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();
		
		$scope.question = {};
		$scope.answer = {};
		var due_date = null;
		var timer = null;
		var date = new Date();

		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL, $scope.courseId).then(function(canManagePosts){
			$scope.canManagePosts = canManagePosts;
		});
		// check how close we are to the deadline
		var checkTime  = function() {
			date = new Date();
			$scope.showCountDown = due_date.getTime()- date.getTime() <= 300000;    // 5 minutes
			if ($scope.showCountDown) {
				stopTimer();
			}
		};
		// cancel the countdown timer
		var stopTimer = function() {
			if (angular.isDefined(timer)) {
				$interval.cancel(timer);
				timer = null;
			}
		};
		// listen to the user leaving the page
		$scope.$on('$destroy', stopTimer);

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
					timer = $interval(checkTime, 1000);
				}
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve question "+questionId, ret);
			}
		);
		AnswerResource.get({'courseId': $scope.courseId, 'questionId': questionId, 'answerId': $scope.answerId}).$promise.then(
			function (ret) {
				$scope.answer = ret;
				AttachmentResource.get({'postId': ret.post.id}).$promise.then(
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

