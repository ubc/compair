var myApp = angular.module('myApp', ['flash', 'ngRoute', 'ngResource', 'ngTable', 'http-auth-interceptor', 'ngCookies', 'ngUpload', '$strap.directives']);

//Global Variables

myApp.factory('installService', function($resource) {
	return $resource( '/install' );
});

myApp.factory('createAdmin', function($resource) {
	return $resource( '/admin' );
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

myApp.factory('roleService', function($resource) {
	return $resource( '/roles' );
});

myApp.factory('userService', function($resource) {
	return $resource( '/user/:uid', {}, { put: {method: 'PUT'} } );
});

myApp.factory('allUserService', function($resource) {
	return $resource( '/allUsers' );
});

myApp.factory('pickscriptService', function($resource) {
	return $resource( '/pickscript/:qid/:sidl/:sidr', {sidl: 0, sidr: 0} );
});

myApp.factory('rankService', function($resource) {
	return $resource( '/ranking/:qid' );
});

myApp.factory('courseService', function($resource) {
	return $resource( '/course' );
});

myApp.factory('questionService', function($resource) {
	return $resource( '/question/:cid', {}, { put: {method: 'PUT'} } );
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

myApp.factory('passwordService', function($resource) {
	return $resource( '/password/:uid' );
});

myApp.factory('flashService', function(flash) {
	return {
		flash: function (type, msg) {
			type = 'alert alert-' + type + ' text-center';
			flash([{ level: type, text: msg}]);
		}		
	};
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
		.when ('/userprofile/:userId',
			{
				controller: ProfileController,
				templateUrl: 'userprofile.html'
			})
		.when('/classimport',
			{
				controller: ImportController,
				templateUrl: 'classimport.html'
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

function InstallController($rootScope, $scope, $location, $cookieStore, flashService, installService, createAdmin, isInstalled) {
	$rootScope.breadcrumb = ['Installer'];
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
		if ($scope.email == undefined || $scope.email == '') {
			$scope.email = undefined;
		} else if (!re.exec($scope.email)) {
			$scope.formaterr = true;
			return;
		}
		input = {"username": $scope.username, "password": $scope.password, "usertype": 'Admin', "email": $scope.email, "firstname": $scope.firstname, "lastname": $scope.lastname, "display": $scope.display};
		var user = createAdmin.save( input, function() {
			$scope.flash = user.flash;
			if (!user.msg && !$scope.flash) {
				$scope.done = true;
				flashService.flash('success', 'Administrator created. Click Login to try logging in with your administrator account');
				return '';
			} else if ($scope.flash) {
				flashService.flash ('error', $scope.flash);
			}
			return '';
		});
	}
}

function IndexController($rootScope, $scope, $location, $cookieStore, loginService, logoutService, isInstalled) {
	$rootScope.intro = introJs();

	var allBreadcrumbs = [];
	$scope.breadcrumbs = [];
	$scope.dropdown = [
		{
			"text": "User Profile",
			"href": "#/userprofile/0"
		},
		{
			"text": "Log Out",
			"href": "#",
			"click": "logout()",
		},
	];
	var login = loginService.get( function() {
		$scope.usertype = login.usertype;
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
	$scope.$on("LOGGED_IN", function(event, user) {
		$scope.check = true;
		$scope.login = user.display;
		$scope.usertype = user.usertype;
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
	$scope.$on("NEW_CRUMB", function(event, crumb) {
		if (crumb.from === 'judgepage') {
			$scope.breadcrumbs = allBreadcrumbs.slice();
			$scope.activecrumb = 'Judgement Time';
			return;
		}
		for (var i = 0; i < allBreadcrumbs.length; i++) {
			if (crumb.from === allBreadcrumbs[i].from) {
				allBreadcrumbs = allBreadcrumbs.slice(0, i);
				break;
			}
		}
		$scope.breadcrumbs = allBreadcrumbs.slice();
		allBreadcrumbs.push( crumb );
		$scope.activecrumb = crumb.display;
	});
	$scope.$on("JUDGEMENT", function(event) {
		route = allBreadcrumbs[allBreadcrumbs.length - 1].route;
		$location.path( route );
	});
	var steps = '';
	$scope.$on("STEPS", function(event, val) {
		$scope.hastutorial = true;
		steps = val.steps;
		var intro = val.intro;
		steps.unshift({element: '#stepTutorial', intro: intro});
	});
	$scope.$on("NO_TUTORIAL", function(event, val) {
		$scope.hastutorial = false;
	});
	$scope.tutorial = function() {
		$rootScope.intro.setOption("steps", steps);
		$rootScope.intro.start();
	}
	//$rootScope.$watch('hastutorial', function(val) {
	//	$scope.hastutorial = val;
	//});
}

function QuickController($scope, $location, flashService, judgeService, pickscriptService, quickService) {
	var retval = quickService.get( function() {
		if (retval.question) {
			questionId = retval.question;
			$location.path('/judgepage/' + questionId);
		} else {
			$location.path('/');
			flashService.flash('error', 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later');
		}
	});
}

function JudgepageController($rootScope, $scope, $cookieStore, $routeParams, $location, flashService, judgeService, pickscriptService) {
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
			var title = retval.qtitle.length > 80 ? retval.qtitle.slice(0, 79) + '...' : retval.qtitle;
			$rootScope.breadcrumb = ['Judge', retval.course, title];
			$scope.course = retval.course;
			$scope.cid = retval.cid;
			$scope.question = retval.question;
			$scope.qtitle = retval.qtitle;
			if (retval.sidl) {
				sidl = retval.sidl;
				sidr = retval.sidr;
			} else {
				flashService.flash( 'error', 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later' );
				//$location.path('/');
				$rootScope.$broadcast("JUDGEMENT"); 
				return;
			}
			loadscripts();
			var steps = [
				{
					element: '#stepTitle',
					intro: "Question title and content",
				},
				{
					element: '#stepNext',
					intro: "Get another pair of answers from this question",
				},
				{
					element: '#stepViews',
					intro: "There are 3 different view modes. By default, it is in Versus view",
				},
				{
					element: '#stepVS',
					intro: "Display the pair side-by-side",
				},
				{
					element: '#stepLeft',
					intro: "Display the left answer only",
				},
				{
					element: '#stepRight',
					intro: "Display the right answer only",
				},
				{
					element: '#stepPick',
					intro: "Pick the winner: Right answer or left answer?",
				},
				{
					element: '#stepSubmit',
					intro: "Once you have picked a winner, submit your judgement",
				},
			];
			var intro = "You will be presented with a random pair of answers from the question. Note that your own answer will not show up and you can judge the same pair only once. Examine both answers carefully and make your judgement."
			$rootScope.$broadcast("STEPS", { "steps": steps, "intro": intro });
		});
	};
	$scope.getscript();
	$scope.submit = function() {
		if ($scope.pick == 'left') {
			winner = sidl;
		} else if ($scope.pick == 'right') {
			winner = sidr;
		} else {
			flashService.flash('error', 'Please pick a side');
			return;
		}
		input = {"sidl": sidl, "sidr": sidr};
		var temp = judgeService.save( {scriptId:winner}, input, function() {
			flashService.flash('success', temp.msg);
			$rootScope.$broadcast("JUDGEMENT"); 
		});
	};
	$scope.nextpair = function() {
		var retval = pickscriptService.get( {qid: questionId, sidl: sidl, sidr: sidr}, function() {
			if (retval.sidl) {
				sidl = retval.sidl;
				sidr = retval.sidr;
				loadscripts();
			} else if (retval.nonew) {
				flashService.flash('error', 'This is the only fresh pair in this question');
				return;
			}
		});
	};
	loadscripts = function() {
		var script1 = judgeService.get( {scriptId:sidl}, function() {
				content = script1.content;
				$scope.scriptl = content;
		});
		var script2 = judgeService.get( {scriptId:sidr}, function() {
				content = script2.content;
				$scope.scriptr = content;
		});
	};
}

function LoginController($rootScope, $cookieStore, $scope, $location, flashService, loginService, authService, isInstalled) {
	$rootScope.breadcrumb = ['Login'];
	$rootScope.$broadcast("NO_TUTORIAL", false);

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
			flashService.flash('error', 'Please provide a username and a password');
			return '';
		}
		input = {"username": $scope.username, "password": $scope.password};
		var user = loginService.save( input, function() {
			if (user.display) {
				authService.loginConfirmed();
				$rootScope.$broadcast("LOGGED_IN", user); 
				$location.path('/');
			} else {
				flashService.flash('error', 'Incorrect username or password');
			}
		});
	};
}

function UserIndexController($rootScope, $scope, $filter, $q, ngTableParams, userService, allUserService) {
	$rootScope.$broadcast("NO_TUTORIAL", false);
	$rootScope.breadcrumb = ['Users'];

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

function UserController($rootScope, $scope, $location, flashService, roleService, userService) {
	$rootScope.$broadcast("NO_TUTORIAL", false); 
	$rootScope.breadcrumb = ['Users', 'Create User'];

	retval = roleService.get(function() {
		$scope.usertypes = retval.roles;
	});
	$scope.submit = function() {
		var re = /[^@]+@[^@]+/;
		if ($scope.email == undefined || $scope.email == '') {
			$scope.email = undefined;
		} else if (!re.exec($scope.email)) {
			$scope.formaterr = true;
		}
		if ($scope.formaterr || $scope.password != $scope.retypepw) {
			return '';
		}
		
		input = {"username": $scope.username, "password": $scope.password, "usertype": $scope.role, "email": $scope.email, "firstname": $scope.firstname, "lastname": $scope.lastname, "display": $scope.display};
		var user = userService.save( {uid:0}, input, function() {
			if (user.success.length > 0) {
				flashService.flash('success', 'User created successfully');
				$location.path('/');
			} else if (!user.error[0].validation) {
				flashService.flash("error", user.error[0].msg);
			}
			return '';
		});
	};
}

function ProfileController($rootScope, $scope, $routeParams, $location, flashService, userService, passwordService) {
	$rootScope.$broadcast("NO_TUTORIAL", false);
	$rootScope.breadcrumb = ['Users', 'Edit Profile']; 

	var uid = $routeParams.userId;
	var retval = userService.get( {uid: uid}, function() {
		if (retval.username) {
			$scope.username = retval.username;
			$scope.fullname = retval.fullname;
			$scope.display = retval.display;
			$scope.email = retval.email;
			$scope.usertype = retval.usertype;
			$scope.loggedType = retval.loggedType;
			$scope.loggedName = retval.loggedName;
		} else {
			flashService.flash('error', 'Invalid User');
			$location.path('/');
		}
	});
	$scope.tooltip = { "title": "Password is needed only when changing password. Otherwise, leave it blank." };
	$scope.submit = function() {
		// typing in new password when current password isn't
		if ($scope.newpassword && $scope.oldpassword == '') {
			return;
		}
		if ($scope.newpassword != $scope.newretypepw) {
			return;
		}
		var re = /[^@]+@[^@]+/;
		if ($scope.newemail == '') {
			$scope.newemail = undefined;
		} else if (!re.exec($scope.newemail) && $scope.newemail) {
			$scope.formaterr = true;
			return;
		} 
		var password = undefined;
		if ($scope.newpassword != '' && $scope.newpassword != '') {
			password = {"old": $scope.oldpassword, "new": $scope.newpassword};
		}
		input = {"display": $scope.newdisplay, "email": $scope.newemail, "password": password};
		var retval = userService.put( {uid: uid}, input, function() {
			$scope.flash = retval.flash;
			if (retval.msg) {
				$scope.edit = false;
				$scope.submitted = false;
				$scope.email = $scope.newemail;
				$scope.display = $scope.newdisplay;
				// broadcast only when the new display name is yours
				if ($scope.loggedName == $scope.username) {
					$rootScope.$broadcast("LOGGED_IN", {"display": $scope.newdisplay, "usertype": retval.usertype}); 
				}
			} else {
				flashService.flash('error', 'Your profile was unsuccessfully updated.');
			}
		});
	};
	$scope.resetpw = function() {
		var retval = passwordService.get( {uid:uid}, function() {
			resetpassword = retval.resetpassword
			if (resetpassword) {
				$scope.resetpassword = resetpassword;
			} else {
				flashService.flash('error', 'Could not reset password.');
			}
		});
	};
}

function RankController($rootScope, $scope, $resource) {
	$rootScope.breadcrumb = ['Ranking'];
	var retval = $resource('/ranking').get( function() {
		$scope.scripts = retval.scripts;
	});
}

function CourseController($rootScope, $scope, $cookieStore, courseService, loginService) {
	// the property by which the list of courses will be sorted
	$scope.orderProp = 'name';
	$rootScope.breadcrumb = ['Courses'];

	var login = loginService.get( function() {
		type = login.usertype;
		if (type && (type=='Teacher' || type=='Admin')) {
			$scope.instructor = true;
		} else {
			$scope.instructor = false;
		}
	});
	var courses = courseService.get( function() {
		var steps = [];
		var intro = '';
		$scope.courses = courses.courses;
		if ( $scope.instructor ) {
			steps = [
				{
					element: '#step1',
					intro: 'Create a new course',
					position: 'left',
				},
				{
					element: '#step2',
					intro: "Go to Question Page to view questions and create questions",
				},
				{
					element: '#step3',
					intro: "Go to Enrol Page to enrol students or drop students",
				},
				{
					element: "#step4",
					intro: "Go to Import Page to import students from a file",
				},
			];
			intro = "Lists all the courses you are enrolled in. As an instructor, creating a new course is also an option. From here you can go to Question Page, Enrolment Page, or Import Page.";
		} else {
			steps = [
				{
					element: '#step2',
					intro: "Go to Question Page to view questions and create question",
				},
			];
			intro = "Lists all the courses you are enrolled in. From here, you can go to Question Page.";
		}
		if ( courses.courses.length < 1 ) {
			steps = [];
		}
		$rootScope.$broadcast("STEPS", {"steps": steps, "intro": intro});
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

function QuestionController($rootScope, $scope, $location, $routeParams, $filter, flashService, ngTableParams, questionService, loginService) 
{
	$scope.orderProp = 'time';
	$scope.newQuestion = '';
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
		}
	});

	$scope.searchFilter = function (obj) {
		var re = new RegExp($scope.search, 'i');
		return !$scope.search || re.test(obj.title) || re.test(obj.content);
	};

	var retval = questionService.get( {cid: courseId}, function() {
		$scope.course = retval.course;
		$scope.questions = retval.questions;
		questionData = retval.questions;
		$scope.questionParams = new ngTableParams({
			page: 1,
			total: questionData.length,
			count: 10,
		});
		$rootScope.breadcrumb = [retval.course, 'Questions'];
		var steps = [
				{
					element: '#stepNav',
					intro: 'Create a question',
					position: 'left',
				}
		];
		if ( retval.questions.length > 0 ) {
			var steps2 = [
				{
					element: '#stepTitle',
					intro: "Question's title and content which can be displayed by clicking Show",
				},
				{
					element: '#stepAnswer',
					intro: "Go to Answer Page to submit answers and view answers submitted by others",
				},
				{
					element: '#stepJudge',
					intro: "Go to Judge Page to judge submitted answers",
				},
			];
			steps = steps.concat(steps2);
		}
		var intro = "All the questions for this course are listed here. You can create a question or answer existing questions by going to Answer Page. You can also access Judge Page from this page.";
		$rootScope.$broadcast("STEPS", {"steps": steps, "intro": intro});
	});
	$scope.previewText = function() {
		$scope.preview = angular.element("div#myquestion").html();
		$scope.question = $scope.preview; // update ng-model
	}
	$scope.submit = function() {
		$scope.question = angular.element("div#myquestion").html();
		newstring = angular.element("div#myquestion").text();
		if (!$scope.title || !newstring) {
			return ''
		}
		input = {"title": $scope.title, "content": $scope.question};
		var msg = questionService.save( {cid: courseId}, input, function() {
			if (msg.msg) {
				// TODO: What use cases would land here? eg. validation error
				// alert('something is wrong');
			} else {
				$scope.questions.push(msg);
				$scope.check = false;
				// reset the form
				$scope.title = '';
				$scope.question = '';
				$scope.submitted = '';
				$scope.preview = '';
				flashService.flash('success', "The question has been successfully added.");
			}
		});
	};
	$scope.editquestion = function(newtitle, newquestion, question) {
		newquestion = angular.element("#question"+question.id).html();
		newstring = angular.element("#question"+question.id).text(); // ignore tags
		input = {"title": newtitle, "content": newquestion};
		if (!newtitle || !newstring) {
			return '';
		}
		var retval = questionService.put( {cid: question.id}, input, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('error', 'Please submit a question.');
			} else {
				var index = jQuery.inArray(question, $scope.questions);
				$scope.questions[index].title = newtitle;
				$scope.questions[index].content = newquestion;
				flashService.flash('success', 'The question has been successfully modified.');
			}
		});
	};
	$scope.remove = function(question) {
		questionId = question.id;
		if (confirm("Delete Answer?") == true) {
			var retval = questionService.remove( {cid: questionId}, function() {
				if (retval.msg) {
					flashService.flash( "error", "You cannot delete others' questions" )
				} else {
					var index = jQuery.inArray(question, $scope.questions);
					$scope.questions.splice(index, 1);
					flashService.flash('success', "The question has been successfully deleted.");
				}
			});
		}
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

function AnswerController($rootScope, $scope, $routeParams, $http, flashService, answerService, rankService, commentAService, commentQService) {
	$rootScope.breadcrumb = ['Course', 'Question', 'Answer'];
	var questionId = $routeParams.questionId; 

	$scope.orderProp = 'time';
	$scope.nextOrder = 'score';
	
	$scope.newScript = '';

	var steps = [
		{
			element: '#stepTitle',
			intro: "Title and content of the question",
		},
		{
			element: '#stepAnswer',
			intro: "Submit your answer",
		},
		{
			element: '#stepJudge',
			intro: "Go to Judge Page to judge submitted answers",
		},
		{
			element: '#stepOrder',
			intro: "Re-order answers by Time or by Score. By default, answers are ordered by Time",
		},
	];
	var intro = "All the subitted answers for the question are listed here. Submit your answer or judge others' answers by going to Judge Page. You can also leave comments on the question or any of the submitted answers.";
	$rootScope.$broadcast("STEPS", {"steps": steps, "intro": intro}); 

	var retval = rankService.get( {qid: questionId}, function() {
		$scope.qid = questionId;
		$scope.course = retval.course;
		$scope.cid = retval.cid;
		$scope.qtitle = retval.qtitle;
		$scope.question = retval.question;
		$scope.scripts = retval.scripts;
		$scope.login = retval.display;
		if (retval.usertype == 'Teacher' || retval.usertype == 'Admin') {
			$scope.instructor = true;
		}
		var title = retval.qtitle.length > 80 ? retval.qtitle.slice(0, 79) + '...' : retval.qtitle;
		$rootScope.breadcrumb = [retval.course, title, 'Answers'];
	});
	$scope.submit = function() {
		$scope.myanswer = angular.element("#myanswer").html();
		newstring = angular.element("#myanswer").text();
		if (!newstring) {
			return '';
		}
		input = {"content": $scope.myanswer};
		var newscript = answerService.save( {qid: questionId}, input, function() {
			if (newscript.msg) {
				flashService.flash('error', 'Please submit a valid answer.');
			} else {
				$scope.scripts.push(newscript);
				$scope.myanswer = '';
				$scope.submitted = false;
				$scope.check = false;
			}
		});
	};
	$scope.previewText = function() {
		$scope.preview = angular.element("div#myanswer").html();
		$scope.myanswer = $scope.preview;
	}
	$scope.editscript = function(script, newanswer) {
		newanswer = angular.element("#editScript"+script.id).html();
		newstring = angular.element("#editScript"+script.id).text();
		if (!newstring) {
			return '';
		}
		input = {"content": newanswer};
		var retval = answerService.put( {qid: script.id}, input, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('error', 'Please submit an answer.');
			} else {
				var index = jQuery.inArray(script, $scope.scripts);
				$scope.scripts[index].content = newanswer;
				flashService.flash('success', 'The answer has been successfully modified.');
			}
		});
	};
	$scope.remove = function(script) {
		if (confirm("Delete Answer?") == true) {
			var retval = answerService.remove( {qid: script.id}, function() {
				if (retval.msg != 'PASS') {
					flashService.flash('error', 'The answer was unsuccessfully deleted.');
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
				flashService.flash('error', 'The comments could not be found.');
			}
		});
	};
	$scope.getQcomments = function() {
		var retval = commentQService.get( {id: questionId}, function() {
			if (retval.comments) {
				$scope.questionComments = retval.comments;
			} else {
				flashService.flash('error', 'The comments could not be found.');
			}
		});
	};
	$scope.makeAcomment = function(script, mycomment) {
		mycomment = angular.element("#newacom"+script.id).html();
		newstring = angular.element("#newacom"+script.id).text();
		if (!newstring) {
			return '';
		}
		input = {"content": mycomment};
		var retval = commentAService.save( {id: script.id}, input, function() {
			if (retval.comment) {
				script.comments.push( retval.comment );
				flashService.flash('success', 'The comment has been successfully added.');
			} else {
				//alert('something is wrong');
				flashService.flash('error', 'Please submit a valid comment.');
			}
		});
	};
	$scope.makeQcomment = function(myQcomment) {
		myQcomment = angular.element("#myQcomment").html();
		newstring = angular.element("#myQcomment").text();
		input = {"content": myQcomment};
		if (!newstring) {
			return '';
		}
		var retval = commentQService.save( {id: questionId}, input, function() {
			if (retval.comment) {
				$scope.questionComments.push( retval.comment );
				$scope.myQcomment = '';
				$scope.lqcomm = false;
				flashService.flash('success', 'The comment has been successfully added');
			} else {
				//alert('something is wrong');
			}
		});
	};
	$scope.delAcom = function(script, comment) {
		if (confirm("Delete Comment?") == true) {
			var retval = commentAService.remove( {id: comment.id}, function() {
				if (retval.msg != 'PASS') {
					flashService.flash('error', 'The comment was unsuccessfully deleted.');
				} else {
					var index = jQuery.inArray(comment, script.comments);
					script.comments.splice(index, 1);
				}
			});
		}
	};
	$scope.delQcom = function(comment) {
		if (confirm("Delete Comment?") == true) {
			var retval = commentQService.remove( {id: comment.id}, function() {
				if (retval.msg != 'PASS') {
					flashService.flash('error', 'The comment was unsuccessfully deleted.');
				} else {
					var index = jQuery.inArray(comment, $scope.questionComments);
					$scope.questionComments.splice(index, 1);
				}
			});
		}
	};
	$scope.editQcom = function(comment, newcontent) {
		console.log('in editQcom');
		newcontent = angular.element("#editqcom"+comment.id).html();
		newstring = angular.element("#editqcom"+comment.id).text();
		if (!newstring) {
			return '';
		}
		input = {"content": newcontent};
		var retval = commentQService.put( {id: comment.id}, input, function() {
			if (retval.msg != 'PASS') {
				// can't seem to use regular span error messages
				// causes the edit toggle not to close if the edit is successful
				flashService.flash('error', 'Please submit a comment.');
			} else {
				var index = jQuery.inArray(comment, $scope.questionComments);
				$scope.questionComments[index].content = newcontent;
				flashService.flash('success', 'The comment has been successfully modified');
			}
		});
	};
	$scope.editAcom = function(script, comment, newcontent) {
		newcontent = angular.element("#editacom"+comment.id).html();
		newstring = angular.element("#editacom"+comment.id).text();
		if (!newstring) {
			return '';
		}
		input = {"content": newcontent};
		var retval = commentAService.put( {id: comment.id}, input, function() {
			if (retval.msg != 'PASS') {
				//alert('something is wrong');
				flashService.flash('error', 'Please submit a valid comment');
			} else {
				var index = jQuery.inArray(comment, script.comments);
				script.comments[index].content = newcontent;
				flashService.flash('success', 'The comment has been successfully added.');
			}
		});
	};
}

function EnrollController($rootScope, $scope, $routeParams, $filter, flashService, ngTableParams, enrollService) {
	$rootScope.$broadcast("NO_TUTORIAL", false); 

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
			$liveFiltering: true,
			page: 1,
			total: teacherData.length,
			count: 10,
		});
		$rootScope.breadcrumb = [retval.course, 'Enrol']
	});
	$scope.add = function(user, type) {
		input = {"uid": user.uid};
		var retval = enrollService.save( {id: courseId}, input, function() {
			if (retval.success.length > 0) {
				if (type == 'T') {
					var index = jQuery.inArray(user, $scope.teachers);
					$scope.teachers[index].enrolled = retval.success[0].eid;
				} else if (type == 'S') {
					var index = jQuery.inArray(user, $scope.students);
					$scope.students[index].enrolled = retval.success[0].eid;
				}
			} else {
				flashService.flash('error', 'The user was unsuccessfully enrolled.');
			}
		});
	};
	$scope.drop = function(user, type) {
		var retval = enrollService.remove( {id: user.enrolled}, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('error', 'The user was unsuccessfully dropped.');
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
			orderedData = params.filter ? $filter('filter')(orderedData, params.filter) : orderedData;

			params.total = orderedData.length;
		
			$scope.teachers = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
	}, true);
	$scope.$watch('studentParams', function(params) {
		if (params) {
			var orderedData = params.sorting ? $filter('orderBy')(studentData, params.orderBy()) : studentData;
			orderedData = params.filter ? $filter('filter')(orderedData, params.filter) : orderedData;

			params.total = orderedData.length;

			$scope.students = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
	}, true);
	$scope.$watch('squery', function(newValue) {
		$scope.studentParams.filter = newValue;
		$scope.studentParams.page = 1;
	}, true);
	$scope.$watch('tquery', function(newValue) {
		$scope.teacherParams.filter = newValue;
		$scope.teacherParams.page = 1;
	}, true);
}

function ImportController($rootScope, $scope, $routeParams, $http, flashService, courseService) {
	$rootScope.breadcrumb = ['Users', 'Import'];
	courses = courseService.get(function() {
		$scope.courses = courses.courses;
		var steps = [
			{
				element: '#stepBrowse',
				intro: "Choose a .txt or .csv file",
			},
			{
				element: '#stepCourses',
				intro: "Choose the target course",
			},
			{
				element: '#stepUpload',
				intro: "Click to import users to the chosen course",
			},
		];
		var intro = "As an instructor, you can import students which will enrol them to your course automatically. Read the instructions and make sure that your file follows the format.";
		$rootScope.$broadcast("STEPS", {"steps": steps, "intro": intro}); 
	});
	$scope.resultPage = false;
	$scope.uploadComplete = function(content) {
		/* angularjs is asynchronous therefore if we don't restrict messages to only
		appear after flask has done its job, we'll see an error message first
		then switches to success message if the task is successful*/
		if (content.completed && content.success && content.success.length > 0) {
			$scope.success = content.success;
			$scope.error = content.error;
			msg = content.error.length > 0 ? 'Users are successfully imported, however some users have errors.' :
				'Users are successfully imported.'
			$scope.resultPage = true;
			flashService.flash('success', msg);
		} else if(content.completed) {
			$scope.error = content.error;
			if (content.msg) {
				$scope.resultPage = false;
				flashService.flash('error', content.msg);
			} else {
				$scope.resultPage = true;
				flashService.flash('error', 'Users are unsuccessfully imported');
			}
		}
	};
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

myApp.directive('inputFocus', function() {
	return {
		restrict: 'A',
		
		link: function(scope, element, attrs) {
			angular.element(element).focus();
		}
	}
});
 
myApp.directive('halloEditor', function() {
    return {
        restrict: 'A',
        require: '?ngModel',
        link: function(scope, element, attrs, ngModel) {
            if (!ngModel) {
                return;
            }
 
            element.hallo({
               plugins: {
                 'halloformat': {'formattings': {"bold": true, "italic": true, "strikethrough": true, "underline": true}},
                 'halloheadings': [1,2,3],
                 'hallojustify' : {},
                 'hallolists': {},
               }
            });
 
            ngModel.$render = function() {
                element.html(ngModel.$viewValue || '');
            };
 
            element.on('hallomodified', function() {
                ngModel.$setViewValue(element.html());
                scope.$apply();
            });
        }
    };
});

myApp.directive("mathjaxBind", function() {
    return {
        restrict: "A",
        controller: ["$scope", "$element", "$attrs",
                function($scope, $element, $attrs) {
            $scope.$watch($attrs.mathjaxBind, function(value) {
                var $script = angular.element("<span class='renderContent'>")
                    .html(value == undefined ? "" : value);
                $element.html("");
                $element.append($script);
                MathJax.Hub.Queue(["Typeset", MathJax.Hub, $element[0]]);
            });
        }]
    };
});

myApp.directive("mathFormula", function() {
	return {
		restrict: "A",
		replace: true,
		scope: {
			equation: "@mathEquation",
			editor: "@editor",
			label: "@label"
		},
		template: '<span ng-click="add()" class="btn btn-default" mathjax-bind="label"></span>',
		controller: function($scope, $element, $attrs) {
			$scope.add = function() {
				var textarea = angular.element("div#"+$scope.editor);
				textarea.append($scope.equation);
			};
		}
	};
});

myApp.directive("mathToolbar", function() {
	return {
		restrict: "A",
		replace: false,
		scope: {
			editor: "@editor",
		},
		controller: function($scope, $element, $attrs) {
			$scope.toolbarOption = 'undefined';
		},
		templateUrl: 'mathjax/toolbar.html',
	};
});

myApp.directive("breadcrumb", function() {
	return {
		restrict: "A",
		replace: true,
		template: '<ul class="breadcrumb">' + 
			'<li ng-class="{active: $last}" ng-repeat="crumb in breadcrumb">{{ crumb }}' +
			'<span class="divider" ng-if="!$last"> > </span></li></ul>',
		scope: true
	}
});

myApp.directive("commentBlock", function() {
	return {
		restrict: "A",
		scope: {
			type: "@ctype",
			login: "@clogin",
			instructor: "@cinstructor",
			sid: "@csid",
		},
		controller: function($scope, $element, $attrs, $routeParams, flashService, commentQService, commentAService) {
			console.log($scope.type);
			console.log($scope.login);
			console.log($scope.instructor);
			console.log($scope.sid);
			var questionId = $routeParams.questionId;

			$scope.getComments = function() {
				if ($scope.type == 'Question') {
					var retval = commentQService.get( {id: questionId}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
						} else {
							flashService.flash('error', 'The comments could not be found.');
						}
					});
				} else if ($scope.type == 'Answer') {
					var retval = commentAService.get( {id: $scope.sid}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
						} else {
							flashService.flash('error', 'The comments could not be found.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question or Answer');
				}
			};
			$scope.getComments();

			$scope.makeComment = function() {
				var myComment = angular.element("#mycomment"+$scope.type).html();
				var newstring = angular.element("#mycomment"+$scope.type).text();
				var input = {"content": myComment};
				if (!newstring) {
					return '';
				}
				if ($scope.type == 'Question') {
					var retval = commentQService.save( {id: questionId}, input, function() {
						if (retval.comment) {
							$scope.anyComments.push( retval.comment );
							$scope.myComment = '';
							$scope.lcomm = false;
							flashService.flash('success', 'The comment has been successfully added');
						} else {
							flashService.flash('error', 'Please submit a valid comment.');
						}
					});
				} else if ($scope.type == 'Answer') {
					var retval = commentAService.save( {id: $scope.sid}, input, function() {
						if (retval.comment) {
							$scope.anyComments.push( retval.comment );
							$scope.myComment = '';
							$scope.lcomm = false;
							flashService.flash('success', 'The comment has been successfully added.');
						} else {
							flashService.flash('error', 'Please submit a valid comment.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question or Answer');
				}
			};

			$scope.delComment = function( comment ) {
				if ($scope.type == 'Question') {
					if (confirm("Delete Question Comment?") == true) {
						var retval = commentQService.remove( {id: comment.id}, function() {
							if (retval.msg != 'PASS') {
								flashService.flash('error', 'The comment was unsuccessfully deleted.');
							} else {
								var index = jQuery.inArray(comment, $scope.anyComments);
								$scope.anyComments.splice(index, 1);
							}
						});
					}
				} else if ($scope.type == 'Answer') {
					if (confirm("Delete Answer Comment?") == true) {
						var retval = commentAService.remove( {id: comment.id}, function() {
							if (retval.msg != 'PASS') {
								flashService.flash('error', 'The comment was unsuccessfully deleted.');
							} else {
								var index = jQuery.inArray(comment, $scope.anyComments);
								$scope.anyComments.splice(index, 1);
							}
						});
					}
				} else {
					alert('something is wrong; comment type should be either Question or Answer');
				}
			};

			$scope.editComment = function( comment ) {
				var newcontent = angular.element("#editcom"+comment.id).html();
				var newstring = angular.element("#editcom"+comment.id).text();
				if (!newstring) {
					return '';
				}
				var input = {"content": newcontent};
				if ($scope.type == 'Question') {
					var retval = commentQService.put( {id: comment.id}, input, function() {
						if (retval.msg != 'PASS') {
							// can't seem to use regular span error messages
							// causes the edit toggle not to close if the edit is successful
							flashService.flash('error', 'Please submit a comment.');
						} else {
							var index = jQuery.inArray(comment, $scope.anyComments);
							$scope.anyComments[index].content = newcontent;
							flashService.flash('success', 'The comment has been successfully modified');
						}
					});
				} else if ($scope.type == 'Answer') {
					var retval = commentAService.put( {id: comment.id}, input, function() {
						if (retval.msg != 'PASS') {
							//alert('something is wrong');
							flashService.flash('error', 'Please submit a valid comment');
						} else {
							var index = jQuery.inArray(comment, $scope.anyComments);
							$scope.anyComments[index].content = newcontent;
							flashService.flash('success', 'The comment has been successfully added.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question or Answer');
				}
			};
		},
		templateUrl: 'templates/comments.html',
	};
});
