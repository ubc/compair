var myApp = angular.module('myApp', ['flash', 'ngRoute', 'ngResource', 'ngTable', 'http-auth-interceptor', 'ngCookies', 'ngUpload', '$strap.directives']);

//Global Variables

myApp.factory('installService', function($resource) {
	return $resource('/install');
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

myApp.factory('editcourseService', function($resource) {
	return $resource( '/editcourse/:cid', {}, { put: {method: 'PUT'} } );
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

myApp.factory('commentJService', function($resource) {
	return $resource( '/judgepage/:id/comment/:sidl/:sidr', {}, { put: {method: 'PUT'} } );
});

myApp.factory('passwordService', function($resource) {
	return $resource( '/password/:uid' );
});

myApp.factory('reviewjudgeService', function($resource) {
	return $resource( '/judgements/:qid' );
});

myApp.factory('notificationService', function($resource) {
	return $resource( '/notifications' );
});

myApp.factory('tagService', function($resource) {
	return $resource( '/managetag/:cid/:tid' );
});

myApp.factory('statisticService', function($resource) {
	return $resource( '/statistics/:cid' );
});

myApp.factory('statisticExportService', function($resource) {
	return $resource( '/statisticexport/', {}, { put: {method: 'POST'} } );
});

//used for testing
myApp.factory('resetDB', function($resource) {
	return $resource( '/resetdb' );
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
		.when ('/reviewjudge/:qid',
			{
				controller: ReviewJudgeController,
				templateUrl: 'reviewjudge.html'
			})
		.when ('/editcourse/:courseId',
			{
				controller: EditCourseController,
				templateUrl: 'editcourse.html'
			})
		.when ('/stats/:courseId',
			{
				controller: StatisticController,
				templateUrl: 'stats.html'
			})
		.when ('/statexport/:cid/:cname',
				{
			controller: StatisticExportController,
			templateUrl: 'statexport.html'
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
	};
});

function InstallController($rootScope, $scope, $location, $cookieStore, flashService, installService, createAdmin, isInstalled) {
	$rootScope.breadcrumb = [{'name':'Installer'}];
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
				flashService.flash ('danger', $scope.flash);
			}
			return '';
		});
	};
}

function IndexController($rootScope, $scope, $location, $cookieStore, loginService, logoutService, isInstalled, notificationService) {
	$rootScope.intro = introJs();

	//var allBreadcrumbs = [];
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
			"id": "logout",
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
		$scope.notifications = false;
		$scope.notificationdropdown = [];
		var notifications = notificationService.get( function() {
			if (notifications.count > 0) {
				$scope.notifications = true;
				$scope.notificationsCount = notifications.count;
				for (var i = 0; i < notifications.questions.length; i++) {
					$scope.notificationdropdown.push({
	           			"text": notifications.questions[i].title.length > 30 ? notifications.questions[i].title.slice(0, 29) + '...' : notifications.questions[i].title,
	           			"href": "#/answerpage/" + notifications.questions[i].qid
	           		});
				}
			}
		});
	});
	
	$scope.logout = function() {
		var logout = logoutService.get( function() {
			if (logout.status) {
				$cookieStore.put('loggedIn', false);
				$scope.check = false;
				$location.path('/login');
			}
		});
	};
	/*
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
	*/
	$scope.$on("JUDGEMENT", function(event) {
		route = $scope.breadcrumb[$scope.breadcrumb.length - 1].link ? $scope.breadcrumb[$scope.breadcrumb.length - 1].link : "";
		$location.path(route.replace("#/", ""));
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
	};
	//$rootScope.$watch('hastutorial', function(val) {
	//	$scope.hastutorial = val;
	//});
}

