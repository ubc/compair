// Provides the services and controllers for assignments.
//
(function() {
function combineDateTime(datetime) {
	var date = new Date(datetime.date);
	var time = new Date(datetime.time);
	date.setHours(time.getHours(), time.getMinutes(), time.getSeconds(), time.getMilliseconds());
	return date;
}

var module = angular.module('ubc.ctlt.acj.assignment',
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
		'ubc.ctlt.acj.criterion',
		'ubc.ctlt.acj.group',
		'ubc.ctlt.acj.comparison',
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
		templateUrl: 'modules/assignment/preview-inline-template.html',
		controller: function ($scope, $modal) {
			/* need to pass to comparison template all expected properties to complete the preview */
			$scope.previewPopup = function() {
				/* assignment has name that is entered, content that is entered, number of comparisons that is entered (or else 3), no files */
				$scope.assignment = {
					name: $scope.assignment.name,
                    description: $scope.assignment.description,
                    file: $scope.assignment.file,
					number_of_comparisons: $scope.assignment.number_of_comparisons ? $scope.assignment.number_of_comparisons : 3,
                    criteria: $scope.assignment.criteria
				};
				/* set current round #, answer #s, and total round # for preview */
				$scope.current = 1;
				$scope.firstAnsNum = 1;
				$scope.secondAnsNum = 2;
				$scope.total = $scope.assignment.number_of_comparisons;
				/* answer pair shown is dummy content, no files */
                $scope.answer1 = {
                    content: "<p>The first student answer in the pair will appear here.</p>",
                    file: null
                }
                $scope.answer2 = {
                    content: "<p>The second student answer in the pair will appear here.</p>",
                    file: null
                }
				$scope.comparisons = [];
                angular.forEach($scope.assignment.criteria, function(criterion) {
                    $scope.comparisons.push({
                        'criterion_id': criterion.id,
                        'criterion': criterion,
                        'content': '',
                        'winner_id': null
                    });
                });
				/* student view preview is comparison template */
				$scope.thePreview = $modal.open({
					templateUrl: 'modules/comparison/comparison-core.html',
					scope: $scope
				});
			}
		}
	};
});

/***** Providers *****/
module.factory(
	"AssignmentResource",
	[ "$resource", "Interceptors",
	function ($resource, Interceptors)
	{
		var url = '/api/courses/:courseId/assignments/:assignmentId';
		var ret = $resource(url, {assignmentId: '@id'},
			{
				'get': {url: url, cache: true},
				'save': {method: 'POST', url: url, interceptor: Interceptors.cache},
				'delete': {method: 'DELETE', url: url, interceptor: Interceptors.cache},
				'getAnswered': {url: '/api/courses/:id/assignments/:assignmentId/answers/count'}
			}
		);
		ret.MODEL = "Assignment";
		return ret;
	}
]);

