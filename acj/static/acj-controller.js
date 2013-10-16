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

//function RankController($rootScope, $scope, $resource) {
//	$rootScope.breadcrumb = [{'name':'Home','link':'#'},{'name':'Ranking'}];
//	var retval = $resource('/ranking').get( function() {
//		$scope.scripts = retval.scripts;
//	});
//}

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
	//TODO create tutorial
	$rootScope.$broadcast("NO_TUTORIAL", false);
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
	//TODO create tutorial
	$rootScope.$broadcast("NO_TUTORIAL", false);
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
	//TODO create tutorial
	$rootScope.$broadcast("NO_TUTORIAL", false);
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
	//var questionData = [];
		
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
		//questionData = retval.questions;
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
		if ($scope.contentLengthCheck) {
			limit = parseInt($scope.contentLength);
			if (isNaN(limit) || limit < 0) {
				flashService.flash('danger', "The limit is invalid.");
				return '';
			}
		}
		//TODO print error msg when wrong limit (here and in edit)
		input = {"title": $scope.title, "content": $scope.question, "type": $scope.type, "taglist": $scope.taglist ? $scope.taglist : new Array(), 
				"contentLength": $scope.contentLengthCheck ? $scope.contentLength : 0};
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
					$scope.contentLengthCheck = false;
					$scope.contentLength = '';
					flashService.flash('success', "The question has been successfully added.");
				}
			}
		});
	};
	
	$scope.editquestion = function(newtitle, newquestion, question, newcontentLength, newcontentLengthCheck) {
		newquestion = angular.element("#question"+question.id).html();
		newstring = angular.element("#question"+question.id).text(); // ignore html tags
		if (!newtitle || !newstring) {
			return '';
		}
		if (newcontentLengthCheck) {
			limit = parseInt(newcontentLength);
			if (isNaN(limit) || limit < 0) {
				flashService.flash('danger', "The limit is invalid.");
				return '';
			}
		}
		input = {"title": newtitle, "content": newquestion, "taglist": question.tmptags ? question.tmptags : new Array(),
				"contentLength": newcontentLengthCheck ? newcontentLength : 0};
		var retval = questionService.put( {cid: question.id}, input, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('danger', 'Please submit a question.');
			} else {
				question.tags = question.tmptags ? question.tmptags : new Array();
				if ($scope.type == 'quiz') {
					var index = jQuery.inArray(question, $scope.quizzes);
					$scope.quizzes[index].title = newtitle;
					$scope.quizzes[index].content = newquestion;
					$scope.quizzes[index].contentLengthCheck = newcontentLengthCheck;
					$scope.quizzes[index].contentLength = newcontentLengthCheck ? newcontentLength : 0;
				}
				else {
					var index = jQuery.inArray(question, $scope.discussions);
					$scope.discussions[index].title = newtitle;
					$scope.discussions[index].content = newquestion;
					$scope.discussions[index].contentLengthCheck = newcontentLengthCheck;
					$scope.discussions[index].contentLength = newcontentLengthCheck ? newcontentLength : 0;
				}
				$scope.switchEdits(-1);
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

function AnswerController($rootScope, $scope, $routeParams, $http, flashService, answerService, rankService, commentAService, loginService) {
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
		$scope.contentLength = retval.contentLength;
		if (retval.usertype == 'Teacher' || retval.usertype == 'Admin') {
			$scope.instructor = true;
		}
		var title = retval.qtitle.length > 80 ? retval.qtitle.slice(0, 79) + '...' : retval.qtitle;
		$rootScope.breadcrumb = [{'name':'Home','link':'#'}, {'name':retval.course, 'link':'#/questionpage/'+retval.cid}, {'name':title, 'link':'#/answerpage/'+questionId}];
		
		var divs = jQuery('[contenteditable="true"][name*="answer"]');
		for ( var i = 0; divs[i]; i++) {
			jQuery(divs[i]).bind('paste', function(e) {
				$scope.saveRange(e, $scope.contentLength);
			});
		}
	});
	$scope.submit = function() {
		$scope.myanswer = angular.element("#myanswer").html();
		newstring = angular.element("#myanswer").text();
		if (!newstring) {
			return '';
		}
		if ($scope.contentLength > 0) {
			elmt = angular.element("#myanswer");
			fullRange = rangy.createRange();
			fullRange.setStartBefore(elmt[0]);
			fullRange.setEndAfter(elmt[0]);
			if (fullRange.toString().length > $scope.contentLength) {
				flashService.flash('danger', 'The answer is too long.');
				return '';
			}
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
		if ($scope.contentLength > 0) {
			elmt = angular.element("#editScript"+script.id);
			fullRange = rangy.createRange();
			fullRange.setStartBefore(elmt[0]);
			fullRange.setEndAfter(elmt[0]);
			if (fullRange.toString().length > $scope.contentLength) {
				flashService.flash('danger', 'The answer is too long.');
				return '';
			}
		}
		input = {"content": newanswer};
		var retval = answerService.put( {qid: script.id}, input, function() {
			if (retval.msg != 'PASS') {
				flashService.flash('danger', 'Please submit an answer.');
			} else {
				var index = jQuery.inArray(script, $scope.scripts);
				$scope.scripts[index].content = newanswer;
				flashService.flash('success', 'The answer has been successfully modified.');
				$scope.switchEdits(-1);
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
	// save the Rangy object for the selected hallo editor
	/*
	$scope.saveRange = function() {
		var selRange = rangy.getSelection();
		$rootScope.savedRange = selRange.rangeCount ? selRange.getRangeAt(0) : null;
	};
	*/
	//TODO
	$scope.saveRange = function($event, max) {
		var selRange = rangy.getSelection();
		$rootScope.savedRange = selRange.rangeCount ? selRange.getRangeAt(0) : null;
		if (max) {
			elmt = selRange.getRangeAt(0).startContainer;
			while (elmt.contentEditable != 'true') {
				elmt = elmt.parentNode;
			}
			fullRange = rangy.getSelection().getRangeAt(0);
			fullRange.setStartBefore(elmt);
			fullRange.setEndAfter(elmt);
			//[backspace,shift,ctrl,alt,end,home,left,up,down,right,delete]
			allowedKeys = [8, 16, 17, 18, 35, 36, 37, 38, 39, 40, 46];
			if($event && allowedKeys.indexOf($event.which) == -1 && fullRange.toString().length >= max) {
				$event.preventDefault();
				jQuery("#" + elmt.id).effect("highlight", {"color":"#dFb5b4"}, 50);
				jQuery("#" + elmt.id + "Error").removeClass('ng-hide');
		    }
			else {
				jQuery("#" + elmt.id + "Error").addClass('ng-hide');
			}
		}
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
	//TODO create tutorial
	$rootScope.$broadcast("NO_TUTORIAL", false);
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