function QuickController($rootScope, $scope, $location, flashService, judgeService, pickscriptService, quickService) {
	var retval = quickService.get( function() {
		if (retval.question) {
			questionId = retval.question;
			$location.path('/judgepage/' + questionId);
		} else {
			//$location.path('/');
			flashService.flash('danger', 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later');
			$rootScope.$broadcast("JUDGEMENT");
		}
	});
}

function JudgepageController($rootScope, $scope, $cookieStore, $routeParams, $location, loginService, flashService, judgeService, pickscriptService) {
	var questionId = $routeParams.questionId;
	if (questionId == 0) {
		$location.path('/');
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
	
	var sidl;
	var sidr;
	var winner;
	$scope.getscript = function() {
		var retval = pickscriptService.get( {qid: questionId}, function() {
			//var title = retval.qtitle ? retval.qtitle.length > 80 ? retval.qtitle.slice(0, 79) + '...' : retval.qtitle : '';
			$scope.course = retval.course;
			$scope.cid = retval.cid;
			$scope.question = retval.question;
			$scope.qtitle = retval.qtitle;
			if (retval.sidl) {
				sidl = retval.sidl;
				sidr = retval.sidr;
				$scope.sidl = retval.sidl;
				$scope.sidr = retval.sidr;
			} else {
				flashService.flash( 'danger', 'Either you have already judged all of the high-priority scripts OR there are not enough answers to judge. Please come back later' );
				//$location.path('/');
				$rootScope.$broadcast("JUDGEMENT"); 
				return;
			}
			$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':retval.course,'link':'#/questionpage/' + retval.cid},{'name':'Judge','link':'#/questionpage/' + retval.cid}];
			loadscripts();
			var steps = [
				{
					element: '#stepTitle',
					intro: "Question title and content",
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
				{
					element: '#stepNext',
					intro: "Can't decide which answer is better? Get another pair of answers from this question",
				},
			];
			var intro = "You will be presented with a random pair of answers from the question. Note that your own answer will not show up and you can judge the same pair only once. Examine both answers carefully and make your judgement.";
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
			flashService.flash('danger', 'Please pick a side');
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
				$scope.sidl = retval.sidl;
				$scope.sidr = retval.sidr;
				loadscripts();
				$scope.pick = "";
			} else if (retval.nonew) {
				flashService.flash('danger', 'This is the only fresh pair in this question');
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
	$rootScope.breadcrumb = [{'name':'Login'}];
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
			flashService.flash('danger', 'Please provide a username and a password');
			return '';
		}
		input = {"username": $scope.username, "password": $scope.password};
		var user = loginService.save( input, function() {
			if (user.display) {
				authService.loginConfirmed();
				$rootScope.$broadcast("LOGGED_IN", user); 
				$location.path('/');
			} else {
				flashService.flash('danger', 'Incorrect username or password');
			}
		});
	};
}

function UserIndexController($rootScope, $scope, $filter, $q, ngTableParams, userService, allUserService) {
	$rootScope.$broadcast("NO_TUTORIAL", false);
	$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':'Users'}];

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
	$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':'Create User'}];

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
	if ($rootScope.referer && $rootScope.referer == 'enrollpage') {
		$rootScope.breadcrumb = [{'name':'Home','link':'#'}, {'name': $rootScope.refererName,'link':'#/enrollpage/'+$rootScope.refererCourseId}];
		$rootScope.referer = null;
		$rootScope.refererName = null;
		$rootScope.refererCourseId = null;
	}
	else {
		$rootScope.breadcrumb = [{'name':'Home','link':'#'}];
	}
	
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
			if ($scope.loggedType == 'Admin' && $rootScope.breadcrumb.length == 1) {
				$rootScope.breadcrumb.push({'name':'Users','link':'#/user'});
			}
			$rootScope.breadcrumb.push({'name':'Edit Profile'});	
		} else {
			flashService.flash('danger', 'Invalid User');
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
			//$scope.flash = retval.flash;
			if (retval.msg) {
				$scope.edit = false;
				$scope.submitted = false;
				$scope.email = $scope.newemail;
				$scope.display = $scope.newdisplay;
				// broadcast only when the new display name is yours
				if ($scope.loggedName == $scope.username) {
					$rootScope.$broadcast("LOGGED_IN", {"display": $scope.newdisplay, "usertype": retval.usertype}); 
				}
				flashService.flash('success', "The profile has been successfully updated.");
			} else {
				//flashService.flash('danger', 'Your profile was unsuccessfully updated.');
			}
		});
	};
	$scope.resetpw = function() {
		var retval = passwordService.get( {uid:uid}, function() {
			resetpassword = retval.resetpassword;
			if (resetpassword) {
				$scope.resetpassword = resetpassword;
			} else {
				flashService.flash('danger', 'Could not reset password.');
			}
		});
	};
}

function RankController($rootScope, $scope, $resource) {
	$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':'Ranking'}];
	var retval = $resource('/ranking').get( function() {
		$scope.scripts = retval.scripts;
	});
}

function CourseController($rootScope, $scope, $cookieStore, $location, courseService, loginService) {
	// the property by which the list of courses will be sorted
	$scope.orderProp = 'name';
	$rootScope.breadcrumb = [{'name':'Home'}];

	var login = loginService.get( function() {
		type = login.usertype;
		if (type && (type=='Teacher' || type=='Admin')) {
			$scope.instructor = true;
			$scope.admin = type=='Admin';
		} else {
			$scope.instructor = false;
		}
	
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
	$scope.redirect = function(url) {
		$location.path(unescape(url));
	};
}

function StatisticController($rootScope, $routeParams, $scope, $cookieStore, $location, $filter, statisticService, ngTableParams) {
	var cid = $routeParams.courseId;
	$scope.cid = cid;
	$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':'Statistics'}];
	
	var stats = statisticService.get({cid: cid}, function() {
		$scope.stats = stats.stats;
		$scope.coursename = stats.coursename;
		statData = stats.stats;
		
		$scope.tableParams = new ngTableParams({
	        page: 1,
	        total: statData.length,
	        count: 10,
	        sorting: {
	            name: 'asc'
	        }
	    });
	});
	
	function orderBy(item, asc, question) {
		val = (question ? item.student.questionCount : item.student.answerCount) / item.totalAnswers * 100; 
		return asc ? val : -val;
	}
	
	$scope.$watch('tableParams', function(params) {
		if (params) {
			if (params.sorting && params.orderBy().toString().indexOf("percent") > -1) {
				if (params.orderBy().toString().indexOf("+") > -1) {
					if(params.orderBy().toString().indexOf("qpercent") > -1) {
						orderedData = $filter('orderBy')(statData, function(item){return orderBy(item, true, true);});
					}
					else {
						orderedData = $filter('orderBy')(statData, function(item){return orderBy(item, true, false);});
					}
				}
				else {
					if(params.orderBy().toString().indexOf("qpercent") > -1) {
						orderedData = $filter('orderBy')(statData, function(item){return orderBy(item, false, true);});
					}
					else {
						orderedData = $filter('orderBy')(statData, function(item){return orderBy(item, false, false);});
					}
				}
			}
			else {
				orderedData = params.sorting ? $filter('orderBy')(statData, params.orderBy()) : statData;
			}
			orderedData = params.filter ? $filter('filter')(orderedData, params.filter) : orderedData;
			
			params.total = orderedData.length;
			
			$scope.stats = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
	}, true);
}

function StatisticExportController($rootScope, $routeParams, $scope, $window, statisticExportService) {
	$scope.cid = $routeParams.cid;
	$scope.cname = $routeParams.cname;
	$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':$scope.cname, 'link':'#/stats/'+$scope.cid},{'name':'Export Data'}];	
	
	$scope.question = true;
	$scope.questionTitle = true;
	$scope.questionBody = true;
	$scope.questionComments = false;
	$scope.answer = true;
	$scope.answerBody = true;
	$scope.answerComments = false;
	$scope.judgement = true;
	$scope.judgementQuestion = false;
	$scope.judgementAnswer = false;
	$scope.judgementComments = false;
	
	$scope.export = function() {
		var form = $('<form action="/statisticexport/" method="post" id="csvForm">' +
			'<input type="hidden" name="cid" value="' + $scope.cid + '" />' +
			
			'<input type="hidden" name="question" value="' + $scope.question + '" />' +
			'<input type="hidden" name="questionTitle" value="' + $scope.questionTitle + '" />' +
			'<input type="hidden" name="questionBody" value="' + $scope.questionBody + '" />' +
			'<input type="hidden" name="questionComments" value="' + $scope.questionComments + '" />' +
			
			'<input type="hidden" name="answer" value="' + $scope.answer + '" />' +
			'<input type="hidden" name="answerBody" value="' + $scope.answerBody + '" />' +
			'<input type="hidden" name="answerComments" value="' + $scope.answerComments + '" />' +
			
			'<input type="hidden" name="judgement" value="' + $scope.judgement + '" />' +
			'<input type="hidden" name="judgementQuestion" value="' + $scope.judgementQuestion + '" />' +
			'<input type="hidden" name="judgementAnswer" value="' + $scope.judgementAnswer + '" />' +
			'<input type="hidden" name="judgementComments" value="' + $scope.judgementComment + '" />' +
		'</form>');
		$('body').append(form);
		$(form).submit();
		$('#csvForm').remove();
	};
}

function EditCourseController($rootScope, $scope, $routeParams, $filter, editcourseService, tagService, ngTableParams) {
	var courseId = $routeParams.courseId; 
	$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':'Edit Course'}];

	var course = editcourseService.get({cid: courseId}, function() {
		$scope.id = course.id;
		$scope.name = course.name;
		$scope.newname = course.name;
		$scope.tags = course.tags;
		tagData = course.tags;
		
		$scope.tagParams = new ngTableParams({
			page: 1,
			total: tagData.length,
			count: 10,
			sorting: {
	            tag: 'asc'
	        }
		});
	});
	
	$scope.$watch('tagParams', function(params) {
		if (params) {
			var orderedData = params.sorting ? $filter('orderBy')(tagData, params.orderBy()) : tagData;
			orderedData = params.filter ? $filter('filter')(orderedData, params.filter) : orderedData;
			
			params.total = orderedData.length;
			
			$scope.tags = orderedData.slice(
				(params.page - 1) * params.count,
				params.page * params.count
			);
		}
	}, true);
	
	$scope.submit = function() {
		var input = {"name": $scope.newname};
		var retval = editcourseService.put({cid: $scope.id}, input, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('danger', retval.msg);
			} else {
				$scope.edit = false;
				$scope.submitted = false;
				$scope.name = $scope.newname;
				flashService.flash('success', 'The course has been successfully modified.');
			}
		});
	};
	
	$scope.removeTag = function(tid) {
		var course = tagService.remove({"cid": $scope.id, "tid": tid}, function() {
			$scope.id = course.id;
			$scope.name = course.name;
			$scope.newname = course.name;
			$scope.tags = course.tags;
			tagData = course.tags;
		});
	};
	$scope.addTag = function() {
		var input = {"cid": $scope.id, "name": $scope.newtag};
		var course = tagService.save({}, input, function() {
			$scope.id = course.id;
			$scope.name = course.name;
			$scope.newname = course.name;
			$scope.tags = course.tags;
			tagData = course.tags;
		});
	};
}

function QuestionController($rootScope, $scope, $location, $routeParams, $filter, flashService, ngTableParams, questionService, answerService, loginService) 
{
	$scope.orderProp = 'time';
	$scope.newQuestion = '';
	$scope.type = $rootScope.type ? $rootScope.type : 'quiz';
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
		for (tag in obj.tags) {
			if (re.test(obj.tags[tag])) {
				return true;
			}
		}
		return !$scope.search || re.test(obj.title) || re.test(obj.content);
	};

	var retval = questionService.get( {cid: courseId}, function() {
		$scope.course = retval.course;
		$scope.discussions = retval.questions;
		$scope.quizzes = retval.quizzes;
		$scope.tags = retval.tags;
		questionData = retval.questions;
		/*
		$scope.questionParams = new ngTableParams({
			page: 1,
			total: questionData.length,
			count: 10,
		});
		*/
		$rootScope.breadcrumb = [{'name':'Home', 'link':'#'}, {'name':retval.course, 'link':'#/questionpage/'+courseId}];
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
	};
	// preview when editing a question
	$scope.previewTextEdit = function(question) {
		$scope.previewEdit = angular.element("#question"+question.id).html();
		$scope.newquestion = $scope.previewEdit; // update ng-model
	};
	// only allow one single question to be editable at a time
	$scope.editId = -1;
	$scope.switchEdits = function(id) {
		if (id) {
			$scope.previewEdit = null;
			$scope.newquestion =  null;
		}
		$scope.editId = id ? id == $scope.editId ? -1 : id : $scope.editId;
		return $scope.editId;
	};
	$scope.submit = function() {
		$scope.question = angular.element("div#myquestion").html();
		newstring = angular.element("div#myquestion").text();
		if (!$scope.title || !newstring) {
			return '';
		}
		input = {"title": $scope.title, "content": $scope.question, "type": $scope.type, "taglist": $scope.taglist ? $scope.taglist : new Array()};
		var msg = questionService.save( {cid: courseId}, input, function() {
			if (msg.msg) {
				// TODO: What use cases would land here? eg. validation error
				// alert('something is wrong');
			} else {
				validAnswer = true;
				if ($scope.type == 'quiz') {
					$scope.myanswerq = angular.element("#myanswerq").html();
					newstring = angular.element("#myanswerq").text();
					if (!newstring) {
						return '';
					}
					input = {"content": $scope.myanswerq};
					var newscript = answerService.save( {qid: msg.id}, input, function() {
						if (newscript.msg) {
							flashService.flash('danger', 'Please submit a valid answer.');
							validAnswer = false;
						} else {
							$scope.answerq = '';
						}
					});
				}
				if (validAnswer) {
					$scope.type == 'quiz' ? $scope.quizzes.push(msg) : $scope.discussions.push(msg);
					$scope.check = false;
					// reset the form
					$scope.title = '';
					$scope.question = '';
					$scope.submitted = '';
					$scope.preview = '';
					$scope.previewEdit = '';
					flashService.flash('success', "The question has been successfully added.");
				}
			}
		});
	};
	
	$scope.editquestion = function(newtitle, newquestion, question) {
		newquestion = angular.element("#question"+question.id).html();
		newstring = angular.element("#question"+question.id).text(); // ignore html tags
		input = {"title": newtitle, "content": newquestion, "taglist": question.tmptags ? question.tmptags : new Array()};
		if (!newtitle || !newstring) {
			return '';
		}
		var retval = questionService.put( {cid: question.id}, input, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('danger', 'Please submit a question.');
			} else {
				question.tags = question.tmptags ? question.tmptags : new Array();
				if ($scope.type == 'quiz') {
					var index = jQuery.inArray(question, $scope.quizzes);
					$scope.quizzes[index].title = newtitle;
					$scope.quizzes[index].content = newquestion;
				}
				else {
					var index = jQuery.inArray(question, $scope.discussions);
					$scope.discussions[index].title = newtitle;
					$scope.discussions[index].content = newquestion;
				}
				flashService.flash('success', 'The question has been successfully modified.');
			}
		});
	};
	$scope.remove = function(question) {
		questionId = question.id;
		if (confirm("Delete Question?") == true) {
			var retval = questionService.remove( {cid: questionId}, function() {
				if (retval.msg) {
					flashService.flash( "error", "You cannot delete others' questions" );
				} else {
					if ($scope.type == 'quiz') {
						var index = jQuery.inArray(question, $scope.quizzes);
						$scope.quizzes.splice(index, 1);
					}
					else {
						var index = jQuery.inArray(question, $scope.discussions);
						$scope.discussions.splice(index, 1);
					}
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
	// TODO what does this do?
	/*
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
	*/
	// save the Rangy object for the selected hallo editor
	$scope.saveRange = function() {
		var selRange = rangy.getSelection();
		$rootScope.savedRange = selRange.rangeCount ? selRange.getRangeAt(0) : null;
	};
	
	$scope.tagActionN = function(id) {
		if (!$scope.taglist) $scope.taglist = [];
		var index = jQuery.inArray(id, $scope.taglist);
		if (index >= 0) {
			$scope.taglist.splice(index, 1);
		}
		else {
			$scope.taglist.push(id);
		}
	};
	$scope.tagActionQ = function(list, name) {
		if (!list) list = [];
		var index = jQuery.inArray(name, list);
		if (index >= 0) {
			list.splice(index, 1);
		}
		else {
			list.push(name);
		}
	};
	$scope.checkTagN = function(id) {
		return jQuery.inArray(id, $scope.taglist) >= 0;
	};
	$scope.checkTagQ = function(list, name) {
		if (list) {
			for (var i = 0; i < list.length; i++) {
				if (list[i] == name) {
					return true;
				}
			}
		}
		return false;
	};
	$scope.setType = function(type) {
		$scope.type = type;
		$rootScope.type = type;
	};
}

function AnswerController($rootScope, $scope, $routeParams, $http, flashService, answerService, rankService, commentAService, commentQService, loginService) {
	$rootScope.breadcrumb = [{'name':'Home', 'link':'#'}, {'name':'Question', 'link':''}, {'name':'Answer'}];
	var questionId = $routeParams.questionId; 

	$scope.orderProp = 'time';
	$scope.nextOrder = 'score';
	
	$scope.newScript = '';
	$scope.answered = false;

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

	var login = loginService.get( function() {
		if (login.display) {
			$scope.login = login.display;
			if (login.usertype == 'Teacher' || login.usertype == 'Admin') {
				$scope.instructor = true;
			}

		} else {
			$scope.login = '';
		}
	});
	
	var retval = rankService.get( {qid: questionId}, function() {
		$scope.qid = questionId;
		$scope.course = retval.course;
		$scope.cid = retval.cid;
		$scope.qtitle = retval.qtitle;
		$scope.question = retval.question;
		$scope.scripts = retval.scripts;
		$scope.login = retval.display;
		$scope.commentQCount = retval.commentQCount;
		$scope.authorQ = retval.authorQ;
		$scope.timeQ = retval.timeQ;
		$scope.avatarQ = retval.avatarQ;
		$scope.answered = retval.answered;
		$scope.quiz = retval.quiz;
		if (retval.usertype == 'Teacher' || retval.usertype == 'Admin') {
			$scope.instructor = true;
		}
		var title = retval.qtitle.length > 80 ? retval.qtitle.slice(0, 79) + '...' : retval.qtitle;
		$rootScope.breadcrumb = [{'name':'Home','link':'#'}, {'name':retval.course, 'link':'#/questionpage/'+retval.cid}, {'name':title, 'link':'#/answerpage/'+questionId}];
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
				flashService.flash('danger', 'Please submit a valid answer.');
			} else {
				$scope.scripts.push(newscript);
				$scope.myanswer = '';
				$scope.submitted = false;
				$scope.check = false;
				$scope.previewEdit = '';
				$scope.answered = true;
			}
		});
	};
	$scope.previewText = function() {
		$scope.preview = angular.element("div#myanswer").html();
		$scope.myanswer = $scope.preview;
	};
	// preview when editing an answer
	$scope.previewTextEdit = function(script) {
		$scope.previewEdit = angular.element("#editScript"+script.id).html();
		$scope.newanswer = $scope.previewEdit; // update ng-model
	};
	// only allow one single answer to be editable at a time
	$scope.editId = -1;
	$scope.switchEdits = function(id) {		
		if (id) {
			$scope.previewEdit = null;
			$scope.newanswer =  null;
		}
		$scope.editId = id ? id == $scope.editId ? -1 : id : $scope.editId;
		return $scope.editId;
	};
	$scope.editscript = function(script, newanswer) {
		newanswer = angular.element("#editScript"+script.id).html();
		newstring = angular.element("#editScript"+script.id).text();
		if (!newstring) {
			return '';
		}
		input = {"content": newanswer};
		var retval = answerService.put( {qid: script.id}, input, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('danger', 'Please submit an answer.');
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
					flashService.flash('danger', 'The answer was unsuccessfully deleted.');
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
				flashService.flash('danger', 'The comments could not be found.');
			}
		});
	};
	/* not used
	$scope.getQcomments = function() {
		var retval = commentQService.get( {id: questionId}, function() {
			if (retval.comments) {
				$scope.questionComments = retval.comments;
			} else {
				flashService.flash('danger', 'The comments could not be found.');
			}
		});
	};
	*/
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
				flashService.flash('danger', 'Please submit a valid comment.');
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
					flashService.flash('danger', 'The comment was unsuccessfully deleted.');
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
					flashService.flash('danger', 'The comment was unsuccessfully deleted.');
				} else {
					var index = jQuery.inArray(comment, $scope.questionComments);
					$scope.questionComments.splice(index, 1);
				}
			});
		}
	};
	$scope.editQcom = function(comment, newcontent) {
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
				flashService.flash('danger', 'Please submit a comment.');
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
				flashService.flash('danger', 'Please submit a valid comment');
			} else {
				var index = jQuery.inArray(comment, script.comments);
				script.comments[index].content = newcontent;
				flashService.flash('success', 'The comment has been successfully added.');
			}
		});
	};
	
	// save the Rangy object for the selected hallo editor
	$scope.saveRange = function() {
		var selRange = rangy.getSelection();
		$rootScope.savedRange = selRange.rangeCount ? selRange.getRangeAt(0) : null;
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
			page: 1,
			total: teacherData.length,
			count: 10,
		});
		$rootScope.breadcrumb = [{'name':'Home','link':'#'}, {'name':retval.course}];
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
				flashService.flash('danger', 'The user was unsuccessfully enrolled.');
			}
		});
	};
	$scope.drop = function(user, type) {
		var retval = enrollService.remove( {id: user.enrolled}, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('danger', 'The user was unsuccessfully dropped.');
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
		if ($scope.studentParams) {
			$scope.studentParams.filter = newValue;
			$scope.studentParams.page = 1;
		}
	}, true);
	$scope.$watch('tquery', function(newValue) {
		if ($scope.teacherParams) {
			$scope.teacherParams.filter = newValue;
			$scope.teacherParams.page = 1;
		}
	}, true);
	
	$scope.storeReferer = function() {
		$rootScope.referer = "enrollpage";
		$rootScope.refererName = $scope.course;
		$rootScope.refererCourseId = courseId;
	};
}

