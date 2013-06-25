var myApp = angular.module('myApp', ['ngResource']);

//Global Variables
var courseId = 0;
var questionId = 0;

myApp.factory('judgeService', function($resource) {
	return $resource( 'http://localhost\\:5000/script/:scriptId' );
});

myApp.factory('loginService', function($resource) {
	return $resource( 'http://localhost\\:5000/login' );
});

myApp.factory('userService', function($resource) {
	return $resource( 'http://localhost\\:5000/user' );
});

myApp.factory('pickscriptService', function($resource) {
	return $resource( 'http://localhost\\:5000/pickscript/:qid' );
});

myApp.factory('rankService', function($resource) {
	return $resource( 'http://localhost\\:5000/ranking/:qid' );
});

myApp.factory('courseService', function($resource) {
	return $resource( 'http://localhost\\:5000/course' );
});

myApp.factory('questionService', function($resource) {
	return $resource( 'http://localhost\\:5000/question/:cid' );
});

myApp.factory('answerService', function($resource) {
	return $resource( 'http://localhost\\:5000/answer/:qid' );
});

myApp.config( function ($routeProvider) {
	$routeProvider
		.when ('/', 
			{
				controller: IndexController,
				templateUrl: 'intro.html'
			})
		.when ('/judgepage',
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
		.when ('/createcourse',
			{
				controller: CreateCourseController,
				templateUrl: 'createcourse.html'
			})
		.when ('/questionpage',
			{
				controller: QuestionController,
				templateUrl: 'questionpage.html'
			})
		.when ('/createquestion',
			{
				controller: AskController,
				templateUrl: 'createquestion.html'
			})
		.when ('/answerpage',
			{
				controller: AnswerController,
				templateUrl: 'answerpage.html'
			})
		.otherwise({redirectTo: '/'});
});

function IndexController($scope, loginService) {
	var login = loginService.get( function() {
		login = login.username;
		if (login) {
			$scope.check = true;
			$scope.login = 'Logged in as: ' + login;
		} else {
			$scope.check = false;
		}
	});
}

function JudgepageController($scope, judgeService, pickscriptService) {
	if (questionId == 0) {
		alert( 'Error: questionId == 0; invalid access point to judgepage');
		window.location = "#/";
		return;
	}
	var sidl;
	var sidr;
	var winner;
	var retval = pickscriptService.get( {qid: questionId}, function() {
		$scope.question = retval.question;
		if (retval.sidl) {
			sidl = retval.sidl;
			sidr = retval.sidr;
		} else {
			alert( 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later' );
			window.location = "#/questionpage";
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
			window.location = "#/questionpage";
		});
	};
}

function LoginController($scope, loginService) {
	$scope.submit = function() {
		if ( !($scope.username && $scope.password) ) {
			alert('You must provide both username and password');
			return;
		}
		input = {"username": $scope.username, "password": $scope.password};
		var user = loginService.save( input, function() {
			message = user.msg;
			if (message) {
				alert(message);
			} else {
				window.location = "#/coursepage";
				document.location.reload();
			}
		});
	};
}

function UserController($scope, userService) {
	$scope.usertypes = ['Student', 'Teacher'];
	$scope.submit = function() {
		if ( !$scope.username ) {
			alert('Username cannot be empty string');
			return;
		}
		if ( !$scope.password ) {
			alert('You must provide password');
			return;
		}
		if ( $scope.password != $scope.retypepw ) {
			alert('Retyped password does not match');
			return;
		}
		input = {"username": $scope.username, "password": $scope.password, "usertype": $scope.usertype};
		var user = userService.save( input, function() {
			message = user.msg;
			if (message) {
				alert(message);
			} else {
				window.location = "http://localhost:5000/static/index.html";
			}
		});
	};
}

function RankController($scope, $resource) {
	var retval = $resource('http://localhost\\:5000/ranking').get( function() {
		$scope.scripts = retval.scripts;
	});
}

function CourseController($scope, courseService) {
	var courses = courseService.get( function() {
		$scope.courses = courses.courses;
	});
	$scope.ask= function(id) {
		courseId = id;
		window.location = "#/questionpage";
	};
}

function CreateCourseController($scope, courseService) {
	$scope.submit = function() {
		input = {"name": $scope.name};
		var msg = courseService.save( input, function() {
			if (msg.msg) {
				alert('something is wrong');
			} else {
				window.location = "#/coursepage";
			}
		});
	};
}

function QuestionController($scope, questionService) {
	if (courseId == 0) {
		alert('Error: courseId == 0; invalid entry point to question page');
		window.location = "#/coursepage";
	}
	var retval = questionService.get( {cid: courseId}, function() {
		$scope.course = retval.course;
		$scope.questions = retval.questions;
	});
	$scope.ask = function() {
		$scope.check = true;
	};
	$scope.submit = function() {
		input = {"content": $scope.question};
		var msg = questionService.save( {cid: courseId}, input, function() {
			if (msg.msg) {
				alert('something is wrong');
			} else {
				QuestionController($scope, questionService);
			}
		});
		$scope.check = false;
	};
	$scope.delete = function(id) {
		questionId = id;
		var retval = questionService.delete( {cid: questionId}, function() {
			QuestionController($scope, questionService);
		});
	};
	$scope.judge = function(id) {
		questionId = id;
		window.location = "#/judgepage";
	};
	$scope.answer = function(id) {
		questionId = id;
		window.location = "#/answerpage";
	};
}

function AskController($scope, questionService) {
	$scope.submit = function() {
		input = {"content": $scope.question};
		var msg = questionService.save( {cid: courseId}, input, function() {
			if (msg.msg) {
				alert('something is wrong');
			} else {
				window.location = "#/questionpage";
			}
		});
	};
}

function AnswerController($scope, answerService, rankService) {
	var retval = rankService.get( {qid: questionId}, function() {
		$scope.question = retval.question;
		$scope.scripts = retval.scripts;
	});
	$scope.answer = function() {
		$scope.check = true;
	};
	$scope.submit = function() {
		input = {"content": $scope.myanswer};
		var msg = answerService.save( {qid: questionId}, input, function() {
			if (msg.msg) {
				alert('something is wrong');
			} else {
				AnswerController($scope, answerService, rankService);
			}
		});
		$scope.check = false;
	};
}

