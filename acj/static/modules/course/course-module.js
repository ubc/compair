// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.course',
	[
		'angularMoment',
		'ngResource',
		'ngRoute',
		'ckeditor',
		'ubc.ctlt.acj.comment',
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
			'getInstructorsLabels': {url: '/api/courses/:id/users/instructors/labels'},
			'getInstructors': {url: '/api/courses/:id/users/instructors'},
			'getStudents': {url: '/api/courses/:id/users/students'}
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
		$scope.criterion = {'default': true};	// initialize default attribute to true
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
				Toaster.reqerror("Course Not Found For ID "+ $scope.courseId, ret);
			}
		);
		CoursesCriteriaResource.get({'courseId': $scope.courseId}).$promise.then(
			function (ret) {
				$scope.criteria = ret.objects;
				var inCourse = {};
				$scope.availableCriteria = [];
				angular.forEach($scope.criteria, function(c, key) {
					inCourse[c.criterion.id] = 1;
				});
				CriteriaResource.get().$promise.then(
					function (ret) {
						for (key in ret.criteria) {
							c = ret.criteria[key];
							if (!(c.id in inCourse)) {
								$scope.availableCriteria.push(c);
							}
						}
					},
					function (ret) {
						Toaster.reqerror("Default Criteria Not Found", ret);
					}
				);
			},
			function (ret) {
				Toaster.reqerror("Criteria Not Found", ret);
			}
		);
		// save course info
		$scope.courseSubmit = function() {
			CourseResource.save($scope.course).$promise.then(
				function(ret) {
					Toaster.success("Course Successfully Updated", "Your course changes have been saved.");
					$location.path('/course/' + ret.id);
				},
				function(ret) { Toaster.reqerror("Course Update Failed", ret); }
			);
		};
		// save new criterion
		$scope.criterionSubmit = function() {
			$scope.criterionSubmitted = true;
			CoursesCriteriaResource.save({'courseId': $scope.courseId}, $scope.criterion).$promise.then(
				function (ret) {
					$scope.criterion = {'name': '', 'description': '', 'default': true}; // reset form
					$scope.criterionSubmitted = false;
					$scope.criteria.push(ret.criterion);
					Toaster.success("New Criterion Created", "Successfully added a new criterion.");
					$scope.toggleForm();
					$(".fa-chevron-right").removeClass("ng-hide"); // reset classes so UI matches current state
					$(".fa-chevron-down").addClass("ng-hide");
				},
				function (ret) {
					$scope.criterionSubmitted = false;
					Toaster.reqerror("No New Criterion Created", ret);
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
					Toaster.reqerror("Unable To Add Criterion", ret);
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
					if (ret.status == '403') {
						Toaster.error(ret.data.error);
					} else {
						Toaster.reqerror("Unable To Remove Criterion " + ret.criterionId, ret);
					}
				}
			);
		}

		$scope.toggleForm = function() {
			$scope.isCreateFormShown = !$scope.isCreateFormShown;
		}
	}
);