function ImportController($rootScope, $scope, $routeParams, $http, flashService, courseService) {
	$rootScope.breadcrumb = [{'name':'Home','link':'#'}, {'name':'Import'}];
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
}

function ReviewJudgeController($rootScope, $scope, $routeParams, loginService, reviewjudgeService) {
	//$rootScope.breadcrumb = [{'name':'Home','link':'#'}, {'name':'Review Judgements','link':''}];
	var qid = $routeParams.qid; 
	var login = loginService.get( function() {
		if (login.display) {
			$scope.login = login.display;
			if (login.usertype == 'Teacher' || login.usertype == 'Admin') {
				$scope.instructor = true;
			}

		} else {
			$scope.login = '';
		}
	});
	var retval = reviewjudgeService.get({qid: qid}, function() {
		$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':retval.course,'link':'#/questionpage/' + retval.cid},{'name':'Review Judgements', 'link':''}];
		$scope.judgements = retval.judgements;
		$scope.title = retval.title;
		$scope.question = retval.question;
		$scope.authorQ = retval.authorQ;
		$scope.timeQ = retval.timeQ;
		$scope.avatarQ = retval.avatarQ;
	});
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
    };
});

myApp.directive('inputFocus', function() {
	return {
		restrict: 'A',
		
		link: function(scope, element, attrs) {
			angular.element(element).focus();
		}
	};
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
 
            ngModel.$render = function($scope) {
                element.html(ngModel.$viewValue || '');
            };
 
            element.on('hallomodified', function() {
                ngModel.$setViewValue(element.html());
                scope.$apply();
            });
        }
    };
});

