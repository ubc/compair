var myApp = angular.module('myApp', ['ngResource', 'ngTable']);

//Global Variables

myApp.factory('judgeService', function($resource) {
	return $resource( '/script/:scriptId' );
});

myApp.factory('loginService', function($resource) {
	return $resource( '/login' );
});

myApp.factory('userService', function($resource) {
	return $resource( '/user' );
});

myApp.factory('pickscriptService', function($resource) {
	return $resource( '/pickscript/:qid' );
});

myApp.factory('rankService', function($resource) {
	return $resource( '/ranking/:qid' );
});

myApp.factory('courseService', function($resource) {
	return $resource( '/course' );
});

myApp.factory('questionService', function($resource) {
	return $resource( '/question/:cid' );
});

myApp.factory('answerService', function($resource) {
	return $resource( '/answer/:qid', {}, { put: {method: 'PUT'} } );
});

myApp.factory('quickService', function($resource) {
	return $resource( '/randquestion' );
});

myApp.factory('enrollService', function($resource) {
	return $resource( '/enrollment/:id' );
});

myApp.factory('commentAService', function($resource) {
	return $resource( '/answer/:id/comment' );
});

myApp.factory('commentQService', function($resource) {
	return $resource( '/question/:id/comment' );
});

myApp.config( function ($routeProvider) {
	$routeProvider
		.when ('/', 
			{
				controller: IndexController,
				templateUrl: 'intro.html'
			})
		.when ('/judgepage/:questionId',
			{
				controller: JudgepageController,
				templateUrl: 'judgepage.html'
			})
		.when ('/login',
			{
				controller: LoginController,
				templateUrl: 'login.html'
			})
		.when ('/createuser',
			{
				controller: UserController,
				templateUrl: 'createuser.html'
			})
		.when ('/rankpage',
			{
				controller: RankController,
				templateUrl: 'rankpage.html'
			})
		.when ('/coursepage',
			{
				controller: CourseController,
				templateUrl: 'coursepage.html'
			})
		.when ('/questionpage/:courseId',
			{
				controller: QuestionController,
				templateUrl: 'questionpage.html'
			})
		.when ('/createquestion',
			{
				controller: AskController,
				templateUrl: 'createquestion.html'
			})
		.when ('/answerpage/:questionId',
			{
				controller: AnswerController,
				templateUrl: 'answerpage.html'
			})
		.when ('/enrollpage/:courseId',
			{
				controller: EnrollController,
				templateUrl: 'enrollpage.html'
			})
		.when ('/quickjudge',
			{
				controller: QuickController,
				templateUrl: 'judgepage.html'
			})
		.otherwise({redirectTo: '/'});
});

function IndexController($scope, loginService) {
	var login = loginService.get( function() {
		login = login.username;
		if (login) {
			$scope.check = true;
			$scope.login = login;
		} else {
			$scope.check = false;
		}
	});
	$scope.$on("LOGGED_IN", function(event, username) {
		$scope.check = true;
		$scope.login = username;
	});
}

function QuickController($scope, $location, judgeService, pickscriptService, quickService) {
	var retval = quickService.get( function() {
		if (retval.question) {
			questionId = retval.question;
			$location.path('/judgepage/' + questionId);
		} else {
			$location.path('/coursepage');
			alert('None of the questions has enough new answers. Please come back later');
		}
	});
}

