function passThrough($httpBackend) {
	$httpBackend.whenGET(/.*/).passThrough();
}

function build(funcs) {
	var funcStr = "angular.module('httpBackEndMock', ['ngMockE2E'])";

	if (Array.isArray(funcs)) {
		for (var i = 0; i < funcs.length; i++) {
			funcStr += "\r.run(" + funcs[i] + ")"
		}
	} else {
		funcStr += "\r.run(" + funcs + ")"
	}

	funcStr += "\r.run(" + passThrough + ")";

	var funcTyped = Function(funcStr);

	//console.log(funcTyped.toString())
	return funcTyped;
}

module.exports.build = function(browser, funcs) {
	if (process.env.DISABLE_MOCK == 'true') {
		return;
	}

	browser.addMockModule('httpBackEndMock', build(funcs));
};

module.exports.session = function ($httpBackend, Session, $rootScope) {
	console.log(Session.isLoggedIn());
	var authenticated = false;
	var current_user = 0;
	var permission_root = {
		"Courses": {
			"create": true,
			"delete": true,
			"edit": true,
			"manage": true,
			"read": true
		},
		"PostsForQuestions": {
			"create": true,
			"delete": true,
			"edit": true,
			"manage": true,
			"read": true
		},
		"Users": {
			"create": true,
			"delete": true,
			"edit": true,
			"manage": true,
			"read": true
		}
	};
	var permission_instructor = {
		"Courses": {
			"create": true,
			"delete": false,
			"edit": false,
			"manage": false,
			"read": false
		},
		"PostsForQuestions": {
			"create": true,
			"delete": true,
			"edit": true,
			"manage": true,
			"read": true
		},
		"Users": {
			"create": true,
			"delete": false,
			"edit": true,
			"manage": false,
			"read": true
		}
	};

	var users = {
		'root':  {
			"userid": 1,
			"permissions": permission_root
		},
		'instructor1': {
			"userid": 2,
			"permissions": permission_instructor
		}
	};

	var sessions = {
		'root': {
			"id": 1,
			"permissions": permission_root
		},
		'instructor1': {
			"id": 2,
			"permissions": permission_instructor
		}
	};


	$httpBackend.whenGET('/api/session').respond(function(method, url, data, headers) {
		return authenticated ? [200, sessions[current_user], {}] : [401, {}, {}];
	});

	$httpBackend.whenGET('/api/session/permission').respond(function(method, url, data, headers) {
		var username = undefined;
		Session.getUser().then(function(user) {
			username =user.username;
		});
		// Propagate getUser() promise resolution to 'then' functions using $apply().
		$rootScope.$apply();

		return [200, users[username].permissions, {}];
	});

	$httpBackend.whenPOST('/api/login').respond(function(method, url, data, headers) {
		authenticated = true;
		current_user = angular.fromJson(data).username;
		return [200, users[current_user], {}];
	});
	// logout
	//$httpBackend.whenDELETE('/api/auth').respond(function(method, url, data, headers) {
	//    authenticated = false;
	//    return [204, {}, {}];
	//});
};

module.exports.user = function($httpBackend) {
	var users = [
		{},
		{ // root
			"avatar": "63a9f0ea7bb98050796b649e85481845",
			"created": "Sat, 27 Dec 2014 20:13:11 -0000",
			"displayname": "root",
			"email": null,
			"firstname": "JaNy",
			"fullname": "JaNy bwsV",
			"id": 1,
			"lastname": "bwsV",
			"lastonline": "Sun, 11 Jan 2015 02:55:59 -0000",
			"modified": "Sun, 11 Jan 2015 02:55:59 -0000",
			"student_no": null,
			"username": "root",
			"usertypeforsystem": {
				"id": 3,
				"name": "System Administrator"
			},
			"usertypesforsystem_id": 3
		},
		{ // instructor1
			"avatar": "b47d5e296b954b96c12fe3b5ced166b4",
			"created": "Sun, 11 Jan 2015 07:59:17 -0000",
			"displayname": "First Instructor",
			"email": "first.instructor@exmple.com",
			"firstname": "First",
			"fullname": "First Instructor",
			"id": 2,
			"lastname": "Instructor",
			"lastonline": "Sun, 11 Jan 2015 08:25:08 -0000",
			"modified": "Sun, 11 Jan 2015 08:25:08 -0000",
			"student_no": null,
			"username": "instructor1",
			"usertypeforsystem": {
				"id": 2,
				"name": "Instructor"
			},
			"usertypesforsystem_id": 2
		}];

	$httpBackend.whenGET(/^\/api\/users\/\d+/).respond(function(method, url, data, headers) {
		var id = url.split('/').pop();
		return [200, users[id], {}];
	});
};