myApp.directive("uploadImage", function() {
	return {
		restrict: "A",
		replace: true,
		scope: {
			image: "@image",
			editor: "@editor"
		},
		template: '<form ng-upload action="/uploadimage" class="margin0" enctype="multipart/form-data" name="uploadImg" novalidate>' +
			'<div><label for="stepBrowse" class="marginR5">Image</label><input type=file name=file id="stepBrowse" class="inlineBlock">' + 
			'<input class="btn btn-primary" type="submit" value="Insert image" upload-submit="addImage(content)"></div></form>',
		controller: function($rootScope, $scope, $element, $attrs, flashService) {
			$scope.addImage = function(content) {
				
				if (content.completed && content.file && content.file.length > 0) {
					img = document.createElement("IMG");
					img.src = "user_images/" + content.file;
					divElmnt = document.getElementById($scope.editor);
					if ($rootScope.savedRange && $rootScope.savedRange.compareNode(divElmnt) == 2) {
						$rootScope.savedRange.insertNode(img);
						rangy.getSelection().setSingleRange($rootScope.savedRange);
					}
					else {
						var textarea = angular.element("div#"+$scope.editor);
						textarea.append(img);
					}
				} else if(content.completed) {
					if(content.msg && content.msg.length > 0) {
						flashService.flash('danger', content.msg);
					}
					else {
						flashService.flash('danger', 'An error occured while uploading the image.');
					}
				}
			};
		}
	};
});

