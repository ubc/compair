// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.course',
	[
		'angularMoment',
		'ngResource',
		'ngRoute',
		'ckeditor',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.judgement',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory('CourseResource', function($q, $routeParams, $log, $resource)
{
	var ret = $resource('/api/courses/:id', {id: '@id'},
		{
			// would enable caching for GET but there's no automatic cache
			// invalidation, I don't want to deal with that manually
			'getQuestions': {url: '/api/courses/:id/questions'},
			'getJudgementCount': {url: '/api/courses/:id/judgements/count'},
			'getAnswered': {url: '/api/courses/:id/answers/count'},
			'getInstructors': {url: '/api/courses/:id/users/instructors'}
		}
	);
	ret.MODEL = "Courses"; // add constant to identify the model
		// being used, this is for permissions checking
		// and should match the server side model name
	return ret;
});

/***** Controllers *****/
module.controller(
	'CourseConfigureController',
	function($scope, $log, $routeParams, $location, CourseResource, EditorOptions, Toaster)
	{
		$scope.editorOptions = EditorOptions.basic;
		// get course info
		$scope.course = {};
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve course: "+ courseId, ret);
			}
		);
		// save course info
		$scope.courseSubmit = function() {
			CourseResource.save($scope.course).$promise.then(
				function(ret) {
					Toaster.success("Course Information Updated!");
					$location.path('/course/' + ret.id);
				},
				function(ret) { Toaster.reqerror("Course Save Failed.", ret); }
			);
		};
	}
);

module.controller(
	'CourseQuestionsController',
	function($scope, $log, $routeParams, CourseResource, QuestionResource, Authorize,
			 AuthenticationService, required_rounds, Toaster)
	{
		// get course info
		var courseId = $scope.courseId = $routeParams['courseId'];
		Authorize.can(Authorize.CREATE, QuestionResource.MODEL).then(function(result) {
				$scope.canCreateQuestions = result;
		});
		Authorize.can(Authorize.EDIT, CourseResource.MODEL).then(function(result) {
				$scope.canEditCourse = result;
		});
		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL).then(function(result) {
				$scope.canManagePosts = result;
		});
		CourseResource.get({'id': courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve course: "+ courseId, ret);
			}
		);
		// get course questions
		CourseResource.getQuestions({'id': courseId}).$promise.then(
			function (ret)
			{
				$scope.questions = ret.questions;
				CourseResource.getJudgementCount({'id': courseId}).$promise.then(
					function (ret) {
						var judged = ret.judgements;
						var required = 0;
						for (key in $scope.questions) {
							ques = $scope.questions[key];
							required = ques.num_judgement_req;
							if (!(ques.id in judged))
								judged[ques.id] = 0;
							ques['left'] = judged[ques.id] <= required ?
								required - judged[ques.id] : 0;
						}
					},
					function (ret) {
						Toaster.reqerror("Unable to retrieve your judgement counts.", ret)
					}
				);
			},
			function (ret)
			{
				Toaster.reqerror("Unable to retrieve course questions: " +
					courseId, ret);
			}
		);
		CourseResource.getAnswered({'id': courseId}).$promise.then(
			function(ret) {
				$scope.answered = ret.answered;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve your answer history.", ret)
			}
		);
	}
);

module.controller(
	'CourseCreateController',
	function($scope, $log, $location, CourseResource, EditorOptions, Toaster)
	{
		$scope.editorOptions = EditorOptions.basic;
		//initialize course so this scope can access data from included form
		$scope.course = {};
		$scope.courseSubmit = function() {
			$scope.submitted = true;
			CourseResource.save($scope.course).$promise.then(
				function (ret)
				{
					$scope.submitted = false;
					Toaster.success(ret.name + " created successfully!");
					$location.path('/course/' + ret.id);
				},
				function (ret)
				{
					$scope.submitted = false;
					Toaster.reqerror("Create course failed.", ret);
				}
			);
		};
	}
);

// End anonymous function
})();
