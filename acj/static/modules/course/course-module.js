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
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.judgement',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory('CourseResource', function($q, $routeParams, $log, $resource, Interceptors)
{
	var url = '/api/courses/:id';
	var ret = $resource('/api/courses/:id', {id: '@id'},
		{
			// would enable caching for GET but there's no automatic cache
			// invalidation, I don't want to deal with that manually
			'get': {url: url, cache: true},
			'save': {method: 'POST', url: url, interceptor: Interceptors.cache},
			'delete': {method: 'DELETE', url: url, interceptor: Interceptors.cache},
			'getJudgementCount': {url: '/api/courses/:id/judgements/count'},
			'getAvailPairLogic': {url: '/api/courses/:id/judgements/availpair'},
			'getAnswered': {url: '/api/courses/:id/answers/answered'},
			'getInstructorsLabels': {url: '/api/courses/:id/users/instructors/labels'},
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
	'CourseQuestionsController',
	function($scope, $log, $routeParams, CourseResource, QuestionResource, Authorize,
			 AnswerCommentResource, AuthenticationService, required_rounds, Toaster)
	{
		// get course info
		var courseId = $scope.courseId = $routeParams['courseId'];
		$scope.answered = {};
		$scope.count = {};
		$scope.filters = [];
		Authorize.can(Authorize.CREATE, QuestionResource.MODEL, courseId).then(function(result) {
				$scope.canCreateQuestions = result;
		});
		Authorize.can(Authorize.EDIT, CourseResource.MODEL, courseId).then(function(result) {
				$scope.canEditCourse = result;
		});
		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL, courseId).then(function(result) {
				$scope.canManagePosts = result;
				$scope.filters.push('All course assignments');
				if ($scope.canManagePosts) {
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

		CourseResource.getAvailPairLogic({'id': courseId}).$promise.then(
			function (ret) {
				$scope.availPairsLogic = ret.availPairsLogic;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the answer pairs availablilty.", ret);
			}
		);

		// get course questions
		QuestionResource.get({'courseId': courseId}).$promise.then(
			function (ret)
			{
				$scope.questions = ret.questions;
				CourseResource.getJudgementCount({'id': courseId}).$promise.then(
					function (ret) {
						var judged = ret.judgements;
						for (var key in $scope.questions) {
							ques = $scope.questions[key];
							var required = ques.num_judgement_req;
							if (!(ques.id in judged))
								judged[ques.id] = 0;
							ques['left'] = judged[ques.id] <= required ?
								required - judged[ques.id] : 0;
							var answered = ques.id in $scope.answered ? $scope.answered[ques.id] : 0;
							var count = ques.answers_count;
							var diff = count - answered;
							/// number of evaluations available
							ques['eval_left'] = ((diff * (diff - 1)) / 2);
							ques['warning'] = (required - judged[ques.id]) > ques['eval_left'];
							// number of evaluations left to complete minus number of available
							ques['leftover'] = ques['left'] - ques['eval_left'];
							// if evaluation period is set answers can be seen after it ends
							if (ques['judge_end']) {
								ques['answers_available'] = ques['after_judging'];
							// if an evaluation period is NOT set - answers can be seen after req met
							} else {
								ques['answers_available'] = ques['after_judging'] && ques['left'] < 1;
							}
						}
					},
					function (ret) {
						Toaster.reqerror("Evaluations Not Found", ret)
					}
				);
				AnswerCommentResource.allSelfEval({'courseId': courseId}).$promise.then(
					function (ret) {
						var replies = ret.replies;
						for (var key in $scope.questions) {
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

		$scope.questionFilter = function(filter) {
			return function(question) {
				switch(filter) {
					// return all questions
					case "All course assignments":
						return true;
					// INSTRUCTOR: return all questions in answer period
					case "Assignments being answered":
						return question.answer_period;
					// INSTRUCTOR: return all questions in comparison period
					case "Assignments being compared":
						return question.judging_period;
					// INSTRUCTOR: return all questions that are unavailable to students at the moment
					case "Upcoming assignments":
						return !question.available;
					// STUDENTS: return all questions that need to be answered or compared
					case "My pending assignments":
						return (question.answer_period && !$scope.answered[question.id]) ||
							(question.judging_period && (question.left || question.selfeval_left));
					default:
						return false;
				}
			}
		}
	}
);

module.controller(
	'CourseController', ['$scope', '$log', '$route', '$routeParams', '$location', 'Session', 'Authorize',
		'CourseResource', 'CriteriaResource', 'CoursesCriteriaResource', '$modal', 'Toaster',
	function($scope, $log, $route, $routeParams, $location, Session, Authorize, CourseResource, CriteriaResource,
			 CoursesCriteriaResource, $modal, Toaster) {
		var self = this;
		var messages = {
			new: {title: 'Course Created', msg: 'The course created successfully'},
			edit: {title: 'Course Successfully Updated', msg: 'Your course changes have been saved.'}
		};
		//initialize course so this scope can access data from included form
		$scope.course = {criteria: []};
		$scope.availableCriteria = [];

		self.removeCourseCriteria = function() {
			$scope.availableCriteria = _.filter($scope.availableCriteria, function(c) {
				return !_($scope.course.criteria).pluck('id').includes(c.id);
			});
		};
		self.edit = function() {
			$scope.courseId = $routeParams['courseId'];
			$scope.course = CourseResource.get({'id':$scope.courseId}, function() {
				CoursesCriteriaResource.get({courseId: $scope.course.id}, function(ret) {
					$scope.course.criteria	= ret.objects;
					if ($scope.availableCriteria.length) {
						self.removeCourseCriteria();
					}
				});
			});
		};

		Authorize.can(Authorize.MANAGE, CoursesCriteriaResource.MODEL).then(function(result) {
			$scope.canManageCriteriaCourses = result;
		});

		Session.getUser().then(function(user) {
			$scope.loggedInUserId = user.id;
		});

		CriteriaResource.get().$promise.then(function (ret) {
			$scope.availableCriteria = ret.criteria;
			if ($scope.course.criteria && !$scope.course.criteria.length) {
				// if we don't have any criterion, e.g. new course, add a default one automatically
				$scope.course.criteria.push(_.find($scope.availableCriteria, {id: 1}));
			}

			// we need to remove the existing course criteria from available list
			self.removeCourseCriteria();
		});

		$scope.save = function() {
			$scope.submitted = true;
			CourseResource.save({id: $scope.course.id}, $scope.course, function (ret) {
				Toaster.success(messages[$scope.method].title, messages[$scope.method].msg);
				// refresh permissions
				Session.refresh();
				$location.path('/course/' + ret.id);
			}).$promise.finally(function() {
				$scope.submitted = false;
			});
		};

		$scope.add = function(key) {
			// not proceed if empty option is being added
			if (key === undefined || key === null || key < 0 || key >= $scope.availableCriteria.length)
				return;
			$scope.course.criteria.push($scope.availableCriteria[key]);
			$scope.availableCriteria.splice(key, 1);
		};
		// remove criterion from course - eg. make it inactive
		$scope.remove = function(key) {
			var criterion = $scope.course.criteria[key];
			$scope.course.criteria.splice(key, 1);
			if (criterion.default == true) {
				$scope.availableCriteria.push(criterion);
			}
		};

		$scope.changeCriterion = function(criterion) {
			var modalScope = $scope.$new();
			modalScope.criterion = angular.copy(criterion);
			var modalInstance;
			var criteriaUpdateListener = $scope.$on('CRITERIA_UPDATED', function(event, c) {
				angular.copy(c.criterion, criterion);
				modalInstance.close();
			});
			var criteriaAddListener = $scope.$on('CRITERIA_ADDED', function(event, criteria) {
				$scope.course.criteria.push(criteria);
				modalInstance.close();
			});
			var criteriaCancelListener = $scope.$on('CRITERIA_CANCEL', function() {
				modalInstance.dismiss('cancel');
			});
			modalInstance = $modal.open({
				animation: true,
				template: '<criteria-form criterion=criterion></criteria-form>',
				scope: modalScope
			});
			// we need to remove the listener, otherwise on multiple click, multiple listeners will be registered
			modalInstance.result.finally(function(){
				criteriaUpdateListener();
				criteriaAddListener();
				criteriaCancelListener();
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