module.controller(
	'CourseQuestionsController',
	function($scope, $log, $routeParams, CourseResource, QuestionResource, Authorize,
			 AnswerCommentResource, AuthenticationService, required_rounds, Toaster)
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
				Toaster.reqerror("Course Not Found For ID "+ courseId, ret);
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
							/// number of evaluations available
							ques['eval_left'] = ((diff * (diff - 1)) / 2);
							ques['warning'] = (required - judged[ques.id]) > ques['eval_left'];
							// number of evaluations left to complete minus number of available
							ques['leftover'] = ques['left'] - ques['eval_left'];
						}
					},
					function (ret) {
						Toaster.reqerror("Evaluations Not Found", ret)
					}
				);
				AnswerCommentResource.allSelfEval({'courseId': courseId}).$promise.then(
					function (ret) {
						var replies = ret.replies;
						for (key in $scope.questions) {
							ques = $scope.questions[key];
							ques['selfeval_left'] = 0;
							/*
							Assumptions made:
							- only one self-evaluation type per question
							- if self-eval is required but not one is submitted --> 1 needs to be completed
							 */
							if (ques.selfevaltype_id && !replies[ques.id]) {
								ques['selfeval_left'] = 1;
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
				Toaster.reqerror("Questions Not Found For Course ID " +
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

		$scope.deleteQuestion = function(key, course_id, question_id) {
			QuestionResource.delete({'courseId': course_id, 'questionId': question_id}).$promise.then(
				function (ret) {
					$scope.questions.splice(key, 1);
					Toaster.success("Successfully deleted question " + ret.id);
				},
				function (ret) {
					Toaster.reqerror("Question deletion failed", ret);
				}
			);
		};
	}
);

module.controller(
	'CourseCreateController',
	function($scope, $log, $location, Session, CourseResource, CriteriaResource, CoursesCriteriaResource,
			 EditorOptions, Toaster)
	{
		$scope.editorOptions = EditorOptions.basic;
		//initialize course so this scope can access data from included form
		$scope.course = {};
		$scope.criteria = [];
		$scope.criterion = {'default': true};	// initialize default attribute to true
		var def = {};

		// initialize default criterion
		CriteriaResource.getDefault().$promise.then(
			function (ret) {
				def = ret;
				$scope.criteria.push({'criterion': def});
			},
			function (ret) {}
		);
		CriteriaResource.get().$promise.then(
			function (ret) {
				// remove default criterion
				for (key in ret.criteria) {
					c = ret.criteria[key];
					if (c.id == def.id) {
						ret.criteria.splice(key, 1);
						break;
					}
				}
				$scope.availableCriteria = ret.criteria;
			},
			function (ret) {
				Toaster.reqerror("Default Criteria Not Found", ret);
			}
		);
		$scope.courseSubmit = function() {
			$scope.submitted = true;
			CourseResource.save($scope.course).$promise.then(
				function (ret)
				{
					Session.refresh().then(function(){
						addMultipleCriteria(ret.id, $scope.criteria);
						$scope.submitted = false;
						Toaster.success("Course Created", ret.name + " created successfully.");
						$location.path('/course/' + ret.id);
					});
				},
				function (ret)
				{
					$scope.submitted = false;
					Toaster.reqerror("No Course Created", ret);
				}
			);
		};

		// add new criterion to tobeAdded
		$scope.criterionSubmit = function() {
			$scope.criterionSubmitted = true;
			CriteriaResource.save({}, $scope.criterion).$promise.then(
				function (ret) {
					$scope.criterion = {'name': '', 'description': '', 'default': true}; // reset form
					$scope.criterionSubmitted = false;
					$scope.criteria.push({'criterion': ret});
					$scope.toggleForm();
					$(".fa-chevron-right").removeClass("ng-hide"); // reset classes so UI matches current state
					$(".fa-chevron-down").addClass("ng-hide");
				},
				function (ret) {
					$scope.criterionSubmitted = false;
					Toaster.reqerror("No New Criterion Created", ret);
				}
			);
		};

		$scope.add = function(key) {
			// not proceed if empty option is being added
			if (!key)
				return;
			$scope.criteria.push({'criterion': $scope.availableCriteria[key]});
			$scope.availableCriteria.splice(key, 1);
		};
		// remove criterion from course - eg. make it inactive
		$scope.remove = function(key) {
			var criterion = $scope.criteria[key].criterion;
			$scope.criteria.splice(key, 1);
			$scope.availableCriteria.push(criterion);
		};

		$scope.toggleForm = function() {
			$scope.isCreateFormShown = !$scope.isCreateFormShown;
		};

		var addMultipleCriteria = function(courseId, criteria) {
			angular.forEach(criteria, function(c, key) {
				CoursesCriteriaResource.save({'courseId': courseId, 'criteriaId': c.criterion.id}, {}).$promise.then(
					function (ret) {},
					function (ret) {
						Toaster.reqerror("Failed to put criterion "+ c.id+" into the course.", ret);
					}
				);
			});
		}
	}
);

// End anonymous function
})();
