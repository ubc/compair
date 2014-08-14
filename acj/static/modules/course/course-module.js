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
			'getQuestions': {url: '/api/courses/:id/questions'}
		}
	);
	ret.MODEL = "Courses"; // add constant to identify the model
		// being used, this is for permissions checking
		// and should match the server side model name
	return ret;
});

/***** Constants *****/
module.constant('required_rounds', 6);

/***** Controllers *****/
module.controller(
	'CourseConfigureController',
	function($scope, $log, $routeParams, CourseResource, EditorOptions, Toaster)
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
				function() { Toaster.success("Course Information Updated!"); },
				function(ret) { Toaster.reqerror("Course Save Failed.", ret); }
			);
		};
	}
);

module.controller(
	'CourseQuestionsController',
	function($scope, $log, $routeParams, CourseResource, QuestionResource, Authorize, AuthenticationService, required_rounds, Toaster)
	{
		// get course info
		var courseId = $routeParams['courseId'];
		$scope.canCreateQuestions = Authorize.can(Authorize.CREATE, QuestionResource.MODEL);
		$scope.canEditCourse=Authorize.can(Authorize.EDIT, CourseResource.MODEL);
		$scope.loggedInUserId = AuthenticationService.getUser().id;
		$scope.canManagePosts = 
			Authorize.can(Authorize.MANAGE, QuestionResource.MODEL);
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
				var judge = ret.judgements;
				count = {}
				for (id in judge) {
					quesId = judge[id].answerpairing.postsforquestions_id;
					if (!(quesId in count))
						count[quesId] = 0;
					count[quesId]++;
				}

				var required = 0;
				var min_pairs = 0;
				for (key in ret.questions) {
					ques = ret.questions[key];
					min_pairs = ques.answers_count / 2;
					required = ret.count > 0 ? Math.ceil(min_pairs * required_rounds / ret.count) : 0;
					if (!(ques.id in count))
						count[ques.id] = 0;
					ques['left'] = count[ques.id] <= required ?
						required - count[ques.id] : 0;
				}
			},
			function (ret)
			{
				Toaster.reqerror("Unable to retrieve course questions: " +
					courseId, ret);
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
			$log.debug($scope.course);
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
