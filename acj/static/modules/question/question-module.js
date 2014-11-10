// Provides the services and controllers for questions.
//
(function() {

var module = angular.module('ubc.ctlt.acj.question',
	[
		'angularFileUpload',
		'ngResource',
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.authentication',
		'ubc.ctlt.acj.authorization',
		'ubc.ctlt.acj.comment',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.group',
		'ubc.ctlt.acj.judgement',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.session'
	]
);

/***** Directives *****/
module.directive(
	'confirmationNeeded',
	function () {
		return {
			priority: -100, //need negative priority to override ng-click
			restrict: 'A',
			link: function(scope, element, attrs){
				var msg = attrs.keyword ? " "+attrs.keyword : "";
				msg = "Are you sure you want to remove this"+msg+"?";
				element.bind('click', function(e) {
					if ( window.confirm(msg) ) {
						scope.$eval(attrs.confirmationNeeded);
						scope.$apply();
					} else {
						e.stopImmediatePropagation();
					}
				});
			}
		}
	}
);

module.directive(
	'getHeight',
	function($timeout) {
		return {
			restrict: 'A',
			link: function(scope, element) {
				// timeout creates delay letting text, images load into the div (answer content)
				$timeout(function(){
					// find the element's scrollHeight (this tells us the full height regardless of max-height set)
					scope.thisHeight = element.prop('scrollHeight');
					// when this full height is outside the max-height, display the read more button to the user
					if (scope.thisHeight > 200) {
						scope.showReadMore = true;
					}
				}, 5000);  
			}
		};
	}
);

/***** Providers *****/
module.factory(
	"QuestionResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/questions/:questionId',
			{questionId: '@id'},
			{
				'getAnswered': {url: '/api/courses/:id/questions/:questionId/answers/count'},
				'getSelfEvalTypes': {url: '/api/selfevaltypes'}
			}
		);
		ret.MODEL = "PostsForQuestions";
		return ret;
	}
);

module.factory(
	"AttachmentResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/attachment/post/:postId/:fileId',
			{postId: '@post_id', fileId: '@file_id'}
		);
		ret.MODEL = "FilesForPosts";
		return ret;
	}
);

/***** Services *****/
module.service('attachService', function(FileUploader, $location, Toaster) {
	var filename = '';
	var alias = '';
	
	var getUploader = function() {
		var uploader = new FileUploader({
			url: '/api/attachment',
			queueLimit: 1,
			autoUpload: true
		});

		filename = '';
		alias = '';

		uploader.onCompleteItem = onComplete();
		uploader.onErrorItem = onError();

		uploader.filters.push({
			name: 'pdfFilter',
			fn: function(item, options) {
				var type = '|' + item.type.slice(item.type.lastIndexOf('/') + 1) + '|';
				var valid = '|pdf|'.indexOf(type) !== -1;
				if (!valid) {
					Toaster.error("File Type Error", "Only PDF files are accepted.")
				}
				return valid;
			}
		});

		uploader.filters.push({
			name: 'sizeFilter',
			fn: function(item) {
				var valid = item.size <= 26214400; // 1024 * 1024 * 25 -> max 25MB
				if (!valid) {
					var size = item.size / 1048576; // convert to MB
					Toaster.error("File Size Error", "The file size is "+size.toFixed(2)+"MB. The maximum allowed is 25MB.")
				}
				return valid;
			}
		});

		return uploader;
	}

	var onComplete = function() {
		return function(fileItem, response, status, headers) {
			if (response) {
				filename = response['name'];
				alias = fileItem.file.name;	
			}	
		};
	}

	var onError = function() {
		return function(fileItem, response, status, headers) {
			if (response == '413') {
				Toaster.error("File Size Error", "The file is larger than 25MB. Please upload a smaller file.");
			} else {
				Toaster.reqerror("Attachment Fail", status);
			}
		};
	}

	var resetName = function() {
		return function() {
			filename = '';
			alias = '';
		}
	}

	var getName = function() {
		return filename;
	}

	var getAlias = function() {
		return alias;
	}	

	return {
		getUploader: getUploader,
		getName: getName,
		getAlias: getAlias,
		resetName: resetName
	};
});

/***** Filters *****/
module.filter("notScoredEnd", function () {
	return function (array, key) {
		if (!angular.isArray(array)) return;
		var scored = [];
		var not_scored = [];
		angular.forEach(array, function(item, index) {
			if (key in item.scores) {
				scored.push(item);
			} else {
				not_scored.push(item);
			}
		});
		return scored.concat(not_scored);
	}
});