//myApp.directive("insertCode", function() {
//	return {
//		restrict: "A",
//		replace: true,
//		scope: {
//			image: "@image",
//			editor: "@editor"
//		},
//		template: '<div><label class="marginR5">Code</label><textarea rows="4" cols="50" class="inlineBlock"></textarea>' + 
//		'<input class="btn btn-primary" type="button" value="Insert Code" ng-click="insertCode()"></div>',
//		controller: function($rootScope, $scope, $element, flashService) {
//			$scope.insertCode = function() {
//				txtArea = document.getElementsByTagName("TEXTAREA")[0];
//				pre = document.createElement("pre");
//				pre.className = "highlight";
//				txt = document.createTextNode(txtArea.value);
//				pre.innerHTML = txtArea.value;
//				divElmnt = document.getElementById($scope.editor);
//				if ($rootScope.savedRange && $rootScope.savedRange.compareNode(divElmnt) == 2) {
//					$rootScope.savedRange.insertNode(pre);
//					rangy.getSelection().setSingleRange($rootScope.savedRange);
//				}
//				else {
//					var textarea = angular.element("div#"+$scope.editor);
//					textarea.append(pre);
//				}
//			};
//		}
//	};
//});

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
		controller: function($rootScope, $scope, $element, $attrs) {
			$scope.add = function() {
				divElmnt = document.getElementById($scope.editor);
				// insert the formular at the cursor position using Rangy's insert method
				if ($rootScope.savedRange && $rootScope.savedRange.compareNode(divElmnt) == 2) {
					$rootScope.savedRange.insertNode(document.createTextNode($scope.equation));
					rangy.getSelection().setSingleRange($rootScope.savedRange);
				}
				else {
					var textarea = angular.element("div#"+$scope.editor);
					textarea.append($scope.equation);
				}
			};
		}
	};
});

