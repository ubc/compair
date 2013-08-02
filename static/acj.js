var myApp = angular.module('myApp', ['flash', 'ngResource', 'ngTable', 'http-auth-interceptor', 'ngCookies']);

//Global Variables

myApp.factory('installService', function($resource) {
	return $resource( '/install' );
});

myApp.factory('isInstalled', function($resource) {
	return $resource( '/isinstalled' );
});

myApp.factory('judgeService', function($resource) {
	return $resource( '/script/:scriptId' );
});

myApp.factory('loginService', function($resource) {
	return $resource( '/login' );
});

myApp.factory('logoutService', function($resource) {
	return $resource( '/logout' );
});

myApp.factory('userService', function($resource) {
	return $resource( '/user', {}, { put: {method: 'PUT'} } );
});

myApp.factory('allUserService', function($resource) {
	return $resource( '/allUsers' );
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
	return $resource( '/answer/:id/comment', {}, { put: {method: 'PUT'} } );
});

myApp.factory('commentQService', function($resource) {
	return $resource( '/question/:id/comment', {}, { put: {method: 'PUT'} } );
});

myApp.config( function ($routeProvider) {
	$routeProvider
		.when ('/install', 
			{
				controller: InstallController,
				templateUrl: 'install.html'
			})
		.when ('/install2', 
			{
				controller: InstallController,
				templateUrl: 'install2.html'
			})
		.when ('/', 
			{
				controller: CourseController,
				templateUrl: 'coursepage.html'
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
		.when ('/user',
			{
				controller: UserIndexController,
				templateUrl: 'userpage.html'
			})
		.when ('/rankpage',
			{
				controller: RankController,
				templateUrl: 'rankpage.html'
			})
		.when ('/questionpage/:courseId',
			{
				controller: QuestionController,
				templateUrl: 'questionpage.html'
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
		.when ('/userprofile',
			{
				controller: ProfileController,
				templateUrl: 'userprofile.html'
			})
		.otherwise({redirectTo: '/'});
});

myApp.directive('authLogin', function($location, $cookieStore) {
	return {
		link: function(scope, elem, attrs) {
			scope.$on('event:auth-loginRequired', function() {
				$location.path('/login');
			});
			scope.$on('event:auth-loginConfirmed', function() {
				$location.path('/');
				$cookieStore.put('loggedIn', true);
			});
		}
	}
});

function InstallController($scope, $location, $cookieStore, flash, installService, userService, isInstalled) {
	var criteria = installService.get( function() {
		//$scope.username = criteria.username;
		$scope.requirements = criteria.requirements;
		$scope.username = 'root';
	});

	$scope.submit = function() {
		if ($scope.password != $scope.retypepw) {
			return '';
		}
		var re = /[^@]+@[^@]+/;
		if (!re.exec($scope.email) && $scope.email != undefined && $scope.email != '') {
			$scope.formaterr = true;
			return;
		} else {
			$scope.email = undefined;
		}
		input = {"username": $scope.username, "password": $scope.password, "usertype": 'Admin', "email": $scope.email, "firstname": $scope.firstname, "lastname": $scope.lastname, "display": $scope.display};
		var user = userService.save( input, function() {
			$scope.flash = user.flash;
			if (!user.msg && !$scope.flash) {
				$scope.done = true;
				flash('Administrator created. Click Login to try logging in with your administrator account');
				return '';
			} else if ($scope.flash) {
				flash ('error', $scope.flash);
			}
			return '';
		});
	}
}

function IndexController($scope, $location, $cookieStore, loginService, logoutService, isInstalled) {
	var login = loginService.get( function() {
		login = login.display;
		if (login) {
			$scope.check = true;
			$scope.login = login;
		} else {
			$scope.check = false;
		}
	});
	var installed = isInstalled.get( function() {
		if (!installed.installed) {
			$location.path('/install');
		}
	});
	$scope.$on("LOGGED_IN", function(event, display) {
		$scope.check = true;
		$scope.login = display;
	});
	$scope.logout = function() {
		var logout = logoutService.get( function() {
			if (logout.status) {
				$cookieStore.put('loggedIn', false);
				$scope.check = false;
				$location.path('/login');
			}
		});
	}
}

function QuickController($scope, $location, flash, judgeService, pickscriptService, quickService) {
	var retval = quickService.get( function() {
		if (retval.question) {
			questionId = retval.question;
			$location.path('/judgepage/' + questionId);
		} else {
			$location.path('/');
			flash('error', 'None of the questions has enough new answers. Please come back later');
		}
	});
}

function JudgepageController($scope, $cookieStore, $routeParams, $location, flash, judgeService, pickscriptService) {
	var questionId = $routeParams.questionId;
	if (questionId == 0) {
		$location.path('/');
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
				flash( 'error', 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later' );
				//$location.path('/');
				$location.path('/questionpage/' + $scope.cid);
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
			flash('error', 'Please pick a side');
			return;
		}
		input = {"sidl": sidl, "sidr": sidr};
		var temp = judgeService.save( {scriptId:winner}, input, function() {
			flash(temp.msg);
			$location.path('/questionpage/' + $scope.cid);
		});
	};
}

function LoginController($rootScope, $cookieStore, $scope, $location, loginService, authService, isInstalled) {
	var installed = isInstalled.get( function() {
		if (!installed.installed) {
			$location.path('/install');
		}
	});
	if ($cookieStore.get('loggedIn')) {
		$location.path('/');
	}
	$scope.submit = function() {
		if ( !($scope.username && $scope.password) ) {
			$scope.msg = 'Please provide a username and a password';
			return '';
		}
		input = {"username": $scope.username, "password": $scope.password};
		var user = loginService.save( input, function() {
			if (user.display) {
				authService.loginConfirmed();
				$rootScope.$broadcast("LOGGED_IN", user.display); 
				$location.path('/');
			} else {
				$scope.msg = 'Incorrect username or password';
			}
		});
	};
}

function UserIndexController($rootScope, $scope, $filter, $q, ngTableParams, userService, allUserService) {
	var allUsers = allUserService.get( function() {
		$scope.allUsers = allUsers.users;
		$scope.userParams = new ngTableParams({
			$liveFiltering: true,
			page: 1,
			total: $scope.allUsers.length,
			count: 10,
			sorting: {fullname: 'asc'}
		});
	});
	
	var usertypes = [{type: 'Admin'}, {type: 'Teacher'}, {type: 'Student'}];
	$scope.types = function(column) {
		var def = $q.defer(),
			arr =[],
			types = [];
		angular.forEach(usertypes, function(item) {
			if ($.inArray(item.type, arr) === -1) {
				arr.push(item.type);
				types.push({
					'id': item.type,
					'title': item.type
				});
			} 
		});
		def.resolve(types);
		return def.promise;
	};

	$scope.$watch('userParams', function(params) {
		// wait for allUsers to become a valid object
		if (params) {
			var orderedData = params.sorting ? $filter('orderBy')(allUsers.users, params.orderBy()) : allUsers.users;
			orderedData = params.filter ? $filter('filter')(orderedData, params.filter) : orderedData;

			params.total = orderedData.length;

			$scope.allUsers = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
	}, true);
}

function UserController($rootScope, $scope, $location, flash, userService) {
	$scope.usertypes = ['Student', 'Teacher'];
	$scope.submit = function() {
		if ($scope.password != $scope.retypepw) {
			return '';
		}
		var re = /[^@]+@[^@]+/;
		if ($scope.email == undefined || $scope.email == '') {
			$scope.email = undefined;
		} else if (!re.exec($scope.email)) {
			$scope.formaterr = true;
			return;
		}
		input = {"username": $scope.username, "password": $scope.password, "usertype": $scope.usertype, "email": $scope.email, "firstname": $scope.firstname, "lastname": $scope.lastname, "display": $scope.display};
		var user = userService.save( input, function() {
			$scope.flash = user.flash;
			if (!user.msg && !$scope.flash) {
				flash('User created successfully');
				$location.path('/user');
			} else if ($scope.flash) {
				flash('error', $scope.flash);
			}
			return '';
		});
	};
}

function ProfileController($rootScope, $scope, userService) {
	var retval = userService.get( function() {
		if (retval.username) {
			$scope.username = retval.username;
			$scope.fullname = retval.fullname;
			$scope.display = retval.display;
			$scope.email = retval.email;
			$scope.usertype = retval.usertype;
			$scope.password = retval.password;
		} else {
			alert('something is wrong');
		}
	});
	$scope.submit = function() {
		// typing in new password when current password isn't
		if ($scope.newpassword && $scope.oldpassword == '') {
			return;
		}
		if ($scope.newpassword != $scope.newretypepw) {
			return;
		}
		if ($scope.oldpassword) {
			$scope.password = $scope.oldpassword;
		}
		var re = /[^@]+@[^@]+/;
		if ($scope.newemail == undefined || $scope.newemail == '') {
			$scope.newemail = undefined;
		} else if (!re.exec($scope.newemail) && $scope.newemail) {
			$scope.formaterr = true;
			return;
		} 
		var newpassword = $scope.newpassword;
		if ($scope.newpassword == '' || $scope.newpassword == undefined) {
			newpassword = undefined;
		}
		input = {"display": $scope.newdisplay, "email": $scope.newemail, "password": $scope.password, "newpassword": newpassword};
		var retval = userService.put( input, function() {
			$scope.flash = retval.flash;
			if (retval.msg) {
				$scope.edit = false;
				$scope.submitted = false;
				$scope.email = $scope.newemail;
				$scope.display = $scope.newdisplay;
				$rootScope.$broadcast("LOGGED_IN", $scope.newdisplay); 
			} else {
				alert('something is wrong');
			}
		});
	};
}

function RankController($scope, $resource) {
	var retval = $resource('/ranking').get( function() {
		$scope.scripts = retval.scripts;
	});
}

function CourseController($scope, $cookieStore, courseService, loginService) {
	// the property by which the list of courses will be sorted
	$scope.orderProp = 'name';

	var login = loginService.get( function() {
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

function QuestionController($scope, $location, $routeParams, $filter, flash, ngTableParams, questionService, loginService) 
{
	$scope.orderProp = 'time';
	var questionData = [];

	var courseId = $routeParams.courseId; 
	if (!courseId) {
		$location.path("/");
		return;
	}
	var login = loginService.get( function() {
		if (login.display) {
			$scope.login= login.display;
			if (login.usertype == 'Teacher' || login.usertype == 'Admin') {
				$scope.instructor = true;
			}
		} else {
			$scope.login = '';
			alert('something is not right; user is not logged in');
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
				// TODO: What use cases would land here? eg. validation error
				// alert('something is wrong');
			} else {
				$scope.questions.push(msg);
				$scope.check = false;
				flash("The question has been successfully added.");
			}
		});
	};
	$scope.delete = function(question) {
		questionId = question.id;
		var retval = questionService.delete( {cid: questionId}, function() {
			if (retval.msg) {
				flash( "error", "You cannot delete others' questions" )
			} else {
				var index = jQuery.inArray(question, $scope.questions);
				$scope.questions.splice(index, 1);
				flash("The question has been successfully deleted.");
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
		// wait for the params object to be created
		if (params) {
			var orderedData = params.sorting ? $filter('orderBy')(questionData, params.orderBy()) : questionData;

			$scope.questions = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
	}, true);
}

function AnswerController($scope, $routeParams, flash, answerService, rankService, commentAService, commentQService) {
	var questionId = $routeParams.questionId; 

	$scope.orderProp = 'time';
	$scope.nextOrder = 'score';

	var retval = rankService.get( {qid: questionId}, function() {
		$scope.course = retval.course;
		$scope.cid = retval.cid;
		$scope.question = retval.question;
		$scope.scripts = retval.scripts;
		$scope.login = retval.display;
		if (retval.usertype == 'Teacher' || retval.usertype == 'Admin') {
			$scope.instructor = true;
		}
	});
	$scope.submit = function() {
		input = {"content": $scope.myanswer};
		var newscript = answerService.save( {qid: questionId}, input, function() {
			if (newscript.msg) {
				//alert('something is wrong');
			} else {
				$scope.scripts.push(newscript);
				$scope.check = false;
			}
		});
	};
	$scope.editscript = function(script, newanswer) {
		input = {"content": newanswer};
		var retval = answerService.put( {qid: script.id}, input, function() {
			if (retval.msg != 'PASS') {
				//alert('something is wrong');
				//alert(retval);
				flash('error', 'Please submit an answer.');
			} else {
				var index = jQuery.inArray(script, $scope.scripts);
				$scope.scripts[index].content = newanswer;
				flash('The answer has been successfully modified.');
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
				flash('The comment has been successfully added.');
			} else {
				//alert('something is wrong');
				flash('error', 'Please submit a valid comment.');
			}
		});
	};
	$scope.makeQcomment = function(myQcomment) {
		input = {"content": myQcomment};
		var retval = commentQService.save( {id: questionId}, input, function() {
			if (retval.comment) {
				$scope.questionComments.push( retval.comment );
				$scope.lqcomm = false;
				flash('The comment has been successfully added');
			} else {
				//alert('something is wrong');
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
	$scope.editQcom = function(comment, newcontent) {
		input = {"content": newcontent};
		var retval = commentQService.put( {id: comment.id}, input, function() {
			if (retval.msg != 'PASS') {
				// can't seem to use regular span error messages
				// causes the edit toggle not to close if the edit is successful
				flash('error', 'Please submit a comment.');
			} else {
				var index = jQuery.inArray(comment, $scope.questionComments);
				$scope.questionComments[index].content = newcontent;
				flash('The comment has been successfully modified');
			}
		});
	};
	$scope.editAcom = function(script, comment, newcontent) {
		input = {"content": newcontent};
		var retval = commentAService.put( {id: comment.id}, input, function() {
			if (retval.msg != 'PASS') {
				//alert('something is wrong');
				flash('error', 'Please submit a valid comment');
			} else {
				var index = jQuery.inArray(comment, script.comments);
				script.comments[index].content = newcontent;
				flash('The comment has been successfully added.');
			}
		});
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
		if (params) {
			var orderedData = params.sorting ? $filter('orderBy')(teacherData, params.orderBy()) : teacherData;
		
			$scope.teachers = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
	}, true);
	$scope.$watch('studentParams', function(params) {
		if (params) {
			var orderedData = params.sorting ? $filter('orderBy')(studentData, params.orderBy()) : studentData;

			$scope.students = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
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
