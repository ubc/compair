// Provides the services and controllers for questions.
//
(function() {
function combineDateTime(datetime) {
	var date = new Date(datetime.date);
	var time = new Date(datetime.time);
	date.setHours(time.getHours(), time.getMinutes(), time.getSeconds(), time.getMilliseconds());
	return date;
}

var module = angular.module('ubc.ctlt.acj.question',
	[
		'angularFileUpload',
		'ngResource',
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.authentication',
		'ubc.ctlt.acj.authorization',
		'ubc.ctlt.acj.comment',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.interceptor',
		'ubc.ctlt.acj.common.mathjax',
		'ubc.ctlt.acj.common.pdf',
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.group',
		'ubc.ctlt.acj.judgement',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.session',
		'ui.bootstrap'
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
						e.preventDefault();
						e.stopImmediatePropagation();
					}
				});
			}
		}
	}
);

module.directive(
	'getHeight',
	[ "$timeout",
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
				}, 7000);
			}
		};
	}
]);

module.directive(
	'toolTip',
	function() {
		return {
			restrict: 'A',
			link: function(scope, element) {
				$(element).hover(function(){
					// on mouseenter
					$(element).tooltip('show');
				}, function(){
					// on mouseleave
					$(element).tooltip('hide');
				});
			}
		};
	}
);

module.directive('comparisonPreview', function() {
	return {
		/* this template is our simple text with button to launch the preview */
		templateUrl: 'modules/question/preview-inline-template.html',
		controller: function ($scope, $modal) {
			/* need to pass to comparison template all expected properties to complete the preview */
			$scope.previewPopup = function() {
				/* question has title that is entered, content that is entered, number of comparisons that is entered (or else 3), no files */
				$scope.question = {
					title: $scope.question.title,
					post: {
						content: $scope.question.post.content,
						files: []
					},
					num_judgement_req: $scope.question.num_judgement_req ? $scope.question.num_judgement_req : 3
				};
				/* previewed criteria initially empty */
				$scope.previewCriteria = [];
				/* we need to determine what has been picked to fill out the previewed criteria */
				var pickCriteria = function(chosen, all) {
					/* first we will loop through the selected criteria */
					angular.forEach(chosen, function(selected, criterionId) {
						/* then we will loop through the course criteria to find what matches */
						angular.forEach(all, function(courseCrit) {
							if (criterionId == courseCrit.id && selected == true) {
								// alert('match' + criterionId + ' ' + courseCrit.id);
								/* matching criteria are added to the preview as criterion */
								$scope.previewCriteria.push({criterion: courseCrit});
							} else {
								//alert('MISmatch ' + criterionId + ' ' + courseCrit.id);
							}
						});
					});
				};
				/* call the function before setting the criteria, passing in selected criteria and all course criteria arrays */
				pickCriteria($scope.selectedCriteria, $scope.courseCriteria);
				/* then set question criteria as the ones we've determined should be previewed */
				$scope.question.criteria = $scope.previewCriteria;
				/* set current round #, answer #s, and total round # for preview */
				$scope.current = 1;
				$scope.firstAnsNum = 1;
				$scope.secondAnsNum = 2;
				$scope.total = $scope.question.num_judgement_req;
				/* answer pair shown is dummy content, no files */
				$scope.answerPair = {
					answers: [
					{
						content: "<p>The first student answer in the pair will appear here.</p>",
						files: []
					},
					{
						content: "<p>The second student answer in the pair will appear here.</p>",
						files: []
					} ]
				};
				/* student view preview is comparison template */
				$scope.thePreview = $modal.open({
					templateUrl: 'modules/judgement/judgement-core.html',
					scope: $scope
				});
			}
		}
	};
});

/***** Providers *****/
module.factory(
	"QuestionResource",
	[ "$resource", "Interceptors",
	function ($resource, Interceptors)
	{
		var url = '/api/courses/:courseId/questions/:questionId';
		var ret = $resource(url, {questionId: '@id'},
			{
				'get': {url: url, cache: true},
				'save': {method: 'POST', url: url, interceptor: Interceptors.cache},
				'delete': {method: 'DELETE', url: url, interceptor: Interceptors.cache},
				'getAnswered': {url: '/api/courses/:id/questions/:questionId/answers/count'}
			}
		);
		ret.MODEL = "PostsForQuestions";
		return ret;
	}
]);

