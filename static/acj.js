var myApp = angular.module('myApp', ['ngResource', 'ngTable']);

//Global Variables
var questionId = 0;

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
	return $resource( '/enrollment/:cid' );
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
		.when ('/answerpage',
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
			$location.path('/judgepage');
		} else {
			window.history.back();
			alert('None of the questions has enough new answers. Please come back later');
		}
	});
}

function JudgepageController($scope, $location, judgeService, pickscriptService) {
	if (questionId == 0) {
		$location.path('/');
		return;
	}
	var sidl;
	var sidr;
	var winner;
	var retval = pickscriptService.get( {qid: questionId}, function() {
		$scope.course = retval.course;
		$scope.question = retval.question;
		if (retval.sidl) {
			sidl = retval.sidl;
			sidr = retval.sidr;
		} else {
			alert( 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later' );
			window.history.back();
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
	$scope.next = function() {
		JudgepageController($scope, judgeService, pickscriptService);
	};
}

function LoginController($rootScope, $scope, $location, loginService) {
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
				$rootScope.$broadcast("LOGGED_IN", $scope.username); 
				$location.path('/coursepage');
			}
		});
	};
}

function UserController($rootScope, $scope, $location, userService) {
	$scope.usertypes = ['Student', 'Teacher'];
	$scope.submit = function() {
		if ( !$scope.usertype ) {
			alert('Pick a usertype');
			return;
		}
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
				$rootScope.$broadcast("LOGGED_IN", $scope.username); 
				$location.path('/coursepage');
			}
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
			$scope.courses.push(retval);
		});
	};
}

function QuestionController($scope, $location, $routeParams, questionService, loginService) 
{
	$scope.orderProp = 'time';

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
	});
	$scope.submit = function() {
		input = {"content": $scope.question};
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

function AnswerController($scope, answerService, rankService) {
	$scope.orderProp = 'time';
	$scope.nextOrder = 'score';

	var retval = rankService.get( {qid: questionId}, function() {
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
		var retval = answerService.delete( {qid: script.id}, function() {
			if (retval.msg != 'PASS') {
				alert('something is wrong');
				alert(retval);
			} else {
				var index = jQuery.inArray(script, $scope.scripts);
				$scope.scripts.splice(index, 1);
			}
		});
	};
}

function EnrollController($scope, $routeParams, $filter, ngTableParams, enrollService) {
	var courseId = $routeParams.courseId; 
	var teacherData = [];
	var studentData = [];
	var retval = enrollService.get( {cid: courseId}, function() {
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
	$scope.add = function(id) {
		input = {"sid": id};
		var retval = enrollService.save( {cid: courseId}, input, function() {
			EnrollController($scope, $routeParams, enrollService);
		});
	};
	$scope.drop = function(id) {
		var retval = enrollService.delete( {cid: id}, function() {
			EnrollController($scope, $routeParams, enrollService);
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

myApp.directive('questionEditor', function() {
	return {
		link: function(scope, element, attrs) {
			new nicEditor({
				maxHeight:100, 
				onSave:function(content, id, instance) {
					scope.question = content;
					scope.$apply();
					scope.submit();
				}
			}).panelInstance('postQ');
		}
	}
});

myApp.directive('answerEditor', function() {
	return {
		link: function(scope, element, attrs) {
			new nicEditor({
				maxHeight:200,
				onSave:function(content, id, instance) {
					scope.myanswer = content;
					scope.$apply();
					scope.submit();
				}
			}).panelInstance('postA');
		}
	}
});

myApp.directive('editEditor', function() {
	return {
		link: function(scope, element, attrs) {
			new nicEditor({
				maxHeight:200,
				onSave:function(content, id, instance) {
					scope.newanswer = content;
					scope.$apply();
					scope.submit();
				}
			}).panelInstance($scope.$index);
		}
	}
});