module.factory(
	"AttachmentResource",
	[ "$resource",
	function ($resource)
	{
		var ret = $resource(
			'/api/attachment/:fileId',
			{fileId: '@file_id'}
		);
		ret.MODEL = "File";
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
module.controller("AssignmentViewController",
	["$scope", "$log", "$routeParams", "$location", "AnswerResource", "Authorize", "AssignmentResource", "AssignmentCommentResource",
			 "AttachmentResource", "ComparisonResource", "CourseResource", "required_rounds", "Session", "Toaster", "AnswerCommentResource",
             "GroupResource", "AnswerCommentType",
	function($scope, $log, $routeParams, $location, AnswerResource, Authorize, AssignmentResource, AssignmentCommentResource,
			 AttachmentResource, ComparisonResource, CourseResource, required_rounds, Session, Toaster, AnswerCommentResource,
             GroupResource, AnswerCommentType)
	{
		$scope.courseId = $routeParams['courseId'];
        $scope.AnswerCommentType = AnswerCommentType;
		var assignmentId = $scope.assignmentId = $routeParams['assignmentId'];
		var params = {
			courseId: $scope.courseId,
			assignmentId: assignmentId
		};
		var myAnsCount = 0; // for the event of deleting own answer
		$scope.allStudents = {};
		var userIds = {};
		$scope.totalNumAnswers = 0;
		$scope.answerFilters = {
			page: 1,
			perPage: 20,
			group_name: null,
			author: null,
			orderBy: null
		};
		$scope.self_evaluation_req_met = true;
		$scope.self_evaluation = 0;

		Session.getUser().then(function(user) {
			$scope.loggedInUserId = user.id;
			ComparisonResource.getComparisonAvailable(angular.extend({'userId': $scope.loggedInUserId}, params), function (ret) {
				$scope.comparisonAvailable = ret.available;
			});

            AssignmentResource.get(params, function (ret) {
                    ret.answer_start = new Date(ret.answer_start);
                    ret.answer_end = new Date(ret.answer_end);
                    ret.compare_start = new Date(ret.compare_start);
                    ret.compare_end = new Date(ret.compare_end);
                    $scope.assignment = ret;

                    $scope.criteria = ret.criteria;
                    if ($scope.criteria.length >= 1) {
                        $scope.answerFilters.orderBy = $scope.criteria[0].id;
                    }
                    $scope.reverse = true;

                    $scope.readDate = Date.parse(ret.created);

                    if ($scope.assignment.compare_end) {
                        $scope.answerAvail = $scope.assignment.compare_end;
                    } else {
                        $scope.answerAvail = $scope.assignment.answer_end;
                    }

                    ComparisonResource.count(angular.extend({'userId': $scope.loggedInUserId}, params), function (ret) {
                            $scope.compared_req_met = ret.count >= $scope.assignment.number_of_comparisons;
                            $scope.evaluation = 0;
                            if (!$scope.compared_req_met) {
                                $scope.evaluation = $scope.assignment.number_of_comparisons - ret.count;
                            }
                            // if evaluation period is set answers can be seen after it ends
                            if ($scope.assignment.compare_end) {
                                $scope.see_answers = $scope.assignment.after_comparing;
                                // if an evaluation period is NOT set - answers can be seen after req met
                            } else {
                                $scope.see_answers = $scope.assignment.after_comparing && $scope.compared_req_met;
                            }
                            var diff = $scope.assignment.answer_count - myAnsCount;
                            var evaluation_left = ((diff * (diff - 1)) / 2);
                            $scope.warning = ($scope.assignment.number_of_comparisons - ret.count) > evaluation_left;
                    });

                    // get the self evaluation if enabled in assignment
                    if ($scope.assignment.enable_self_evaluation) {
                        AnswerCommentResource.query(angular.extend({}, params, {user_ids: $scope.loggedInUserId, self_evaluation: 'only'}),
                            function (ret) {
                                $scope.self_evaluation_req_met = ret.length > 0;
                                $scope.self_evaluation = 1 - ret.length;
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
                    Toaster.reqerror("Assignment Not Found For ID " + assignmentId, ret);
                }
            );
		});

		Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId).then(function(result) {
			$scope.canManageAssignment = result;
			if ($scope.canManageAssignment) {
				GroupResource.get({'courseId': $scope.courseId}, function (ret) {
					$scope.groups = ret.objects;
				});
			}
		});
		$scope.students = {};
		CourseResource.getStudents({'id': $scope.courseId}, function (ret) {
			$scope.allStudents = ret.objects;
			$scope.students = ret.objects;
			userIds = $scope.getUserIds(ret.objects);
		});
        $scope.assignment = {};

		$scope.comments = AssignmentCommentResource.get(params);

		AssignmentResource.getAnswered({'id': $scope.courseId, 'assignmentId': assignmentId},
			function (ret) {
				myAnsCount = ret.answered;
				$scope.answered = ret.answered > 0;
			},
			function (ret) {
				Toaster.reqerror("Answers Not Found", ret);
			}
		);

        $scope.instructors = {};
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
				users[s.id] = 1;
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
				// can see if canManageAssignment OR their own answer OR public
				return $scope.canManageAssignment ||
                    answer.user_id == $scope.loggedInUserId ||
                    comment.comment_type == AnswerCommentType.public;
			}
		};

		var tab = 'answers';
		// tabs: answers, help, participation, comparisons
		$scope.setTab = function(name) {
			tab = name;
			if (name == "comparisons") {
                $scope.comparisons = AnswerResource.comparisons(params);
			}
		};
		$scope.showTab = function(name) {
			return tab == name;
		};

		// revealAnswer function shows full answer content for abbreviated answers (determined by getHeight directive)
		$scope.revealAnswer = function(answerId) {
			var thisClass = '.content.'+answerId;      // class for the answer to show is "content" plus the answer's ID
			$(thisClass).css({'max-height' : 'none'}); // now remove height restriction for this answer
			this.showReadMore = false;                 // and hide the read more button for this answer
		};

		// assignment delete function
		$scope.deleteAssignment = function(course_id, assignment_id) {
			AssignmentResource.delete({'courseId': course_id, 'assignmentId': assignment_id},
				function (ret) {
					Toaster.success("Assignment Delete Successful", "Successfully deleted assignment " + ret.id);
					$location.path('/course/'+course_id);
				},
				function (ret) {
					Toaster.reqerror("Assignment Delete Failed", ret);
					$location.path('/course/'+course_id);
				}
			);
		};

		$scope.deleteAnswer = function(answer, course_id, assignment_id, answer_id) {
			AnswerResource.delete({'courseId':course_id, 'assignmentId':assignment_id, 'answerId':answer_id},
				function (ret) {
					Toaster.success("Answer Delete Successful", "Successfully deleted answer "+ ret.id);
					var authorId = answer['user_id'];
					$scope.answers.objects.splice($scope.answers.objects.indexOf(answer), 1);
					$scope.assignment.answer_count -= 1;
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
		$scope.unflagAnswer = function(answer, course_id, assignment_id, answer_id) {
			var params = {'flagged': false};
			var resultMsg = "Answer Successfully Unflagged";
			AnswerResource.flagged({'courseId':course_id, 'assignmentId':assignment_id, 'answerId':answer_id}, params).$promise.then(
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
				{courseId: $scope.courseId, assignmentId: assignmentId, answer_ids: answer.id})
		};

		$scope.deleteComment = function(key, course_id, assignment_id, comment_id) {
			AssignmentCommentResource.delete({'courseId': course_id, 'assignmentId': assignment_id, 'commentId': comment_id},
				function (ret) {
					Toaster.success("Comment Delete Successful", "Successfully deleted comment " + ret.id);
					$scope.comments.objects.splice(key, 1);
					$scope.assignment.comment_count--;
				},
				function (ret) {
					Toaster.reqerror("Comment Delete Failed", ret);
				}
			);
		};

		$scope.deleteReply = function(answer, commentKey, course_id, assignment_id, answer_id, comment_id) {
			AnswerCommentResource.delete({'courseId': course_id, 'assignmentId': assignment_id, 'answerId': answer_id, 'commentId': comment_id},
				function (ret) {
					Toaster.success("Reply Delete Successful", "Successfully deleted reply.");
					var comment = answer['comments'].splice(commentKey, 1)[0];
					if (comment.public) {
						answer.public_comment_count--;
					} else {
						answer.private_comment_count--;
					}
					answer.comment_count--;
				},
				function (ret) {
					Toaster.reqerror("Reply Delete Failed", ret);
				}
			);
		};

		$scope.updateAnswerList = function() {
			var params = angular.merge({'courseId': $scope.courseId, 'assignmentId': assignmentId}, $scope.answerFilters);
			if (params.author != null) {
				params.author = params.author.id;
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
					GroupResource.get({'courseId': $scope.courseId, 'groupName': $scope.answerFilters.group},
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
					userIds[$scope.answerFilters.author.id] = 1;
				}
				$scope.answerFilters.page = 1;
			}
			$scope.updateAnswerList();
		};
	}
]);
module.controller("AssignmentWriteController",
	[ "$scope", "$log", "$location", "$routeParams", "$route", "AssignmentResource", "$modal", "Authorize",
			 "AssignmentCriterionResource", "CriterionResource", "required_rounds", "Toaster", "attachService",
             "AttachmentResource", "Session",
	function($scope, $log, $location, $routeParams, $route, AssignmentResource, $modal, Authorize,
			 AssignmentCriterionResource, CriterionResource, required_rounds, Toaster, attachService,
             AttachmentResource, Session)
	{
		var courseId = $routeParams['courseId'];
        //initialize assignment so this scope can access data from included form
		$scope.assignment = {criteria: []};
        $scope.availableCriteria = [];

		$scope.uploader = attachService.getUploader();
		$scope.resetName = attachService.resetName();
		$scope.recommended_evaluation = Math.floor(required_rounds / 2);

		Session.getUser().then(function(user) {
			$scope.loggedInUserId = user.id;
		});

		// DATETIMES
		// declaration
		var today = new Date();
		$scope.format = 'dd-MMMM-yyyy';
		$scope.date = {
			'astart': {'date': new Date(), 'time': new Date().setHours(0, 0, 0, 0)},
			'aend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
			'cstart': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)},
			'cend': {'date': new Date(), 'time': new Date().setHours(23, 59, 0, 0)}
		};


        // initialization method data
        if ($route.current.method == "new") {
            //want default to encourage discussion
		    $scope.assignment.students_can_reply = true;
            // default the setting to the recommended # of evaluations
		    $scope.assignment.number_of_comparisons = $scope.recommended_evaluation;

            $scope.date.astart.date.setDate(today.getDate()+1);
            $scope.date.aend.date.setDate(today.getDate()+8);
            $scope.date.cstart.date.setDate(today.getDate()+8);
            $scope.date.cend.date.setDate(today.getDate()+15);

        } else if ($route.current.method == "edit") {
		    $scope.assignmentId = $routeParams['assignmentId'];
            AssignmentResource.get({'courseId': courseId, 'assignmentId': $scope.assignmentId}).$promise.then(
                function (ret) {
                    $scope.date.astart.date = new Date(ret.answer_start);
                    $scope.date.astart.time = new Date(ret.answer_start);
                    $scope.date.aend.date = new Date(ret.answer_end);
                    $scope.date.aend.time = new Date(ret.answer_end);

                    if (ret.compare_start && ret.compare_end) {
                        ret.availableCheck = true;
                        $scope.date.cstart.date = new Date(ret.compare_start);
                        $scope.date.cstart.time = new Date(ret.compare_start);
                        $scope.date.cend.date = new Date(ret.compare_end);
                        $scope.date.cend.time = new Date(ret.compare_end)
                    } else {
                        $scope.date.cstart.date = new Date($scope.date.aend.date);
                        $scope.date.cstart.time = new Date($scope.date.aend.time);
                        $scope.date.cend.date = new Date();
                        $scope.date.cend.date.setDate($scope.date.cstart.date.getDate()+7);
                        $scope.date.cend.time = new Date($scope.date.aend.time);
                        $scope.date.cstart.date = $scope.date.cstart.date;
                        $scope.date.cend.date = $scope.date.cend.date;
                    }
                    $scope.assignment = ret;
                    $scope.compared = ret.compared;
                    if (ret.file) {
                        AttachmentResource.get({'fileId': ret.file.id}).$promise.then(
                            function (ret) {
                                $scope.assignment.uploadedFile = ret.file;

                            },
                            function (ret) {
                                Toaster.reqerror("Attachment Not Found", ret);
                            }
                        );
                    }
                },
                function () {
                    Toaster.reqerror("Assignment Not Found", "No assignment found for id "+$scope.assignmentId);
                }
            );
        }

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
		$scope.date.cstart.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.cstart.opened = true;
		};
		$scope.date.cend.open = function($event) {
			$event.preventDefault();
			$event.stopPropagation();

			$scope.date.cend.opened = true;
		};

		$scope.deleteFile = function(file_id) {
			AttachmentResource.delete({'fileId': file_id}).$promise.then(
				function () {
					Toaster.success('Attachment Delete Successful', "This attachment was successfully deleted.");
					$scope.assignment.uploadedFile = false;
				},
				function (ret) {
					Toaster.reqerror('Attachment Delete Failed', ret);
				}
			);
		};

        Authorize.can(Authorize.MANAGE, AssignmentCriterionResource.MODEL).then(function(result) {
			$scope.canManageCriteriaAssignment = result;
		});

		CriterionResource.get().$promise.then(function (ret) {
			$scope.availableCriteria = ret.objects;
			if (!$scope.assignment.criteria.length) {
				// if we don't have any criterion, e.g. new assignment, add a default one automatically
				$scope.assignment.criteria.push(_.find($scope.availableCriteria, {id: 1}));
			}
			// we need to remove the existing assignment criteria from available list
			$scope.availableCriteria = _.filter($scope.availableCriteria, function(c) {
				return !_($scope.assignment.criteria).pluck('id').includes(c.id);
			});
		});

		$scope.add = function(key) {
			// not proceed if empty option is being added
			if (key === undefined || key === null || key < 0 || key >= $scope.availableCriteria.length)
				return;
			$scope.assignment.criteria.push($scope.availableCriteria[key]);
			$scope.availableCriteria.splice(key, 1);
		};

		// remove criterion from assignment - eg. make it inactive
		$scope.remove = function(key) {
			var criterion = $scope.assignment.criteria[key];
			$scope.assignment.criteria.splice(key, 1);
			if (criterion.default == true) {
				$scope.availableCriteria.push(criterion);
			}
		};

		$scope.changeCriterion = function(criterion) {
			var modalScope = $scope.$new();
			modalScope.criterion = angular.copy(criterion);
			var modalInstance;
			var criterionUpdateListener = $scope.$on('CRITERION_UPDATED', function(event, c) {
				angular.copy(c, criterion);
				modalInstance.close();
			});
			var criterionAddListener = $scope.$on('CRITERION_ADDED', function(event, criterion) {
				$scope.assignment.criteria.push(criterion);
				modalInstance.close();
			});
			var criterionCancelListener = $scope.$on('CRITERION_CANCEL', function() {
				modalInstance.dismiss('cancel');
			});
			modalInstance = $modal.open({
				animation: true,
				template: '<criterion-form criterion=criterion></criterion-form>',
				scope: modalScope
			});
			// we need to remove the listener, otherwise on multiple click, multiple listeners will be registered
			modalInstance.result.finally(function(){
				criterionUpdateListener();
				criterionAddListener();
				criterionCancelListener();
			});
		};

		$scope.assignmentSubmit = function () {
			$scope.submitted = true;
			$scope.assignment.answer_start = combineDateTime($scope.date.astart);
			$scope.assignment.answer_end = combineDateTime($scope.date.aend);
			$scope.assignment.compare_start = combineDateTime($scope.date.cstart);
			$scope.assignment.compare_end = combineDateTime($scope.date.cend);

			// answer end datetime has to be after answer start datetime
			if ($scope.assignment.answer_start >= $scope.assignment.answer_end) {
				Toaster.error('Answer Period Error', 'Answer end time must be after answer start time.');
				$scope.submitted = false;
				return;
			} else if ($scope.assignment.availableCheck && $scope.assignment.answer_start > $scope.assignment.compare_start) {
                Toaster.error("Time Period Error", 'Please double-check the answer and evaluation period start and end times.');
                $scope.submitted = false;
                return;
			} else if ($scope.assignment.availableCheck && $scope.assignment.compare_start >= $scope.assignment.compare_end) {
                Toaster.error("Time Period Error", 'Evauluation end time must be after evauluation start time.');
                $scope.submitted = false;
                return;
            }
			// if option is not checked; make sure no compare dates are saved.
			if (!$scope.assignment.availableCheck) {
				$scope.assignment.compare_start = null;
				$scope.assignment.compare_end = null;
			}
			$scope.assignment.file_name = attachService.getName();
			$scope.assignment.file_alias = attachService.getAlias();
            AssignmentResource.save({'courseId': courseId}, $scope.assignment)
                .$promise.then(function (ret) {
                    $scope.submitted = false;
                    if ($route.current.method == "new") {
                        Toaster.success("New Assignment Created",'"' + ret.name + '" should now be listed.');
                    } else {
                        Toaster.success("Assignment Updated");
                    }
                    $location.path('/course/' + courseId);
                },
                function (ret) {
                    $scope.submitted = false;
                    if ($route.current.method == "new") {
                        Toaster.reqerror("No New Assignment Created", ret);
                    } else {
                        Toaster.reqerror("Assignment Not Updated", ret);
                    }
                }
            );
		};
	}
]);

// End anonymous function
})();