/***** Controllers *****/
module.controller("QuestionViewController",
	function($scope, $log, $routeParams, $location, AnswerResource, Authorize, QuestionResource, QuestionCommentResource,
			 AttachmentResource, CoursesCriteriaResource, JudgementResource, CourseResource, required_rounds, Session, Toaster,
			AnswerCommentResource, GroupResource)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
		var myAnsCount = 0; // for the event of deleting own answer
		var allStudents = {};
		var students = {};
		var userIds = {};
		Session.getUser().then(function(user) {
			$scope.loggedInUserId = user.id;
		});
		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL).then(function(result) {
			$scope.canManagePosts = result;
			if ($scope.canManagePosts) {
				GroupResource.get({'courseId': $scope.courseId}).$promise.then(
					function (ret) {
						$scope.groups = ret.groups;
					},
					function (ret) {
						Toaster.reqerror("Unable to retrieve the groups in the course.", ret);
					}
				);
				CourseResource.getStudents({'id': $scope.courseId}).$promise.then(
					function (ret) {
						allStudents = ret.students;
						students = allStudents;
						userIds = getUserIds(students);
					},
					function (ret) {
						Toaster.reqerror("Class list retrieval failed", ret);
					}
				);
			}
		});
		$scope.question = {};
		QuestionResource.get({'courseId': $scope.courseId,
			'questionId': questionId}).$promise.then(
				function (ret)
				{
					var judgeEnd = ret.question.judge_end;
					ret.question.answer_start = new Date(ret.question.answer_start);
					ret.question.answer_end = new Date(ret.question.answer_end);
					ret.question.judge_start = new Date(ret.question.judge_start);
					ret.question.judge_end = new Date(ret.question.judge_end);
					$scope.question = ret.question;

					$scope.criteria = ret.question.criteria;
					$scope.grade = {'sortby': '0', 'group': 0};
					$scope.criteriaChange();
					$scope.answers = ret.question.answers;
					$scope.reverse = true;

					$scope.readDate = Date.parse(ret.question.post.created);

					if (judgeEnd) {
						$scope.answerAvail = $scope.question.judge_end;
					} else {
						$scope.answerAvail = $scope.question.answer_end;
					}

					JudgementResource.count({'courseId': $scope.courseId, 'questionId': questionId,
								'userId': $scope.loggedInUserId}).$promise.then(
						function (ret) {
							// if an evaluation period is set - assume one criterion
							$scope.judged_req_met = ret.count >= $scope.question.num_judgement_req;
							$scope.evaluation = 0;
							if (!$scope.judged_req_met) {
								$scope.evaluation = $scope.question.num_judgement_req - ret.count;
							}
							if (judgeEnd) {
								$scope.see_answers = $scope.question.after_judging;
							// if an evaluation period is NOT set
							} else {
								$scope.see_answers = $scope.question.after_judging && $scope.judged_req_met;
							}
						},
						function (ret) {
							Toaster.reqerror("Evaluation Count Not Found", ret);
						}
					);
					AttachmentResource.get({'postId': ret.question.post.id}).$promise.then(
						function (ret) {
							$scope.question.uploadedFile = ret.file;
						},
						function (ret) {
							Toaster.reqerror("Attachment Not Found", ret);
						}
					);
					AnswerCommentResource.selfEval({'courseId': $scope.courseId, 'questionId': questionId}).$promise.then(
						function (ret) {
							$scope.selfEval_req_met = true;
							$scope.selfEval = 0;
							if ($scope.question.selfevaltype_id) {
								$scope.selfEval_req_met = ret.count > 0;
								$scope.selfEval = 1 - ret.count;
							}
						},
						function (ret) {
							Toaster.reqerror("Self-Evaluation Records Not Found.", ret);
						}
					);
				},
				function (ret)
				{
					Toaster.reqerror("Question Not Found For ID " + questionId, ret);
				}
			);
		QuestionCommentResource.get({'courseId': $scope.courseId,
			'questionId': questionId}).$promise.then(
				function (ret)
				{
					$scope.comments = ret.objects;
				},
				function (ret)
				{
					Toaster.reqerror("Comments Not Found", ret);
				}
		);
		QuestionResource.getAnswered({'id': $scope.courseId,
			'questionId': questionId}).$promise.then(
				function (ret) {
					myAnsCount = ret.answered;
					$scope.answered = ret.answered > 0;
				},
				function (ret) {
					Toaster.reqerror("Answers Not Found", ret);
				}
		);

		CourseResource.getInstructorsLabels({'id': $scope.courseId}).$promise.then(
			function (ret) {
				$scope.instructors = ret.instructors;
			},
			function (ret) {
				Toaster.reqerror("Instructors Not Found", ret);
			}
		);

		var getUserIds = function(students) {
			var users = {};
			angular.forEach(students, function(s, key){
				users[s.user.id] = 1;
			});
			return users;
		};

		$scope.groupChange = function() {
			if ($scope.grade.group == null) {
				students = allStudents;
				userIds = getUserIds(students);
			} else {
				GroupResource.get({'courseId': $scope.courseId, 'groupId': $scope.grade.group.id}).$promise.then(
					function (ret) {
						students = ret.students;
						userIds = getUserIds(students);
					},
					function (ret) {
						Toaster.reqerror("Unable to retrieve the group members", ret);
					}
				);
			}
		};

		$scope.groupFilter = function() {
			return function (answer) {
				if (!$scope.canManagePosts) {
					return true;
				}
				return answer.post.user.id in userIds;
			}
		};
		
		// enable tabs for answers and comments
		$('#answers a').click(function (e) {
			e.preventDefault();
			$(this).tab('show');
		});
		$('#comments a').click(function (e) {
			e.preventDefault();
			$(this).tab('show');
		});
		
		// revealAnswer function shows full answer content for abbreviated answers (determined by getHeight directive)
		$scope.revealAnswer = function(answerId) {
			var thisClass = '.content.'+answerId;      // class for the answer to show is "content" plus the answer's ID
			$(thisClass).css({'max-height' : 'none'}); // now remove height restriction for this answer
			this.showReadMore = false;                 // and hide the read more button for this answer
		}

		$scope.criteriaChange = function() {
			if ($scope.grade.sortby == null) {
				$scope.order = 'answer.post.created';
			} else {
				$scope.order = 'scores['+$scope.grade.sortby+'].score';
			}
		};
		
		
		// question delete function
		$scope.deleteQuestion = function(course_id, question_id) {
			QuestionResource.delete({'courseId': course_id, 'questionId': question_id}).$promise.then(
				function (ret) {
					Toaster.success("Question Delete Successful", "Successfully deleted question " + ret.id);
					$location.path('/course/'+course_id);
				},
				function (ret) {
					Toaster.reqerror("Question Delete Failed", ret);
					$location.path('/course/'+course_id);
				}
			);
		};

		$scope.deleteAnswer = function(key, course_id, question_id, answer_id) {
			AnswerResource.delete({'courseId':course_id, 'questionId':question_id, 'answerId':answer_id}).$promise.then(
				function (ret) {
					Toaster.success("Answer Delete Successful", "Successfully deleted answer "+ ret.id);
					var authorId = $scope.answers[key]['post']['user']['id'];
					$scope.answers.splice(key, 1);
					$scope.question.answers_count -= 1;
					if ($scope.loggedInUserId == authorId) {
						myAnsCount--;
						$scope.answered = myAnsCount > 0;
					}
				},
				function (ret) {
					Toaster.reqerror("Answer Delete Failed", ret);
				}
			);
		};

		$scope.deleteComment = function(key, course_id, question_id, comment_id) {
			QuestionCommentResource.delete({'courseId': course_id, 'questionId': question_id, 'commentId': comment_id}).$promise.then(
				function (ret) {
					Toaster.success("Comment Delete Successful", "Successfully deleted comment " + ret.id);
					$scope.comments.splice(key, 1);
					$scope.question.comments_count--;
				},
				function (ret) {
					Toaster.reqerror("Comment Delete Failed", ret);
				}
			);
		}

		$scope.deleteReply = function(answerKey, commentKey, course_id, question_id, answer_id, comment_id) {
			AnswerCommentResource.delete({'courseId': course_id, 'questionId': question_id, 'answerId': answer_id, 'commentId': comment_id}).$promise.then(
				function (ret) {
					Toaster.success("Reply Delete Successful", "Successfully deleted reply " + ret.id);
					$scope.answers[answerKey]['comments'].splice(commentKey, 1);
				},
				function (ret) {
					Toaster.reqerror("Reply Delete Failed", ret);
				}
			);
		}
	}
);
module.controller("QuestionCreateController",
	function($scope, $log, $location, $routeParams, QuestionResource, CoursesCriteriaResource,
			 QuestionsCriteriaResource, required_rounds, Toaster, attachService)
	{
		var courseId = $routeParams['courseId'];
		$scope.question = {};
		$scope.question.can_reply = true; //want default to encourage discussion
		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();
		$scope.recommended_eval = Math.floor(required_rounds / 2);
		// default the setting to the recommended # of evaluations
		$scope.question.num_judgement_req = $scope.recommended_eval;
		$scope.oneSelected = false;		// logic to make sure at least one criterion is selected
		$scope.selectedCriteria = {};
		$scope.selfevaltypes = [];

		CoursesCriteriaResource.get({'courseId': courseId}).$promise.then(
			function (ret) {
				$scope.courseCriteria = ret.objects
			},
			function (ret) {
				Toaster.reqerror("Criteria Not Found.");
			}
		);

		$scope.selectCriteria = function(criteriaId) {
			// check whether at least one criterion is selected
			$scope.oneSelected = false;
			for (var cId in $scope.selectedCriteria) {
				if ($scope.selectedCriteria[cId]) {
					$scope.oneSelected = true;
					break;
				}
			}
		};

		QuestionResource.getSelfEvalTypes().$promise.then(
			function (ret) {
				$scope.selfevaltypes = ret.types;
				$scope.question.selfevaltype_id = $scope.selfevaltypes[0].id;
			},
			function (ret) {
				Toaster.reqerror("Self Evaluation Types Not Found.");
			}
		);

		$scope.questionSubmit = function () {
			$scope.submitted = true;
			// answer end datetime has to be after answer start datetime
			if ($scope.question.answer_start >= $scope.question.answer_end) {
				Toaster.error('Answer Period Error', 'Answer end time must be after answer start time.');
				$scope.submitted = false;
				return;
			} else if ($scope.question.availableCheck && !($scope.question.answer_end <= $scope.question.judge_start && $scope.question.judge_start <= $scope.question.judge_end)) {
				Toaster.error("Time Period Error", 'Please double-check the answer and/or evaluation period start and end times.');
				$scope.submitted = false;
				return;
			}
			// if option is not checked; make sure no judge dates are saved.
			if (!$scope.question.availableCheck) {
				$scope.question.judge_start = null;
				$scope.question.judge_end = null;
			}
			$scope.question.name = attachService.getName();
			$scope.question.alias = attachService.getAlias();
			QuestionResource.save({'courseId': courseId}, $scope.question).
				$promise.then(
					function (ret)
					{
						// add criteria to the question
						addMultipleCriteria(courseId, ret.id, $scope.selectedCriteria);
						$scope.submitted = false;
						Toaster.success("New Question Created",'"' + ret.title + '" should now be listed.');
						$location.path('/course/' + courseId);
					},
					function (ret)
					{
						$scope.submitted = false;
						Toaster.reqerror("No New Question Created", ret);
					}
				);
		};

		var addMultipleCriteria = function(courseId, questionId, criteria) {
			angular.forEach(criteria, function(selected, criterionId){
				// add to question
				QuestionsCriteriaResource.save({'courseId': courseId, 'questionId': questionId,
						'criteriaId': criterionId}, {}).$promise.then(
						function (ret) {},
						function (ret) {
							// error therefore uncheck the box
							Toaster.reqerror("Failed to add the criterion " + criterionId + " to the question.", ret);
						}
				);
			});
		}
	}
);