function JudgepageController($scope, $routeParams, $location, judgeService, pickscriptService) {
	var questionId = $routeParams.questionId;
	if (questionId == 0) {
		$location.path('/coursepage');
		return;
	}
	var sidl;
	var sidr;
	var winner;
	$scope.getscript = function() {
		var retval = pickscriptService.get( {qid: questionId}, function() {
			$scope.course = retval.course;
			$scope.cid = retval.cid;
			$scope.question = retval.question;
			if (retval.sidl) {
				sidl = retval.sidl;
				sidr = retval.sidr;
			} else {
				alert( 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later' );
				$location.path('/coursepage');
				//$location.path('/questionpage/' + courseId);
				return;
			}
			var script1 = judgeService.get( {scriptId:sidl}, function() {
					content = script1.content;
					$scope.scriptl = content;
			});
			var script2 = judgeService.get( {scriptId:sidr}, function() {
					content = script2.content;
					$scope.scriptr = content;
			});
		});
	};
	$scope.getscript();
	$scope.submit = function() {
		if ($scope.pick == 'left') {
			winner = sidl;
		} else if ($scope.pick == 'right') {
			winner = sidr;
		} else {
			alert('Pick a side');
			return;
		}
		input = {"sidl": sidl, "sidr": sidr};
		var temp = judgeService.save( {scriptId:winner}, input, function() {
			alert(temp.msg);
			$location.path('/questionpage');
		});
	};
}

function LoginController($rootScope, $scope, $location, loginService) {
	$scope.submit = function() {
		if ( !($scope.username && $scope.password) ) {
			$scope.msg = 'Please provide a username and a password';
			return '';
		}
		input = {"username": $scope.username, "password": $scope.password};
		var user = loginService.save( input, function() {
			$scope.msg = user.msg;
			if (!$scope.msg) {
				$rootScope.$broadcast("LOGGED_IN", $scope.username); 
				$location.path('/coursepage');
			}
		});
	};
}

function UserController($rootScope, $scope, $location, userService) {
	$scope.usertypes = ['Student', 'Teacher'];
	$scope.submit = function() {
		if ($scope.password != $scope.retypepw) {
			return '';
		}
		input = {"username": $scope.username, "password": $scope.password, "usertype": $scope.usertype};
		var user = userService.save( input, function() {
			$scope.flash = user.flash;
			if (!user.msg && !$scope.flash) {
				$rootScope.$broadcast("LOGGED_IN", $scope.username); 
				$location.path('/coursepage');
			}
			return '';
		});
	};
}

function RankController($scope, $resource) {
	var retval = $resource('/ranking').get( function() {
		$scope.scripts = retval.scripts;
	});
}

function CourseController($scope, courseService, loginService) {
	// the property by which the list of courses will be sorted
	$scope.orderProp = 'name';

	var login = loginService.get( function() {
		$scope.login = login.username;
		type = login.usertype;
		if (type && (type=='Teacher' || type=='Admin')) {
			$scope.instructor = true;
		} else {
			$scope.instructor = false;
		}
	});
	var courses = courseService.get( function() {
		$scope.courses = courses.courses;
	});
	$scope.submit = function() {
		input = {"name": $scope.course};
		var retval = courseService.save( input, function() {
			$scope.check = false;
			$scope.flash = retval.flash;
			if (!$scope.flash) {
				$scope.courses.push(retval);
			}
		});
	};
}

function QuestionController($scope, $location, $routeParams, $filter, ngTableParams, questionService, loginService) 
{
	$scope.orderProp = 'time';
	var questionData = [];

	var courseId = $routeParams.courseId; 
	if (!courseId) {
		$location.path("/coursepage");
		return;
	}
	var login = loginService.get( function() {
		if (login.username) {
			$scope.login= login.username;
			if (login.usertype == 'Teacher') {
				$scope.instructor = true;
			}
		} else {
			$scope.login = '';
		}
	});
	var retval = questionService.get( {cid: courseId}, function() {
		$scope.course = retval.course;
		$scope.questions = retval.questions;
		questionData = retval.questions;
		$scope.questionParams = new ngTableParams({
			page: 1,
			total: questionData.length,
			count: 10,
		});
	});
	$scope.submit = function() {
		input = {"title": $scope.title, "content": $scope.question};
		var msg = questionService.save( {cid: courseId}, input, function() {
			if (msg.msg) {
				// TODO: What use cases would land here?
				alert('something is wrong');
			} else {
				$scope.questions.push(msg);
			}
		});
		$scope.check = false;
	};
	$scope.delete = function(question) {
		questionId = question.id;
		var retval = questionService.delete( {cid: questionId}, function() {
			if (retval.msg) {
				alert( "You cannot delete others' questions" )
			} else {
				var index = jQuery.inArray(question, $scope.questions);
				$scope.questions.splice(index, 1);
			}
		});
	};
	$scope.judge = function(id) {
		questionId = id;
		$location.path("/judgepage");
	};
	$scope.answer = function(id) {
		questionId = id;
		$location.path("/answerpage");
	};
	$scope.$watch('questionParams', function(params) {
		var orderedData = params.sorting ? $filter('orderBy')(questionData, params.orderBy()) : questionData;

		$scope.questions = orderedData.slice(
			(params.page - 1) * params.count,
			params.page * params.count
		);
	}, true);
}

function AskController($scope, $location, questionService) {
	$scope.submit = function() {
		input = {"content": $scope.question};
		var msg = questionService.save( {cid: courseId}, input, function() {
			if (msg.msg) {
				alert('something is wrong');
			} else {
				$location.path("/questionpage");
			}
		});
	};
}

function AnswerController($scope, $routeParams, answerService, rankService, commentAService, commentQService) {
	var questionId = $routeParams.questionId; 

	$scope.orderProp = 'time';
	$scope.nextOrder = 'score';

	var retval = rankService.get( {qid: questionId}, function() {
		$scope.course = retval.course;
		$scope.cid = retval.cid;
		$scope.question = retval.question;
		$scope.scripts = retval.scripts;
		$scope.login = retval.username;
		if (retval.usertype == 'Teacher' || retval.usertype == 'Admin') {
			$scope.instructor = true;
		}
	});
	$scope.submit = function() {
		input = {"content": $scope.myanswer};
		var newscript = answerService.save( {qid: questionId}, input, function() {
			if (!newscript) {
				alert('something is wrong');
			} else {
				$scope.scripts.push(newscript);
			}
		});
		$scope.check = false;
	};
	$scope.editscript = function(script, newanswer) {
		input = {"content": newanswer};
		var retval = answerService.put( {qid: script.id}, input, function() {
			if (retval.msg != 'PASS') {
				alert('something is wrong');
				alert(retval);
			} else {
				var index = jQuery.inArray(script, $scope.scripts);
				$scope.scripts[index].content = newanswer;
			}
		});
	};
	$scope.delete = function(script) {
		if (confirm("Delete Answer?") == true) {
			var retval = answerService.delete( {qid: script.id}, function() {
				if (retval.msg != 'PASS') {
					alert('something is wrong');
					alert(retval);
				} else {
					var index = jQuery.inArray(script, $scope.scripts);
					$scope.scripts.splice(index, 1);
				}
			});
		}
	};
	$scope.getAcomments = function(script) {
		var retval = commentAService.get( {id: script.id}, function() {
			if (retval.comments) {
				script.comments = retval.comments;
			} else {
				alert('something is wrong');
			}
		});
	};
	$scope.getQcomments = function() {
		var retval = commentQService.get( {id: questionId}, function() {
			if (retval.comments) {
				$scope.questionComments = retval.comments;
			} else {
				alert('something is wrong');
			}
		});
	};
	$scope.makeAcomment = function(script, mycomment) {
		input = {"content": mycomment};
		var retval = commentAService.save( {id: script.id}, input, function() {
			if (retval.comment) {
				script.comments.push( retval.comment );
			} else {
				alert('something is wrong');
			}
		});
	};
	$scope.makeQcomment = function(myQcomment) {
		input = {"content": myQcomment};
		var retval = commentQService.save( {id: questionId}, input, function() {
			if (retval.comment) {
				$scope.questionComments.push( retval.comment );
			} else {
				alert('something is wrong');
			}
		});
	};
	$scope.delAcom = function(script, comment) {
		if (confirm("Delete Comment?") == true) {
			var retval = commentAService.delete( {id: comment.id}, function() {
				if (retval.msg != 'PASS') {
					alert('something is wrong');
				} else {
					var index = jQuery.inArray(comment, script.comments);
					script.comments.splice(index, 1);
				}
			});
		}
	};
	$scope.delQcom = function(comment) {
		if (confirm("Delete Comment?") == true) {
			var retval = commentQService.delete( {id: comment.id}, function() {
				if (retval.msg != 'PASS') {
					alert('something is wrong');
				} else {
					var index = jQuery.inArray(comment, $scope.questionComments);
					$scope.questionComments.splice(index, 1);
				}
			});
		}
	};
}

function EnrollController($scope, $routeParams, $filter, ngTableParams, enrollService) {
	var courseId = $routeParams.courseId; 
	var teacherData = [];
	var studentData = [];
	var retval = enrollService.get( {id: courseId}, function() {
		$scope.course = retval.course;
		studentData = retval.students;
		$scope.students = retval.students;
		teacherData = retval.teachers;
		$scope.teachers = retval.teachers;
		$scope.studentParams = new ngTableParams({
			page: 1,
			total: studentData.length,
			count: 10,
		});
		$scope.teacherParams = new ngTableParams({
			page: 1,
			total: teacherData.length,
			count: 10,
		});
	});
	$scope.add = function(user, type) {
		input = {"uid": user.uid};
		var retval = enrollService.save( {id: courseId}, input, function() {
			if (retval.eid) {
				if (type == 'T') {
					var index = jQuery.inArray(user, $scope.teachers);
					$scope.teachers[index].enrolled = retval.eid;
				} else if (type == 'S') {
					var index = jQuery.inArray(user, $scope.students);
					$scope.students[index].enrolled = retval.eid;
				}
			} else {
				alert('something is wrong');
			}
		});
	};
	$scope.drop = function(user, type) {
		var retval = enrollService.delete( {id: user.enrolled}, function() {
			if (retval.msg != 'PASS') {
				alert('something is wrong');
			} else {
				if (type == 'T') {
					var index = jQuery.inArray(user, $scope.teachers);
					$scope.teachers[index].enrolled = '';
				} else if (type == 'S') {
					var index = jQuery.inArray(user, $scope.students);
					$scope.students[index].enrolled = '';
				}
			}
		});
	};
	$scope.$watch('teacherParams', function(params) {
		var orderedData = params.sorting ? $filter('orderBy')(teacherData, params.orderBy()) : teacherData;
		
		$scope.teachers = orderedData.slice(
			(params.page - 1) * params.count,
			params.page * params.count
		);
	}, true);
	$scope.$watch('studentParams', function(params) {
		var orderedData = params.sorting ? $filter('orderBy')(studentData, params.orderBy()) : studentData;

		$scope.students = orderedData.slice(
			(params.page - 1) * params.count,
			params.page * params.count
		);
	}, true);
}

myApp.directive('backButton', function(){
    return {
      restrict: 'A',

      link: function(scope, element, attrs) {
        element.bind('click', goBack);

        function goBack() {
          history.back();
          scope.$apply();
        }
      }
    }
});

myApp.directive('jqte', function() {
	return function(scope, element, attrs)
	{
		// convert the given element, presumably a text area, into a jqueryte
		// wysiwyg text editor
		element.jqte({
			// event callback that tells angularjs when a user is typing stuff
			// into the text area by updating the ng-model binding
			change: function() 
				{
					if (!scope.$$phase) 
					{ // prevent digest already in progress err on init
						scope.$apply(function() 
							{ scope[attrs.ngModel] = element.val(); }); 
					}
				}
		});
		// On initial page load, we haven't received data from the services yet
		// so jqte will just create an empty textarea.  This watch will
		// properly initialize the value shown in the jqte created textarea
		// once the model has been properly loaded from services.
		// Can't figure out how to remove the watch after the init, the standard
		// way of using the returned unwatch function doesn't seem to work.
		scope.$watch(attrs.ngModel, 
			function (newVal, oldVal) 
			{ 
				if (oldVal == undefined && newVal != undefined)
				{ // we finally got an actual value
					element.jqteVal(newVal); // initialize jqte textarea
				}
			} 
		);

	};
});