module.exports.course = function($httpBackend) {
	var default_criteria = {
		"created": "Sun, 11 Jan 2015 07:45:31 -0000",
		"default": true,
		"description": "<p>Choose the response that you think is the better of the two.</p>",
		"id": 1,
		"judged": false,
		"modified": "Sun, 11 Jan 2015 07:45:31 -0000",
		"name": "Which is better?",
		"users_id": 1
	};

	var criteria = {
		"criteria": [default_criteria]
	};

	var course1 = {
		"criteriaandcourses": [
			{
				"active": true,
				"courses_id": 1,
				"criterion": default_criteria,
				"id": 1,
				"inQuestion": false
			}
		],
		"description": null,
		"id": 1,
		"name": "Test Course"
	};
	var course2 = {
		"available": true,
		"created": "Sun, 11 Jan 2015 08:44:46 -0000",
		"criteriaandcourses": [
			{
				"active": true,
				"courses_id": 2,
				"criterion": default_criteria,
				"id": 2,
				"inQuestion": false
			}
		],
		"description": null,
		"enable_student_create_questions": false,
		"enable_student_create_tags": false,
		"id": 2,
		"modified": "Sun, 11 Jan 2015 08:44:46 -0000",
		"name": "Test Course"
	};

	var courses = {
		"objects": [course1, course2]
	};

	$httpBackend.whenGET(/\/api\/users\/\d+\/courses/).respond(courses);
	$httpBackend.whenGET(/\/api\/courses\/\d+\/name/).respond(function(method, url, data, headers) {
		var id = url.replace('/name', '').split('/').pop();
		return [200, courses.objects[id-1].name, {}];
	});
	$httpBackend.whenGET('/api/criteria/default').respond(default_criteria);
	$httpBackend.whenGET('/api/criteria').respond(criteria);
	$httpBackend.whenPOST('/api/courses').respond(course2);
	$httpBackend.whenGET(/\/api\/courses\/\d+/).respond(function(method, url, data, headers) {
		var id = url.split('/').pop();
		return [200, courses.objects[id-1], {}];
	});

	// Course 1
	$httpBackend.whenGET('/api/courses/1/criteria').respond({
		"objects": course1.criteriaandcourses
	});
	$httpBackend.whenGET('/api/courses/1/judgements/availpair').respond({
		"availPairsLogic": {}
	});
	$httpBackend.whenGET('/api/courses/1/questions').respond({
		"questions": []
	});
	$httpBackend.whenGET('/api/courses/1/judgements/count').respond({
		"judgements": {}
	});
	$httpBackend.whenGET('/api/selfeval/courses/1/questions').respond({
		"replies": {}
	});
	$httpBackend.whenGET('/api/courses/1/answers/answered').respond({
		"answered": {}
	});

	// Course 2
	$httpBackend.whenPOST('/api/courses/2/criteria/1').respond({
		"criterion": {
			"active": true,
			"courses_id": 2,
			"criterion": default_criteria,
			"id": 2,
			"inQuestion": false
		}
	});
	$httpBackend.whenGET('/api/courses/2/judgements/availpair').respond({
		"availPairsLogic": {}
	});
	$httpBackend.whenGET('/api/courses/2/questions').respond({
		"questions": []
	});
	$httpBackend.whenGET('/api/courses/2/answers/answered').respond({
		"answered": {}
	});
	$httpBackend.whenGET('/api/selfeval/courses/2/questions').respond({
		"replies": {}
	});
	$httpBackend.whenGET('/api/courses/2/judgements/count').respond({
		"judgements": {}
	});
};

module.exports.question = function($httpBackend) {
	var selfeval1 = {
		'id': 1,
		'name': "No Comparison with Another Answer"
	};

	$httpBackend.whenGET('/api/selfevaltypes').respond({
		'types': [selfeval1]
	});
};