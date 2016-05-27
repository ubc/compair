module.exports.build = function(browser, storageFixture) {
	if (process.env.DISABLE_MOCK == 'true') {
		return;
	}

	browser.addMockModule('httpBackEndMock', module.exports.httpbackendMock, storageFixture);
};

module.exports.httpbackendMock = function(storageFixture) {
    angular.module('httpBackEndMock', ['ngMockE2E'])
    .run(function($httpBackend) {
        var authenticated = false;

        var default_criteria = {
            "id": 1,
            "users_id": 1,
            "name": "Which is better?",
            "description": "<p>Choose the response that you think is the better of the two.</p>",
            "default": true,
            "judged": false,
            "created": "Sun, 11 Jan 2015 07:45:31 -0000",
            "modified": "Sun, 11 Jan 2015 07:45:31 -0000"
        };


        var storage = {
            loginDetails: { id: null, username: null, password: null },
            session: {},
            users: [],
            courses: [],
            // userId -> [ { courseId, roleId} ]
            users_and_courses: {},
            // courseId -> [criteriaId]
            course_criteria: {},
            questions: [],
            // courseId -> [questionId]
            course_questions: {},
            // questionId -> [criteriaId]
            question_criteria: {},
            answers: [],
            // courseId -> [answerId]
            course_answers: {},
            // questionId -> [answerId]
            question_answers: {},
            criteria: [],
            groups: [],
            // userId -> [groupId]
            user_group: {},
            user_search_results: {
                "objects": [],
                "page":1,
                "pages":1,
                "per_page":20,
                "total":0
            },
            selfEvalTypes: [
                { "id": 1, "name": "No Comparison with Another Answer" }
            ],
            userTypes: [
                { "id": 1, "name": "Student" },
                { "id": 2, "name": "Instructor" }
            ],
            courseroles: [
                { "id": 2, "name": "Instructor" },
                { "id": 3, "name": "Teaching Assistant" },
                { "id": 4, "name": "Student" }
            ]
        }

        // add fixture data to storage
        if (storageFixture) {
            storage = angular.merge({}, storage, storageFixture);
        }

        // add default criteria is storage criteria is empty
        if (storage.criteria.length == 0) {
            storage.criteria.push(default_criteria);
        }

        // Start Session

        // get current session
        $httpBackend.whenGET('/api/session').respond(function(method, url, data, headers) {
            return authenticated ? [200, storage.session, {}] : [401, {}, {}];
        });

        // get current session permissions
        $httpBackend.whenGET('/api/session/permission').respond(function(method, url, data, headers) {
            return authenticated ? [200, storage.session.permissions, {}] : [401, {}, {}];
        });

        // login
        $httpBackend.whenPOST('/api/login').respond(function(method, url, data, headers) {
            authenticated = true;
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);
            return [200, currentUser, {}];
        });

        // logout
        $httpBackend.whenDELETE('/api/logout').respond(function(method, url, data, headers) {
            authenticated = false;
            return [202, {}, {}];
        });
        // End Session



        // Start User

        // get user types
        $httpBackend.whenGET('/api/usertypes').respond(storage.userTypes);

        // get user by id
        $httpBackend.whenGET(/^\/api\/users\/\d+$/).respond(function(method, url, data, headers) {
            var id = url.split('/').pop();
            return [200, storage.users[id-1], {}];
        });

        // create user
        $httpBackend.whenPOST('/api/users').respond(function(method, url, data, headers) {
            data = JSON.parse(data);
            var newUser = {
                "id": storage.users.length + 1,
                "username": null,
                "displayname": null,
                "email": null,
                "firstname": null,
                "fullname": null,
                "lastname": null,
                "student_no": null,
                "avatar": "63a9f0ea7bb98050796b649e85481845",
                "created": "Sat, 27 Dec 2014 20:13:11 -0000",
                "modified": "Sun, 11 Jan 2015 02:55:59 -0000",
                "lastonline": "Sun, 11 Jan 2015 02:55:59 -0000",
                "usertypeforsystem": {
                    "id": null,
                    "name": null
                },
                "system_role": null,
                "usertypesforsystem_id": null
            };

            newUser = angular.merge({}, newUser, data);
            newUser.fullname = newUser.firstname + " " + newUser.lastname;
            newUser.usertypeforsystem.id = newUser.usertypesforsystem_id;

            var userType = "";
            switch (newUser.usertypesforsystem_id) {
                case 3: userType = "System Administrator"; break;
                case 2: userType = "Instructor"; break;
                case 1: userType = "Student"; break;
            }
            newUser.system_role = userType;
            newUser.usertypeforsystem.name = userType;

            storage.users.push(newUser);

            var returnData = {
                id: newUser.id,
                displayname: newUser.displayname,
                avatar: newUser.avatar,
                created: newUser.created,
                lastonline: newUser.lastonline
            }

            return [200, returnData, {}]
        });

        // search for user by text
        $httpBackend.whenGET(/\/api\/users\?search\=.*$/).respond(storage.user_search_results);

        // get edit button availability
        $httpBackend.whenGET(/\/api\/users\/\d+\/edit$/).respond(function(method, url, data, headers) {
            var editId = url.replace('/edit', '').split('/').pop();
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);

            var available = false;
            // admins can edit anyone
            if (currentUser.usertypesforsystem_id == 3) {
                available = true;

            // anyone can edit themselves
            } else if (currentUser.id == editId) {
                available = true;

            // teachers can edit users in their class
            } else if (currentUser.usertypesforsystem_id == 2) {

                // if both current user and edit user have courses
                if (storage.users_and_courses[currentUser.id] && storage.users_and_courses[editId]) {

                    // check courses current user is instructor of
                    angular.forEach(storage.users_and_courses[currentUser.id], function(course_and_role) {
                        if (course_and_role.role == 2) {
                            var courseId = course_and_role.courseId;

                            // check if edit user in course
                            angular.forEach(storage.users_and_courses[currentUser.id], function(course_and_role) {
                                // if edit user in course
                                if (course_and_role.courseId == courseId) {
                                    available = true;
                                }
                            });
                        }
                    });
                }
            }

            return [200, { "available": available }, {}];
        });

        // update user details
        $httpBackend.whenPOST(/^\/api\/users\/\d+$/).respond(function(method, url, data, headers) {
            var data = JSON.parse(data);
            var editId = url.split('/').pop();
            storage.users[editId-1] = data;
            return [200, data, {}];
        });

        // update user password
        $httpBackend.whenPOST(/^\/api\/users\/\d+\/password$/).respond(function(method, url, data, headers) {
            var editId = url.split('/')[3];
            //no need to actually change the password
            return [200, storage.users[editId-1], {}];
        });


        // End User


        // Start Courses

        // get course roles
        $httpBackend.whenGET('/api/courseroles').respond(storage.courseroles);

        // get current user courses
        $httpBackend.whenGET(/\/api\/users\/\d+\/courses$/).respond({
            "objects": storage.courses
        });

        /*
        TODO check if needed
        $httpBackend.whenGET(/\/api\/courses\/\d+\/name$/).respond(function(method, url, data, headers) {
            var id = url.replace('/name', '').split('/').pop();
            return [200, {'course_name': courses.objects[id-1].name}, {}];
        });
        */

        // create new course
        $httpBackend.whenPOST('/api/courses').respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var id = storage.courses.length + 1;

            var newCourse = {
                "id": id,
                "name": data.name,
                "description": data.description,
                "available": true,
                "enable_student_create_questions": false,
                "enable_student_create_tags": false,
                "modified": "Sun, 11 Jan 2015 08:44:46 -0000",
                "created": "Sun, 11 Jan 2015 08:44:46 -0000"
            }

            storage.courses.push(newCourse);

            // setup course criteria
            storage.course_criteria[id] = [];
            angular.forEach(data.criteria, function(criteria, key) {
                storage.course_criteria[id].push(criteria.id);
            });

            return [200, newCourse, {}];
        });

        // get course by id
        $httpBackend.whenGET(/\/api\/courses\/\d+$/).respond(function(method, url, data, headers) {
            var id = url.split('/').pop();
            return [200, storage.courses[id-1], {}];
        });

        // edit course by id
        $httpBackend.whenPOST(/\/api\/courses\/\d+$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var criteria = data.criteria;
            delete data.criteria;

            var id = url.split('/').pop();
            storage.courses[id-1] = angular.merge(storage.courses[id-1], data);

            // setup course criteria
            storage.course_criteria[id] = [];
            angular.forEach(criteria, function(criteria, key) {
                storage.course_criteria[id].push(criteria.id);
            });

            return [200, storage.courses[id-1], {}];
        });

        // get course criteria by course id
        $httpBackend.whenGET(/\/api\/courses\/\d+\/criteria$/).respond(function(method, url, data, headers){
            var id = url.replace('/criteria', '').split('/').pop();

            var criteriaList = [];

            if (storage.course_criteria[id]) {
                angular.forEach(storage.course_criteria[id], function(criteriaId) {
                    var criteria = angular.copy(storage.criteria[criteriaId-1]);
                    criteria.active = true;
                    criteriaList.push(criteria);
                });
            }

            return [200, { 'objects': criteriaList }, {}];
        });


        // get course users by course id
        $httpBackend.whenGET(/\/api\/courses\/\d+\/users$/).respond(function(method, url, data, headers){
            var courseId = url.replace('/users', '').split('/').pop();

            var userList = [];

            angular.forEach(storage.users, function(user) {
                if (storage.users_and_courses[user.id]) {
                    angular.forEach(storage.users_and_courses[user.id], function(userCoruseInfo) {

                        if (courseId == userCoruseInfo.courseId) {
                            var user_copy = angular.copy(user);
                            user_copy.course_role = storage.courseroles[userCoruseInfo.role-2].name;
                            user_copy.group_id = 0;

                            if (storage.user_group[user.id]) {
                                user_copy.group_id = storage.user_group[user.id];
                            }

                            userList.push(user_copy);
                        }
                    });
                }
            });

            return [200, { 'objects': userList }, {}];
        });

        // get course groups by course id
        $httpBackend.whenGET(/\/api\/courses\/\d+\/groups$/).respond({ 'groups': storage.groups });

        // update user role in course
        $httpBackend.whenPOST(/\/api\/courses\/\d+\/users\/\d+$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);
            var courseId = url.split('/')[3];
            var userId = url.split('/').pop();
            var courseRoleId = data.course_role_id;

            storage.users_and_courses[userId] = [
                { courseId: courseId, role: courseRoleId }
            ];

            var returnData = {
                course_role: storage.courseroles[courseRoleId-2].name,
                fullname: storage.users[userId-1].fullname,
                user_id: userId
            }

            return [200, returnData, {}];
        });

        // drop user from coruse
        $httpBackend.whenDELETE(/\/api\/courses\/\d+\/users\/\d+$/).respond(function(method, url, data, headers) {
            var userId = url.split('/').pop();

            storage.users_and_courses[userId] = [];

            var returnData = {
                "user": {
                    "fullname": storage.users[userId-1].fullname,
                    "id": userId
                },
                "usertypesforcourse": {
                    "id": 1,
                    "name": "Dropped"
                }
            }

            return [200, returnData, {}];
        });

        // update user group in course
        $httpBackend.whenPOST(/\/api\/courses\/\d+\/users\/\d+\/groups\/\d+$/).respond(function(method, url, data, headers) {
            var userId = url.split('/')[5];
            var groupId = url.split('/').pop();

            storage.user_group[userId] = groupId;

            var returnData = {
                "groups_name": storage.groups[groupId-1].name
            };

            return [200, returnData, {}];
        });

        // remove user from groups in course
        $httpBackend.whenDELETE(/\/api\/courses\/\d+\/users\/\d+\/groups$/).respond(function(method, url, data, headers) {
            var courseId = url.split('/')[3];
            var userId = url.split('/')[5];

            delete storage.user_group[userId];

            var returnData = {
                "course_id": courseId,
                "user_id": userId
            };

            return [200, returnData, {}];
        });

        $httpBackend.whenGET(/\/api\/courses\/\d+\/judgements\/availpair$/).respond({
            "availPairsLogic": {}
        });
        $httpBackend.whenGET(/\/api\/courses\/\d+\/judgements\/count$/).respond({
            "judgements": 0
        });
        $httpBackend.whenGET(/\/api\/courses\/\d+\/answers\/answered$/).respond(function(method, url, data, headers){
            var courseId = url.split('/')[3];
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);

            var answered = {};

            // get all answers in course
            if (storage.course_answers[courseId]) {
                angular.forEach(storage.course_answers[courseId], function(answerId) {
                    var answer = storage.answers[answerId-1];

                    // if answer is by current user, set answered to true for question
                    if (answer.user_id == currentUser.id) {
                        answered[answer.questions_id] = 1;
                    }
                });
            }


            return [200, { 'answered': answered }, {}];
        });

        /*
        TODO: check usage
        $httpBackend.whenPOST(/\/api\/courses\/\d+\/criteria\/\d$/).respond(function(method, url, data, headers) {
        });
        */

        /*
        TODO: check usage
        $httpBackend.whenGET('/api/criteria/default').respond(default_criteria);
        */

        // get current user's criteria
        $httpBackend.whenGET('/api/criteria').respond({
            "criteria": storage.criteria
        });

        // create new criteria
        $httpBackend.whenPOST('/api/criteria').respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var id = storage.criteria.length + 1;
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);

            var newCriteria = {
                "id": id,
                "users_id": currentUser.id,
                "name": data.name,
                "description": data.description,
                "default": data.default,
                "judged": false,
                "created": "Mon, 18 Apr 2016 17:38:23 -0000",
                "modified": "Mon, 18 Apr 2016 17:38:23 -0000"
            };

            storage.criteria.push(newCriteria);

            return [200, newCriteria, {}];
        });

        // update criteria by id
        $httpBackend.whenPOST(/\/api\/criteria\/\d+$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);
            var id = url.split('/').pop();

            storage.criteria[id-1] = angular.merge(storage.criteria[id-1], data);

            return [200, storage.criteria[id-1], {}];
        });

        $httpBackend.whenGET(/\/api\/selfeval\/courses\/\d+\/questions$/).respond({
            "replies": {}
        });


        // End Courses



        // Start Questions

        $httpBackend.whenGET('/api/selfevaltypes').respond({
            'types': storage.selfEvalTypes
        });

        $httpBackend.whenGET(/\/api\/courses\/\d+\/questions$/).respond(function(method, url, data, headers) {
            var id = url.replace('/questions', '').split('/').pop();

            var questionList = [];

            if (storage.course_questions[id]) {
                angular.forEach(storage.course_questions[id], function(questionId) {
                    questionList.push(storage.questions[questionId-1]);
                });
            }

            return [200, { 'questions': questionList }, {}]
        });

        $httpBackend.whenPOST(/\/api\/courses\/\d+\/questions$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var courseId = url.replace('/questions', '').split('/').pop();
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);

            var newQuestion = {
                "id": null,
                "title": null,
                "num_judgement_req": null,
                "answer_end": null,
                "answer_start": null,
                "can_reply": null,
                "judge_end": null,
                "judge_start": null,
                "after_judging": false,
                "answer_period": false,
                "answers_count": 0,
                "available": false,
                "comments_count": 0,
                "criteria": [],
                "evaluation_count": 0,
                "judged": false,
                "judging_period": false,
                "modified": "Wed, 20 Apr 2016 21:50:31 -0000",
                "selfevaltype_id": 0,
                "post": {
                    "id": null,
                    "content": null,
                    "files": [],
                    "user": angular.copy(currentUser),
                    "created": "Wed, 20 Apr 2016 21:50:31 -0000",
                    "modified": "Wed, 20 Apr 2016 21:50:31 -0000"
                }
            }
            newQuestion = angular.merge(newQuestion, data);
            newQuestion.id = storage.questions.length + 1;

            storage.questions.push(newQuestion);

            if (!storage.course_questions[courseId]) {
                storage.course_questions[courseId] = [];
            }
            storage.course_questions[courseId].push(newQuestion.id)

            return [200, newQuestion, {}]
        });

        $httpBackend.whenPOST(/\/api\/courses\/\d+\/questions\/\d+\/criteria\/\d+$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var courseId = url.split('/')[3];
            var questionId = url.split('/')[5];
            var criteriaId = url.split('/').pop();

            if (!storage.question_criteria[questionId]) {
                storage.question_criteria[questionId] = [];
            }
            var active = false,
                activeIndex = null;
            angular.forEach(storage.question_criteria[questionId], function(activeCriteriaId, index) {
                if (activeCriteriaId == criteriaId) {
                    active = true;
                    activeIndex = index;
                }
            });

            if (active) {
                // remvoe criteria
                storage.question_criteria[questionId] = storage.question_criteria[questionId].splice(activeIndex, 1);
            } else {
                // add criteria
                storage.question_criteria[questionId].push(criteriaId);
            }

            var criteria = storage.criteria[criteriaId-1];
            var returnData = {
                'active': !active,
                'criterion': criteria
            }

            return [200, returnData, {}]
        });

        $httpBackend.whenPOST(/\/api\/courses\/\d+\/questions\/\d+\/criteria\/\d+$/).respond({
            'active': true,
            'criterion': default_criteria
        });

        // End Questions
    })
    .run(function($httpBackend) {
        $httpBackend.whenGET(/.*/).passThrough();
    });
};