module.controller("QuestionEditController",
	function($scope, $log, $location, $routeParams, $filter, QuestionResource, AttachmentResource,
			 QuestionsCriteriaResource, CoursesCriteriaResource, required_rounds, Toaster, attachService)
	{
		var courseId = $routeParams['courseId'];
		$scope.questionId = $routeParams['questionId'];
		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();
		$scope.recommended_eval = Math.floor(required_rounds / 2);
		$scope.question = {};
		$scope.oneSelected = false;		// logic to make sure at least one criterion is selected
		$scope.selectedCriteria = {};

		$scope.deleteFile = function(post_id, file_id) {
			AttachmentResource.delete({'postId': post_id, 'fileId': file_id}).$promise.then(
				function (ret) {
					Toaster.success('Attachment Delete Successful', "This attachement was successfully deleted.");
					$scope.question.uploadedFile = false;
				},
				function (ret) {
					Toaster.reqerror('Attachment Delete Failed', ret);
				}
			);
		};

		$scope.selectCriteria = function(criteriaId) {
			if ($scope.selectedCriteria[criteriaId]) {
				// add to question
				QuestionsCriteriaResource.save({'courseId': courseId, 'questionId': $scope.questionId,
						'criteriaId': criteriaId}, {}).$promise.then(
						function (ret) {
							Toaster.success("Successfully added the criterion to the question.");
						},
						function (ret) {
							// error therefore uncheck the box
							Toaster.reqerror("Failed to add the criterion to the question.", ret);
							$scope.selectedCriteria[criteriaId] = false;
						}
				);
			} else {
				// remove from question
				QuestionsCriteriaResource.delete({'courseId': courseId, 'questionId': $scope.questionId,
						'criteriaId': criteriaId}).$promise.then(
						function (ret) {
							Toaster.success("Successfully removed the criterion from the question.");
						},
						function (ret) {
							// error therefore recheck the box
							$scope.selectedCriteria[criteriaId] = true;
							Toaster.reqerror("Failed to remove the criterion from the question.", ret);
						}
				);
			}

			// check whether at least one criterion is selected
			$scope.oneSelected = false;
			for (var cId in $scope.selectedCriteria) {
				if ($scope.selectedCriteria[cId]) {
					$scope.oneSelected = true;
					break;
				}
			}
		};

		QuestionResource.getSelfEvalTypes().$promise.then(
			function (ret) {
				$scope.selfevaltypes = ret.types;
			},
			function (ret) {
				Toaster.reqerror("Self Evaluation Types Not Found.");
			}
		);

		QuestionResource.get({'courseId': courseId, 'questionId': $scope.questionId}).$promise.then(
			function (ret) {
				ret.question.answer_start = new Date(ret.question.answer_start);
				ret.question.answer_end = new Date(ret.question.answer_end);	
				if (ret.question.judge_start && ret.question.judge_end) {
					ret.question.availableCheck = true;
					ret.question.judge_start = new Date(ret.question.judge_start);
					ret.question.judge_end = new Date(ret.question.judge_end);
				}
				$scope.question = ret.question;
				$scope.judged = ret.question.judged;

				if ($scope.question.selfevaltype_id) {
					$scope.question.selfEvalCheck = true;
				} else {
					$scope.question.selfevaltype_id = $scope.selfevaltypes[0].id;
				}

				AttachmentResource.get({'postId': ret.question.post.id}).$promise.then(
					function (ret) {
						$scope.question.uploadedFile = ret.file;
						
					},
					function (ret) {
						Toaster.reqerror("Attachment Not Found", ret);
					}
				);
				CoursesCriteriaResource.get({'courseId': courseId}).$promise.then(
					function (ret) {
						$scope.courseCriteria = ret.objects;
						$scope.oneSelected = $scope.question.criteria.length > 0;
						var inQuestion = {};
						angular.forEach($scope.question.criteria, function(c, key) {
							inQuestion[c.criterion.id] = 1;
						});
						for (key in ret.objects) {
							c = ret.objects[key];
							$scope.selectedCriteria[c.criterion.id] = c.criterion.id in inQuestion
						}
					},
					function (ret) {
						Toaster.reqerror("Criteria Not Found", ret);
					}
				);
			},
			function (ret) {
				Toaster.reqerror("Question Not Found", "No question found for id "+$scope.questionId);
			}
		);

		$scope.questionSubmit = function () {
			$scope.submitted = true;
			// answer end datetime has to be after answer start datetime
			if ($scope.question.answer_start > $scope.question.answer_end) {
				Toaster.error('Answer Period Error', 'Answer end time must be after answer start time.');
				$scope.submitted = false;
				return;
			} else if ($scope.question.availableCheck && !($scope.question.answer_end <= $scope.question.judge_start
				&& $scope.question.judge_start < $scope.question.judge_end)) {
				Toaster.error("Time Period Error", 'Please double-check the answer and/or evaluation period start and end times.');
				$scope.submitted = false;
				return;
			}
			$scope.question.name = attachService.getName();
			$scope.question.alias = attachService.getAlias();
			// if option is not checked; make sure no judge dates are saved.
			if (!$scope.question.availableCheck) {
				$scope.question.judge_start = null;
				$scope.question.judge_end = null;
			}
			if (!$scope.question.selfEvalCheck) {
				delete $scope.question.selfevaltype_id;
			}
			QuestionResource.save({'courseId': courseId}, $scope.question).$promise.then(
				function() {
					$scope.submitted = false;
					Toaster.success("Question Updated");
					$location.path('/course/' + courseId);
				 },
				function(ret) { 
					$scope.submitted = false;
					Toaster.reqerror("Question Not Updated", ret);
				}
			);
		};
	}
);

// End anonymous function
})();
