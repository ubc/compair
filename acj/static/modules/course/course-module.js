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
		'ubc.ctlt.acj.criteria',
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
			'getAnswered': {url: '/api/courses/:id/answers/answered'},
			'getInstructors': {url: '/api/courses/:id/users/instructors'},
			'getAnswerCount': {url: '/api/courses/:id/answers/count'}
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
	function($scope, $log, $routeParams, $location, CourseResource, CriteriaResource, CoursesCriteriaResource, EditorOptions, Authorize, Session, Toaster)
	{
		$scope.editorOptions = EditorOptions.basic;
		// get course info
		$scope.course = {};
		$scope.criterion = {};
		$scope.courseId = $routeParams['courseId'];
		Authorize.can(Authorize.MANAGE, CoursesCriteriaResource.MODEL).then(function(result) {
			$scope.canManageCriteriaCourses = result;
		});
		Session.getUser().then(function(user) {
		    $scope.loggedInUserId = user.id;
		});
		CourseResource.get({'id':$scope.courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve course: "+ $scope.courseId, ret);
			}
		);
		CoursesCriteriaResource.get({'courseId': $scope.courseId}).$promise.then(
			function (ret) {
				$scope.criteria = ret.objects;
				var inCourse = {};
				angular.forEach($scope.criteria, function(c, key) {
					inCourse[c.criterion.id] = 1;
				});
				CriteriaResource.get().$promise.then(
					function (ret) {
						$scope.availableCriteria = ret.criteria.filter(
							function(c) {
								return !(c.id in inCourse);
							}
						);
					},
					function (ret) {
						Toaster.reqerror("Unable to retrieve available criteria.", ret);
					}
				);
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve this course's criteria", ret);
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
		// save new criterion
		$scope.criterionSubmit = function() {
			$scope.criterionSubmitted = true;
			CoursesCriteriaResource.save({'courseId': $scope.courseId}, $scope.criterion).$promise.then(
				function (ret) {
					$scope.criterion = {'name': '', 'description': ''}; // reset form
					$scope.criterionSubmitted = false;
					$scope.criteria.push(ret.criterion);
					Toaster.success("Successfully added a new criterion.");
				},
				function (ret) {
					$scope.criterionSubmitted = false;
					Toaster.reqerror("Unable to create a new criterion.", ret);
				}
			);
		};
		$scope.add = function(key) {
			// not proceed if empty option is being added
			if (!key)
				return;
			var criterionId = $scope.availableCriteria[key].id;
			CoursesCriteriaResource.save({'courseId': $scope.courseId, 'criteriaId': criterionId}, {}).$promise.then(
				function (ret) {
					$scope.availableCriteria.splice(key, 1);
					$scope.criteria.push(ret.criterion);
				},
				function (ret) {
					Toaster.reqerror("Unable to add the criterion to the course", ret);
				}
			);
		}
		// remove criterion from course - eg. make it inactive
		$scope.remove = function(key) {
			var criterionId = $scope.criteria[key].criterion.id;
			CoursesCriteriaResource.delete({'courseId': $scope.courseId, 'criteriaId': criterionId}).$promise.then(
				function (ret) {
					$scope.availableCriteria.push($scope.criteria[key].criterion);
					$scope.criteria.splice(key, 1);
				},
				function (ret) {
					Toaster.reqerror("Unable to remove criterion " + ret.criterionId, ret);
				}
			);
		}
	}
);

module.controller(
	'CourseQuestionsController',
	function($scope, $log, $routeParams, CourseResource, QuestionResource, Authorize,
			 AuthenticationService, required_rounds, Toaster)
	{
		// get course info
		var courseId = $scope.courseId = $routeParams['courseId'];
		$scope.answered = {};
		$scope.count = {};
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
						for (key in $scope.questions) {
							ques = $scope.questions[key];
							var required = ques.num_judgement_req;
							if (!(ques.id in judged))
								judged[ques.id] = 0;
							ques['left'] = judged[ques.id] <= required ?
								required - judged[ques.id] : 0;
							var answered = ques.id in $scope.answered ? $scope.answered[ques.id] : 0;
							var count = ques.id in $scope.count ? $scope.count[ques.id] : 0;
							var diff = count - answered;
							ques['eval_left'] = ((diff * (diff - 1)) / 2);
							ques['warning'] = (required - judged[ques.id]) <= ques['eval_left'];
							ques['leftover'] = ques['left'] - ques['eval_left'];
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
				Toaster.reqerror("Unable to retrieve your answer history.", ret);
			}
		);
		CourseResource.getAnswerCount({'id': courseId}).$promise.then(
			function (ret) {
				$scope.count = ret.count;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the answer counts for the questions.", ret);
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