module.factory(
	"AttachmentResource",
	[ "$resource", 
	function ($resource)
	{
		var ret = $resource(
			'/api/attachment/post/:postId/:fileId',
			{postId: '@post_id', fileId: '@file_id'}
		);
		ret.MODEL = "FilesForPosts";
		return ret;
	}
]);

module.factory(
	"SelfEvaluationTypeResource",
	[ "$resource", 
	function($resource)
	{
		var url = '/api/selfevaltypes';
		var ret = $resource(url, {},
			{
				'get': {url: url, cache: true}
			});
		ret.model = "SelfEvalTypes";
		return ret;
	}
]);

/***** Services *****/
module.service('attachService', 
		["FileUploader", "$location", "Toaster", 
		function(FileUploader, $location, Toaster) {
	var filename = '';
	var alias = '';

	var getUploader = function() {
		var uploader = new FileUploader({
			url: '/api/attachment',
			queueLimit: 1,
			autoUpload: true,
			headers: {
				Accept: 'application/json'
			}
		});

		filename = '';
		alias = '';

		uploader.onCompleteItem = onComplete();
		uploader.onErrorItem = onError();

		uploader.filters.push({
			name: 'pdfFilter',
			fn: function(item) {
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
	};

	var onComplete = function() {
		return function(fileItem, response) {
			if (response) {
				filename = response['name'];
				alias = fileItem.file.name;
			}
		};
	};

	var onError = function() {
		return function(fileItem, response, status) {
			if (response == '413') {
				Toaster.error("File Size Error", "The file is larger than 25MB. Please upload a smaller file.");
			} else {
				Toaster.reqerror("Attachment Fail", status);
			}
		};
	};

	var resetName = function() {
		return function() {
			filename = '';
			alias = '';
		}
	};

	var getName = function() {
		return filename;
	};

	var getAlias = function() {
		return alias;
	};

	return {
		getUploader: getUploader,
		getName: getName,
		getAlias: getAlias,
		resetName: resetName
	};
}]);

/***** Filters *****/
module.filter("excludeInstr", function() {
	return function(items, instructors) {
		var filtered = [];
		angular.forEach(items, function(item) {
			// if user id is NOT in the instructors array, keep it
			if (!instructors[item.user_id]) {
				filtered.push(item);
			}
		});
		return filtered;
	};
});

module.filter("notScoredEnd", function () {
	return function (array, key) {
		if (!angular.isArray(array)) return;
		var scored = [];
		var not_scored = [];
		angular.forEach(array, function(item) {
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
	["$scope", "$log", "$routeParams", "$location", "AnswerResource", "Authorize", "QuestionResource", "QuestionCommentResource",
			 "AttachmentResource", "CoursesCriteriaResource", "JudgementResource", "EvalCommentResource", "CourseResource", 
			 "required_rounds", "Session", "Toaster", "AnswerCommentResource", "GroupResource",
	function($scope, $log, $routeParams, $location, AnswerResource, Authorize, QuestionResource, QuestionCommentResource,
			 AttachmentResource, CoursesCriteriaResource, JudgementResource, EvalCommentResource, CourseResource, 
			 required_rounds, Session, Toaster, AnswerCommentResource, GroupResource)
	{
		$scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
		var params = {
			courseId: $scope.courseId,
			questionId: questionId
		};
		var myAnsCount = 0; // for the event of deleting own answer
		$scope.allStudents = {};
		var userIds = {};
		$scope.totalNumAnswers = 0;
		$scope.answerFilters = {
			page: 1,
			perPage: 20,
			group: null,
			author: null,
			orderBy: null
		};
		$scope.selfEval_req_met = true;
		$scope.selfEval = 0;

		Session.getUser().then(function(user) {
			$scope.loggedInUserId = user.id;
			JudgementResource.getAvailPairLogic(angular.extend({'userId': $scope.loggedInUserId}, params), function (ret) {
				$scope.availPairsLogic = ret.availPairsLogic;
			});
		});
		Authorize.can(Authorize.MANAGE, QuestionResource.MODEL, $scope.courseId).then(function(result) {
			$scope.canManagePosts = result;
			if ($scope.canManagePosts) {
				GroupResource.get({'courseId': $scope.courseId}, function (ret) {
					$scope.groups = ret.groups;
				});
			}
		});
		$scope.students = {};
		CourseResource.getStudents({'id': $scope.courseId}, function (ret) {
			$scope.allStudents = ret.students;
			$scope.students = ret.students;
			userIds = $scope.getUserIds(ret.students);
		});
		$scope.question = {};
		QuestionResource.get(params, function (ret) {
				var judgeEnd = ret.question.judge_end;
				ret.question.judgeEnd = judgeEnd;
				ret.question.answer_start = new Date(ret.question.answer_start);
				ret.question.answer_end = new Date(ret.question.answer_end);
				ret.question.judge_start = new Date(ret.question.judge_start);
				ret.question.judge_end = new Date(ret.question.judge_end);
				$scope.question = ret.question;

				$scope.criteria = ret.question.criteria;
				if ($scope.criteria.length >= 1) {
					$scope.answerFilters.orderBy = $scope.criteria[0].id;
				}
				$scope.reverse = true;

				$scope.evalcriteria = {};
				angular.forEach(ret.question.criteria, function(criterion){
					$scope.evalcriteria[criterion['id']] = criterion['criterion']['name'];
				});

				$scope.readDate = Date.parse(ret.question.post.created);

				if (judgeEnd) {
					$scope.answerAvail = $scope.question.judge_end;
				} else {
					$scope.answerAvail = $scope.question.answer_end;
				}

				JudgementResource.count(angular.extend({'userId': $scope.loggedInUserId}, params), function (ret) {
						$scope.judged_req_met = ret.count >= $scope.question.num_judgement_req;
						$scope.evaluation = 0;
						if (!$scope.judged_req_met) {
							$scope.evaluation = $scope.question.num_judgement_req - ret.count;
						}
						// if evaluation period is set answers can be seen after it ends
						if (judgeEnd) {
							$scope.see_answers = $scope.question.after_judging;
							// if an evaluation period is NOT set - answers can be seen after req met
						} else {
							$scope.see_answers = $scope.question.after_judging && $scope.judged_req_met;
						}
						var diff = $scope.question.answers_count - myAnsCount;
						var eval_left = ((diff * (diff - 1)) / 2);
						$scope.warning = ($scope.question.num_judgement_req - ret.count) > eval_left;
				});

				// get the self eval if enabled in question
				if ($scope.question.selfevaltype_id) {
					AnswerCommentResource.query(angular.extend({}, params, {user_ids: $scope.loggedInUserId, selfeval: 'only'}),
						function (ret) {
							$scope.selfEval_req_met = ret.length > 0;
							$scope.selfEval = 1 - ret.length;
						}
					);
				}
				// update the answer list
				$scope.updateAnswerList();
				// register watcher here so that we start watching when all filter values are set
				$scope.$watchCollection('answerFilters', filterWatcher);
			},
			function (ret)
			{
				Toaster.reqerror("Question Not Found For ID " + questionId, ret);
			}
		);


		$scope.comments = QuestionCommentResource.get(params);

		QuestionResource.getAnswered({'id': $scope.courseId, 'questionId': questionId},
			function (ret) {
				myAnsCount = ret.answered;
				$scope.answered = ret.answered > 0;
			},
			function (ret) {
				Toaster.reqerror("Answers Not Found", ret);
			}
		);

		CourseResource.getInstructorsLabels({'id': $scope.courseId},
			function (ret) {
				$scope.instructors = ret.instructors;
			},
			function (ret) {
				Toaster.reqerror("Instructors Not Found", ret);
			}
		);

		$scope.getUserIds = function(students) {
			var users = {};
			angular.forEach(students, function(s){
				users[s.user.id] = 1;
			});
			return users;
		};

		$scope.adminFilter = function() {
			return function (answer) {
				// assume if any filter is applied - instructor/TAs answer will not meet requirement
				return !$scope.answerFilters.author && !$scope.answerFilters.group
			}
		};

		//TODO: this filter should be implemented in backend
		$scope.commentFilter = function(answer) {
			return function (comment) {
				// can see if canManagePosts OR their own answer OR not from evaluation and selfeval
				return $scope.canManagePosts || answer.user_id == $scope.loggedInUserId ||
					!(comment.evaluation || comment.selfeval || comment.type == 0);
			}
		};

		var tab = 'answers';
		// tabs: answers, help, participation, comparisons
		$scope.setTab = function(name) {
			tab = name;
			if (name == "comparisons") {
				//need some way to get answers here ???
				//originally had a $scope.ans to reference...
				$scope.comparisons = EvalCommentResource.view(params);
				var answer_params = angular.extend({}, params, {author: $scope.loggedInUserId});
				$scope.user_answers = AnswerResource.get(answer_params, function(ret) {
					// pre-load the comments to display if there is any self-eval
					_.forEach($scope.user_answers.objects, function(answer) {
						$scope.loadComments(answer);
					});
				});
			}
		};
		$scope.showTab = function(name) {
			return tab == name;
		};

		$scope.loadAnswer = function(id) {
			if (_.find($scope.answers, {id: id})) return;
			AnswerResource.get({'courseId': $scope.courseId, 'questionId': questionId, 'answerId': id}, function(response) {
				$scope.answers.objects.push(response);
			});
		};

		// revealAnswer function shows full answer content for abbreviated answers (determined by getHeight directive)
		$scope.revealAnswer = function(answerId) {
			var thisClass = '.content.'+answerId;      // class for the answer to show is "content" plus the answer's ID
			$(thisClass).css({'max-height' : 'none'}); // now remove height restriction for this answer
			this.showReadMore = false;                 // and hide the read more button for this answer
		};

		// question delete function
		$scope.deleteQuestion = function(course_id, question_id) {
			QuestionResource.delete({'courseId': course_id, 'questionId': question_id},
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

		$scope.deleteAnswer = function(answer, course_id, question_id, answer_id) {
			AnswerResource.delete({'courseId':course_id, 'questionId':question_id, 'answerId':answer_id},
				function (ret) {
					Toaster.success("Answer Delete Successful", "Successfully deleted answer "+ ret.id);
					var authorId = answer['user_id'];
					$scope.answers.objects.splice($scope.answers.objects.indexOf(answer), 1);
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

		// unflag a flagged answer
		$scope.unflagAnswer = function(answer, course_id, question_id, answer_id) {
			var params = {'flagged': false};
			var resultMsg = "Answer Successfully Unflagged";
			AnswerResource.flagged({'courseId':course_id, 'questionId':question_id, 'answerId':answer_id}, params).$promise.then(
				function () {
					answer['flagged'] = false;
					Toaster.success(resultMsg);
				},
				function (ret) {
					Toaster.reqerror("Unable To Change Flag", ret);
				}
			);
		};

		$scope.loadComments = function(answer) {
			answer.comments = AnswerCommentResource.query(
				{courseId: $scope.courseId, questionId: questionId, answer_ids: answer.id})
		};

		$scope.deleteComment = function(key, course_id, question_id, comment_id) {
			QuestionCommentResource.delete({'courseId': course_id, 'questionId': question_id, 'commentId': comment_id},
				function (ret) {
					Toaster.success("Comment Delete Successful", "Successfully deleted comment " + ret.id);
					$scope.comments.objects.splice(key, 1);
					$scope.question.comments_count--;
				},
				function (ret) {
					Toaster.reqerror("Comment Delete Failed", ret);
				}
			);
		};

		$scope.deleteReply = function(answer, commentKey, course_id, question_id, answer_id, comment_id) {
			AnswerCommentResource.delete({'courseId': course_id, 'questionId': question_id, 'answerId': answer_id, 'commentId': comment_id},
				function (ret) {
					Toaster.success("Reply Delete Successful", "Successfully deleted reply.");
					var comment = answer['comments'].splice(commentKey, 1)[0];
					if (comment['evaluation'] || comment['selfeval'] || comment['type'] == 0) {
						answer.private_comments_count--;
					} else {
						answer.public_comments_count--;
					}
					answer.comments_count--;
				},
				function (ret) {
					Toaster.reqerror("Reply Delete Failed", ret);
				}
			);
		};

		$scope.updateAnswerList = function() {
			var params = angular.merge({'courseId': $scope.courseId, 'questionId': questionId}, $scope.answerFilters);
			if (params.group != null) {
				params.group = params.group.id;
			}
			if (params.author != null) {
				params.author = params.author.user.id;
			}
			$scope.answers = AnswerResource.get(params, function(response) {
				$scope.totalNumAnswers = response.total;
			});
			// TO DO: grab the right array of answer ids/scores depending on the criteria selected and load into allScores here
			// (can use $scope.answerFilters.orderBy to grab the criteria ID for requesting the scores)
			$scope.allScores = {
				"104":"0",
				"95":"0",
				"85":"4.38635",
				"183":"2.19318",
				"110":"2.19318",
				"109":"2.19318",
				"99":"2.19318",
				"96":"1.96212",
				"98":"1.61186",
				"112":"1.46212",
				"108":"1.46212",
				"94":"1.46212",
				"84":"1.23106",
				"83":"1.23106",
				"81":"0.768941",
				"97":"0.731059" };
			$scope.rankScores($scope.allScores);
		};
		
		// function to show the simple ranking for the student view
		$scope.rankScores = function(allScores) {
			// first sort scores high-to-low
			$scope.rankSort = [];
			for (var prop in allScores) {
				if (allScores.hasOwnProperty(prop)) {
					$scope.rankSort.push({
						'key': prop,
						'value': allScores[prop]
					});
				}
			}
			// need to sort by id (key) first to get ties to show up correctly later
			$scope.rankSort.sort(function(a, b) { return b.key - a.key; });
			$scope.rankSort.sort(function(a, b) { return b.value - a.value; });
			// then loop through scores to increment ranking number
			$scope.rankNumber = 0;
			var prevScore = -1;
			var tied = "";
			for (var answer in $scope.rankSort) {
				if (prevScore != $scope.rankSort[answer].value) {
					$scope.rankNumber += 1;
					tied = "";
				}
				if (prevScore == $scope.rankSort[answer].value) {
					tied = " (tied)";
				}
				// now overwrite score with ranking number plus tied status
				allScores[$scope.rankSort[answer].key] = ($scope.rankNumber+tied);
				prevScore = $scope.rankSort[answer].value;
			}
		};

		var filterWatcher = function(newValue, oldValue) {
			if (angular.equals(newValue, oldValue)) return;
			if (oldValue.group != newValue.group) {
				$scope.answerFilters.author = null;
				if ($scope.answerFilters.group == null) {
					userIds = $scope.getUserIds($scope.allStudents);
					$scope.students = $scope.allStudents;
				} else {
					GroupResource.get({'courseId': $scope.courseId, 'groupId': $scope.answerFilters.group.id},
						function (ret) {
							$scope.students = ret.students;
							userIds = $scope.getUserIds(ret.students);
						},
						function (ret) {
							Toaster.reqerror("Unable to retrieve the group members", ret);
						}
					);
				}
				$scope.answerFilters.page = 1;
			}
			if (oldValue.author != newValue.author) {
				userIds = {};
				if ($scope.answerFilters.author == null) {
					userIds = $scope.getUserIds($scope.students);
				} else {
					userIds[$scope.answerFilters.author.user.id] = 1;
				}
				$scope.answerFilters.page = 1;
			}
			$scope.updateAnswerList();
		};
	}
]);
module.controller("QuestionCreateController",
	[ "$scope", "$log", "$location", "$routeParams", "QuestionResource", "CoursesCriteriaResource",
			 "QuestionsCriteriaResource", "required_rounds", "Toaster", "attachService", "SelfEvaluationTypeResource",
	function($scope, $log, $location, $routeParams, QuestionResource, CoursesCriteriaResource,
			 QuestionsCriteriaResource, required_rounds, Toaster, attachService, SelfEvaluationTypeResource)
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

		// DATETIMES
		// declaration
		var today = new Date();
		$scope.format = 'dd-MMMM-yyyy';
		$scope.date = {
			'astart': {'date': new Date(), 'time': new Date().setHours(0, 0, 0, 0)},
			'aend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
			'jstart': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
			'jend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)}
		};
		// initialization
		$scope.date.astart.date.setDate(today.getDate()+1);
		$scope.date.aend.date.setDate(today.getDate()+8);
		$scope.date.jstart.date.setDate(today.getDate()+8);
		$scope.date.jend.date.setDate(today.getDate()+15);

		$scope.date.astart.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.astart.opened = true;
		};
		$scope.date.aend.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.aend.opened = true;
		};
		$scope.date.jstart.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.jstart.opened = true;
		};
		$scope.date.jend.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.jend.opened = true;
		};

		$scope.questionSubmit = function () {
			$scope.submitted = true;
			$scope.question.answer_start = combineDateTime($scope.date.astart);
			$scope.question.answer_end = combineDateTime($scope.date.aend);
			$scope.question.judge_start = combineDateTime($scope.date.jstart);
			$scope.question.judge_end = combineDateTime($scope.date.jend);

			// answer end datetime has to be after answer start datetime
			if ($scope.question.answer_start >= $scope.question.answer_end) {
				Toaster.error('Answer Period Error', 'Answer end time must be after answer start time.');
				$scope.submitted = false;
				return;
			} else if ($scope.question.availableCheck && !($scope.question.answer_start <= $scope.question.judge_start && $scope.question.judge_start <= $scope.question.judge_end)) {
				Toaster.error("Time Period Error", 'Please double-check the answer and/or evaluation period start and end times.');
				$scope.submitted = false;
				return;
			}
			// if option is not checked; make sure no judge dates are saved.
			if (!$scope.question.availableCheck) {
				$scope.question.judge_start = null;
				$scope.question.judge_end = null;
			}
			if (!$scope.question.selfEvalCheck) {
				delete $scope.question.selfevaltype_id;
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

		// Criteria
		CoursesCriteriaResource.get({'courseId': courseId},
			function (ret) {
				$scope.courseCriteria = ret.objects;
			},
			function (ret) {
				Toaster.reqerror("Criteria Not Found.", ret);
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

		var addMultipleCriteria = function(courseId, questionId, criteria) {
			angular.forEach(criteria, function(selected, criterionId){
				if (selected == true) {
					QuestionsCriteriaResource.save({'courseId': courseId, 'questionId': questionId,
							'criteriaId': criterionId}, {}).$promise.then(
							function (ret) {},
							function (ret) {
								// error therefore uncheck the box
								Toaster.reqerror("Failed to add the criterion " + criterionId + " to the question.", ret);
							}
					);
				}
			});
		};

		// Self-Evaluation
		SelfEvaluationTypeResource.get().$promise.then(
			function (ret) {
				$scope.selfevaltypes = ret.types;
				$scope.question.selfevaltype_id = $scope.selfevaltypes[0].id;
			},
			function (ret) {
				Toaster.reqerror("Self Evaluation Types Not Found.", ret);
			}
		);
	}
]);

module.controller("QuestionEditController",
	[ "$scope", "$log", "$location", "$routeParams", "$filter", "QuestionResource", "AttachmentResource",
			 "QuestionsCriteriaResource", "CoursesCriteriaResource", "required_rounds", "Toaster",
			 "SelfEvaluationTypeResource", "attachService",
	function($scope, $log, $location, $routeParams, $filter, QuestionResource, AttachmentResource,
			 QuestionsCriteriaResource, CoursesCriteriaResource, required_rounds, Toaster,
			 SelfEvaluationTypeResource, attachService)
	{
		var courseId = $routeParams['courseId'];
		$scope.questionId = $routeParams['questionId'];
		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();
		$scope.recommended_eval = Math.floor(required_rounds / 2);
		$scope.question = {};
		$scope.oneSelected = false;		// logic to make sure at least one criterion is selected
		$scope.selectedCriteria = {};
		$scope.format = 'dd-MMMM-yyyy';
		$scope.date = {'astart': {}, 'aend': {}, 'jstart': {}, 'jend': {}};

		$scope.date.astart.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.astart.opened = true;
		};
		$scope.date.aend.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.aend.opened = true;
		};
		$scope.date.jstart.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.jstart.opened = true;
		};
		$scope.date.jend.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.jend.opened = true;
		};


		$scope.deleteFile = function(post_id, file_id) {
			AttachmentResource.delete({'postId': post_id, 'fileId': file_id}).$promise.then(
				function () {
					Toaster.success('Attachment Delete Successful', "This attachment was successfully deleted.");
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
						function () {
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
						function () {
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

		SelfEvaluationTypeResource.get(
			function (ret) {
				$scope.selfevaltypes = ret.types;
			},
			function (ret) {
				Toaster.reqerror("Self Evaluation Types Not Found.", ret);
			}
		);

		QuestionResource.get({'courseId': courseId, 'questionId': $scope.questionId}).$promise.then(
			function (ret) {
				$scope.date.astart.date = new Date(ret.question.answer_start);
				$scope.date.astart.time = new Date(ret.question.answer_start);
				$scope.date.aend.date = new Date(ret.question.answer_end);
				$scope.date.aend.time = new Date(ret.question.answer_end);

				if (ret.question.judge_start && ret.question.judge_end) {
					ret.question.availableCheck = true;
					$scope.date.jstart.date = new Date(ret.question.judge_start);
					$scope.date.jstart.time = new Date(ret.question.judge_start);
					$scope.date.jend.date = new Date(ret.question.judge_end);
					$scope.date.jend.time = new Date(ret.question.judge_end)
				} else {
					$scope.date.jstart.date = new Date($scope.date.aend.date);
					$scope.date.jstart.time = new Date($scope.date.aend.time);
					$scope.date.jend.date = new Date();
					$scope.date.jend.date.setDate($scope.date.jstart.date.getDate()+7);
					$scope.date.jend.time = new Date($scope.date.aend.time);
					$scope.date.jstart.date = $scope.date.jstart.date;
					$scope.date.jend.date = $scope.date.jend.date;
				}
				$scope.question = ret.question;
				$scope.judged = ret.question.judged;

				if ($scope.question.selfevaltype_id) {
					$scope.question.selfEvalCheck = true;
				} else {
					/*TODO: add empty option - when the question is cached, the API call
					is a lot faster than the selfeval type API call, therefore we cannot
					just select the first type in the list since it is undefined
					*/
					//$scope.question.selfevaltype_id = $scope.selfevaltypes[0].id;
					$scope.question.selfevaltype_id = 1;
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
						angular.forEach($scope.question.criteria, function(c) {
							inQuestion[c.criterion.id] = 1;
						});
						for (var key in ret.objects) {
							var c = ret.objects[key];
							$scope.selectedCriteria[c.id] = c.id in inQuestion;
						}
					},
					function (ret) {
						Toaster.reqerror("Criteria Not Found", ret);
					}
				);
			},
			function () {
				Toaster.reqerror("Question Not Found", "No question found for id "+$scope.questionId);
			}
		);

		$scope.questionSubmit = function () {
			$scope.submitted = true;
			$scope.question.answer_start = combineDateTime($scope.date.astart);
			$scope.question.answer_end = combineDateTime($scope.date.aend);
			$scope.question.judge_start = combineDateTime($scope.date.jstart);
			$scope.question.judge_end = combineDateTime($scope.date.jend);
			// answer end datetime has to be after answer start datetime
			if ($scope.question.answer_start > $scope.question.answer_end) {
				Toaster.error('Answer Period Error', 'Answer end time must be after answer start time.');
				$scope.submitted = false;
				return;
			} else if ($scope.question.availableCheck && !($scope.question.answer_start <= $scope.question.judge_start
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
]);

// End anonymous function
})();