myApp.directive("mathImage", function() {
	return {
		restrict: "A",
		replace: true,
		scope: {
			equation: "@mathEquation",
			editor: "@editor",
			label: "@label",
			imgSrc: "@imgSrc",
			height: "@height"				
		},
		template: '<span ng-click="add()" class="btn btn-default"><img ng-src="img/{{imgSrc}}" style="height:{{height || 18}}px;" /></span>',
		controller: function($rootScope, $scope, $element, $attrs) {
			$scope.add = function() {
				divElmnt = document.getElementById($scope.editor);
				// insert the formular at the cursor position using Rangy's insert method
				if ($rootScope.savedRange && $rootScope.savedRange.compareNode(divElmnt) == 2) {
					$rootScope.savedRange.insertNode(document.createTextNode($scope.equation));
					rangy.getSelection().setSingleRange($rootScope.savedRange);
				}
				else {
					var textarea = angular.element("div#"+$scope.editor);
					textarea.append($scope.equation);
				}
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
		scope: true,
		template: '<ul class="breadcrumb">' + 
			'<li ng-class="{active: $last}" ng-repeat="crumb in breadcrumb"><a href="{{crumb.link}}" ng-if="!$last">{{crumb.name}}</a>' +
			'<span ng-if="$last">{{crumb.name}}</span>' +
			'</li></ul>'	
	};
});

myApp.directive("notification", function() {
	return {		
		restrict: "A",
		replace: true,
		scope: true,
		template: '<ul class="dropdown-menu"><li>{{notificationsCount}} new answer(s):</li>' + 
		'<li ng-repeat="item in notificationdropdown"><a href="{{item.href}}">{{item.text}}</a>' +
		'</li></ul>'	
	};
});

myApp.directive("commentBlock", function() {
	return {
		restrict: "A",
		scope: {
			type: "@ctype",
			login: "@clogin",
			instructor: "@cinstructor",
			sid: "@csid",
			sidl: "@sidl",
			sidr: "@sidr",
			qid: "@qid",
		},
		controller: function($rootScope, $scope, $element, $attrs, $routeParams, flashService, commentQService, commentAService, commentJService) {
			var questionId = $routeParams.questionId;
			
			$scope.commentEditId = -1;
			$scope.switchEdits = function(id) {		
				if (id) {
					$scope.myComment = null;
					$scope.lcomm =  null;
					$rootScope.savedRange = null;
				}
				$scope.commentEditId = id ? id == $scope.commentEditId ? -1 : id : $scope.commentEditId;				
				return $scope.commentEditId;
			};
	
			$scope.getComments = function() {
				if ($scope.type == 'Question') {
					var retval = commentQService.get( {id: questionId}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
						} else {
							flashService.flash('danger', 'The comments could not be found.');
						}
					});
				} else if ($scope.type == 'Answer') {
					var retval = commentAService.get( {id: $scope.sid}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
						} else {
							flashService.flash('danger', 'The comments could not be found.');
						}
					});
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					var retval = commentJService.get( {id: $scope.type == 'Judgement' ? questionId : $scope.qid, sidl: $scope.sidl, sidr: $scope.sidr}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
						} else {
							flashService.flash('danger', 'The comments could not be found.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
				}
			};
			$scope.getComments();

			$scope.makeComment = function() {
				var myComment = angular.element("#mycomment"+$scope.type + ($scope.type == "Answer" ? $scope.sid : "")).html();
				var newstring = angular.element("#mycomment"+$scope.type + ($scope.type == "Answer" ? $scope.sid : "")).text();
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
							flashService.flash('danger', 'Please submit a valid comment.');
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
							flashService.flash('danger', 'Please submit a valid comment.');
						}
					});
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					var retval = commentJService.save( {id: $scope.type == 'Judgement' ? questionId : $scope.qid, sidl: $scope.sidl, sidr: $scope.sidr}, input, function() {
						if (retval.comment) {
							$scope.anyComments.push( retval.comment );
							$scope.myComment = '';
							$scope.lcomm = false;
							flashService.flash('success', 'The comment has been successfully added.');
						} else {
							flashService.flash('danger', 'Please submit a valid comment.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
				}
			};

			$scope.delComment = function( comment ) {
				if ($scope.type == 'Question') {
					if (confirm("Delete Question Comment?") == true) {
						var retval = commentQService.remove( {id: comment.id}, function() {
							if (retval.msg != 'PASS') {
								flashService.flash('danger', 'The comment was unsuccessfully deleted.');
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
								flashService.flash('danger', 'The comment was unsuccessfully deleted.');
							} else {
								var index = jQuery.inArray(comment, $scope.anyComments);
								$scope.anyComments.splice(index, 1);
							}
						});
					}
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					if (confirm("Delete Answer Comment?") == true) {
						var retval = commentJService.remove( {id: comment.id, sidl: $scope.sidl, sidr: $scope.sidr}, function() {
							if (retval.msg != 'PASS') {
								flashService.flash('danger', 'The comment was unsuccessfully deleted.');
							} else {
								var index = jQuery.inArray(comment, $scope.anyComments);
								$scope.anyComments.splice(index, 1);
							}
						});
					}
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
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
							flashService.flash('danger', 'Please submit a comment.');
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
							flashService.flash('danger', 'Please submit a valid comment');
						} else {
							var index = jQuery.inArray(comment, $scope.anyComments);
							$scope.anyComments[index].content = newcontent;
							flashService.flash('success', 'The comment has been successfully added.');
						}
					});
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					var retval = commentJService.put( {id: comment.id, sidl: $scope.sidl, sidr: $scope.sidr}, input, function() {
						if (retval.msg != 'PASS') {
							//alert('something is wrong');
							flashService.flash('danger', 'Please submit a valid comment');
						} else {
							var index = jQuery.inArray(comment, $scope.anyComments);
							$scope.anyComments[index].content = newcontent;
							flashService.flash('success', 'The comment has been successfully added.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
				}
			};
			
			// save the Rangy object for the selected hallo editor
			$scope.saveRange = function() {
				var selRange = rangy.getSelection();
				$rootScope.savedRange = selRange.rangeCount ? selRange.getRangeAt(0) : null;
			};
		},
		templateUrl: 'templates/comments.html',
	};
});