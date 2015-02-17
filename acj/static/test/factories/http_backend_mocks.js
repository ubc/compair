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
			"create": {'global': true},
			"delete": {'global': true},
			"edit": {'global': true},
			"manage": {'global': true},
			"read": {'global': true}
		},
		"PostsForQuestions": {
			"create": {'global': true},
			"delete": {'global': true},
			"edit": {'global': true},
			"manage": {'global': true},
			"read": {'global': true}
		},
		"Users": {
			"create": {'global': true},
			"delete": {'global': true},
			"edit": {'global': true},
			"manage": {'global': true},
			"read": {'global': true}
		}
	};
	var permission_instructor = {
		"Courses": {
			"create": {'global': true},
			"delete": {'global': false, '1': false, '2': false},
			"edit": {'global': true, '1': true, '2': true},
			"manage": {'global': false, '1': false, '2': false},
			"read": {'global': true, '1': true, '2': true}
		},
		"PostsForQuestions": {
			"create": {'global': true, '1': true, '2': true},
			"delete": {'global': true, '1': true, '2': true},
			"edit": {'global': true, '1': true, '2': true},
			"manage": {'global': true, '1': true, '2': true},
			"read": {'global': true, '1': true, '2': true}
		},
		"Users": {
			"create": {'global': true},
			"delete": {'global': false},
			"edit": {'global': true},
			"manage": {'global': false},
			"read": {'global': true}
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

	$httpBackend.whenGET(/^\/api\/users\/\d+$/).respond(function(method, url, data, headers) {
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

	var post1 = {
		"content": "",
		"created": "Fri, 06 Feb 2015 22:12:59 -0000",
		"files": [],
		'id': 1,
		'modified': "Fri, 06 Feb 2015 22:12:59 -0000",
		'user': {
			"avatar": "b47d5e296b954b96c12fe3b5ced166b4",
			"created": "Sun, 11 Jan 2015 07:59:17 -0000",
			"displayname": "First Instructor",
			"id": 2,
			"lastonline": "Sun, 11 Jan 2015 08:25:08 -0000",
		}
	};

	var course1question = {
		"after_judging": false,
		"answer_end": "Sun, 15 Feb 2015 07:59:00 -0000",
		"answer_period": false,
		"answer_start": "Sat, 07 Feb 2015 08:00:00 -0000",
		"answers": [],
		"answers_count": 0,
		"available": false,
		"can_reply": true,
		"comments_count": 0,
		"criteria": [],
		"evaluation_count": 0,
		"id": 1,
		"judge_end": null,
		"judge_start": null,
		"judged": false,
		"judging_period": false,
		"modified": "Fri, 06 Feb 2015 22:12:59 -0000",
		"num_judgement_req": 3,
		"post": post1,
		"selfevaltype_id": 0,
		"title": "Test Question"
	};

	var questions = [
		[course1question],
		[]
	];

	var courses = {
		"objects": [course1, course2]
	};

	$httpBackend.whenGET(/\/api\/users\/\d+\/courses$/).respond(courses);
	$httpBackend.whenGET(/\/api\/courses\/\d+\/name$/).respond(function(method, url, data, headers) {
		var id = url.replace('/name', '').split('/').pop();
		return [200, {'course_name': courses.objects[id-1].name}, {}];
	});
	$httpBackend.whenPOST('/api/courses').respond(course2);
	$httpBackend.whenGET(/\/api\/courses\/\d+$/).respond(function(method, url, data, headers) {
		var id = url.split('/').pop();
		return [200, courses.objects[id-1], {}];
	});

	$httpBackend.whenGET(/\/api\/courses\/\d+\/criteria$/).respond(function(method, url, data, headers){
		var id = url.replace('/criteria', '').split('/').pop();
		return [200, {'objects': courses.objects[id-1].criteriaandcourses}, {}];
	});
	$httpBackend.whenGET(/\/api\/courses\/\d+\/judgements\/availpair$/).respond({
		"availPairsLogic": {}
	});
	$httpBackend.whenGET(/\/api\/courses\/\d+\/questions$/).respond(function(method, url, data, headers) {
		var id = url.replace('/questions', '').split('/').pop();
		return [200, {'questions': questions[id-1]}, {}]
	});
	$httpBackend.whenGET(/\/api\/courses\/\d+\/judgements\/count$/).respond({
		"judgements": 0
	});
	$httpBackend.whenGET(/\/api\/courses\/\d+\/answers\/answered$/).respond({
		"answered": {}
	});

	$httpBackend.whenPOST('/api/courses/2/criteria/1').respond({
		"criterion": {
			"active": true,
			"courses_id": 2,
			"criterion": default_criteria,
			"id": 2,
			"inQuestion": false
		}
	});
	$httpBackend.whenPOST(/\/api\/courses\/\d+\/questions\/\d+\/criteria\/\d+$/).respond({
		'active': true,
		'criterion': default_criteria
	});
	$httpBackend.whenGET('/api/criteria/default').respond(default_criteria);
	$httpBackend.whenGET('/api/criteria').respond(criteria);

	$httpBackend.whenGET(/\/api\/selfeval\/courses\/\d+\/questions$/).respond({
		"replies": {}
	});
};

module.exports.question = function($httpBackend) {
	var selfeval1 = {
		'id': 1,
		'name': "No Comparison with Another Answer"
	};
	var post1 = {
		"content": "",
		"created": "Fri, 06 Feb 2015 22:12:59 -0000",
		"files": [],
		'id': 1,
		'modified': "Fri, 06 Feb 2015 22:12:59 -0000",
		'user': {
			"avatar": "b47d5e296b954b96c12fe3b5ced166b4",
			"created": "Sun, 11 Jan 2015 07:59:17 -0000",
			"displayname": "First Instructor",
			"id": 2,
			"lastonline": "Sun, 11 Jan 2015 08:25:08 -0000",
		}
	};

	$httpBackend.whenGET('/api/selfevaltypes').respond({
		'types': [selfeval1]
	});

	$httpBackend.whenPOST(/\/api\/courses\/\d+\/questions$/).respond({
		"after_judging": false,
		"answer_end": "Sun, 15 Feb 2015 07:59:00 -0000",
		"answer_period": false,
		"answer_start": "Sat, 07 Feb 2015 08:00:00 -0000",
		"answers": [],
		"answers_count": 0,
		"available": false,
		"can_reply": true,
		"comments_count": 0,
		"criteria": [],
		"evaluation_count": 0,
		"id": 1,
		"judge_end": null,
		"judge_start": null,
		"judged": false,
		"judging_period": false,
		"modified": "Fri, 06 Feb 2015 22:12:59 -0000",
		"num_judgement_req": 3,
		"post": post1,
		"selfevaltype_id": 0,
		"title": "Test Question"
	});
};