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

        var default_criterion = {
            "id": 1,
            "user_id": 1,
            "name": "Which is better?",
            "description": "<p>Choose the response that you think is the better of the two.</p>",
            "default": true,
            "compared": false,
            "created": "Sun, 11 Jan 2015 07:45:31 -0000",
            "modified": "Sun, 11 Jan 2015 07:45:31 -0000"
        };


        var storage = {
            loginDetails: { id: null, username: null, password: null },
            session: {},
            users: [],
            courses: [],
            // userId -> [ { courseId, courseRole, groupName} ]
            user_courses: {},
            assignments: [],
            // courseId -> [assignmentId]
            course_assignments: {},
            answers: [],
            // courseId -> [answerId]
            course_answers: {},
            // assignmentId -> [answerId]
            assignment_answers: {},
            criteria: [],
            groups: [],
            user_search_results: {
                "objects": [],
                "page":1,
                "pages":1,
                "per_page":20,
                "total":0
            }
        }

        // add fixture data to storage
        if (storageFixture) {
            storage = angular.merge({}, storage, storageFixture);
        }

        // add default criterion is storage criterion is empty
        if (storage.criteria.length == 0) {
            storage.criteria.push(default_criterion);
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
                "student_number": null,
                "avatar": "63a9f0ea7bb98050796b649e85481845",
                "created": "Sat, 27 Dec 2014 20:13:11 -0000",
                "modified": "Sun, 11 Jan 2015 02:55:59 -0000",
                "last_online": "Sun, 11 Jan 2015 02:55:59 -0000",
                "system_role": null
            };

            newUser = angular.merge({}, newUser, data);
            newUser.fullname = newUser.firstname + " " + newUser.lastname;

            storage.users.push(newUser);

            var returnData = {
                id: newUser.id,
                displayname: newUser.displayname,
                avatar: newUser.avatar,
                created: newUser.created,
                last_online: newUser.last_online
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
            if (currentUser.system_role == "System Administrator") {
                available = true;

            // anyone can edit themselves
            } else if (currentUser.id == editId) {
                available = true;

            // teachers can edit users in their class
            } else if (currentUser.system_role == "Instructor") {

                // if both current user and edit user have courses
                if (storage.user_courses[currentUser.id] && storage.user_courses[editId]) {

                    // check courses current user is instructor of
                    angular.forEach(storage.user_courses[currentUser.id], function(course_and_role) {
                        if (course_and_role.courseRole == "Instructor") {
                            var courseId = course_and_role.courseId;

                            // check if edit user in course
                            angular.forEach(storage.user_courses[currentUser.id], function(course_and_role) {
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

        // get current user courses
        $httpBackend.whenGET(/\/api\/users\/\d+\/courses$/).respond({
            "objects": storage.courses
        });

        // create new course
        $httpBackend.whenPOST('/api/courses').respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var id = storage.courses.length + 1;

            var newCourse = {
                "id": id,
                "name": data.name,
                "year": data.year,
                "term": data.term,
                "description": data.description,
                "available": true,
                "start_date": data.start_date,
                "end_date": data.end_date,
                "modified": "Sun, 11 Jan 2015 08:44:46 -0000",
                "created": "Sun, 11 Jan 2015 08:44:46 -0000"
            }

            storage.courses.push(newCourse);

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

            var id = url.split('/').pop();
            storage.courses[id-1] = angular.merge(storage.courses[id-1], data);

            return [200, storage.courses[id-1], {}];
        });


        // get course users by course id
        $httpBackend.whenGET(/\/api\/courses\/\d+\/users$/).respond(function(method, url, data, headers){
            var courseId = url.replace('/users', '').split('/').pop();

            var userList = [];

            angular.forEach(storage.users, function(user) {
                if (storage.user_courses[user.id]) {
                    angular.forEach(storage.user_courses[user.id], function(userCoruseInfo) {

                        if (courseId == userCoruseInfo.courseId) {
                            var user_copy = angular.copy(user);
                            user_copy.course_role = userCoruseInfo.courseRole;
                            user_copy.group_name = userCoruseInfo.groupName;

                            userList.push(user_copy);
                        }
                    });
                }
            });

            return [200, { 'objects': userList }, {}];
        });

        // get course students by course id
        $httpBackend.whenGET(/\/api\/courses\/\d+\/users\/students$/).respond(function(method, url, data, headers){
            var courseId = url.replace('/users', '').split('/').pop();

            var userList = [];

            angular.forEach(storage.users, function(user) {
                if (storage.user_courses[user.id]) {
                    angular.forEach(storage.user_courses[user.id], function(userCoruseInfo) {
                        if (courseId == userCoruseInfo.courseId && userCoruseInfo.courseRole == "Student") {
                            userList.push({
                                course_role: userCoruseInfo.courseRole,
                                id: user.id,
                                group_name: userCoruseInfo.groupName
                            });
                        }
                    });
                }
            });

            return [200, { 'objects': userList }, {}];
        });

        // get course instructor labels
        $httpBackend.whenGET(/\/api\/courses\/\d+\/users\/instructors\/labels$/).respond(function(method, url, data, headers){
            var courseId = url.replace('/users', '').split('/').pop();

            var userList = {};

            angular.forEach(storage.users, function(user) {
                if (storage.user_courses[user.id]) {
                    angular.forEach(storage.user_courses[user.id], function(userCoruseInfo) {
                        if (courseId == userCoruseInfo.courseId) {
                            if (userCoruseInfo.courseRole == "Instructor") {
                                userList[user.id] = "Instructor";
                            } else if (userCoruseInfo.courseRole == "Teaching Assistant") {
                                userList[user.id] = "Teaching Assistant";
                            }
                        }
                    });
                }
            });

            return [200, { 'objects': userList }, {}];
        });

        // get course groups by course id
        $httpBackend.whenGET(/\/api\/courses\/\d+\/groups$/).respond({ 'objects': storage.groups });

        // update user role in course
        $httpBackend.whenPOST(/\/api\/courses\/\d+\/users\/\d+$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);
            var courseId = url.split('/')[3];
            var userId = url.split('/').pop();
            var courseRole = data.course_role;

            var found = false;

            angular.forEach(storage.user_courses[userId], function(userCoruseInfo) {
                if (userCoruseInfo.courseId == courseId) {
                    found = true;
                    userCoruseInfo.courseRole = courseRole;
                }
            });

            if (!found) {
                storage.user_courses[userId] = [
                    { courseId: courseId, courseRole: courseRole, groupName: null }
                ];
            }

            var returnData = {
                course_role: courseRole,
                fullname: storage.users[userId-1].fullname,
                user_id: userId
            }

            return [200, returnData, {}];
        });

        // drop user from coruse
        $httpBackend.whenDELETE(/\/api\/courses\/\d+\/users\/\d+$/).respond(function(method, url, data, headers) {
            var userId = url.split('/').pop();

            storage.user_courses[userId] = [];

            var returnData = {
                fullname: storage.users[userId-1].fullname,
                user_id: userId,
                course_role: "Dropped"
            }

            return [200, returnData, {}];
        });

        // update user group in course
        $httpBackend.whenPOST(/\/api\/courses\/\d+\/users\/\d+\/groups\/.+$/).respond(function(method, url, data, headers) {
            var courseId = url.split('/')[3];
            var userId = url.split('/')[5];
            var groupName = url.split('/').pop();

            angular.forEach(storage.user_courses[userId], function(userCoruseInfo) {
                if (userCoruseInfo.courseId == courseId) {
                    userCoruseInfo.groupName = groupName;
                }
            });

            var returnData = {
                "group_name": groupName
            };

            return [200, returnData, {}];
        });

        // remove user from group in course
        $httpBackend.whenDELETE(/\/api\/courses\/\d+\/users\/\d+\/groups$/).respond(function(method, url, data, headers) {
            var courseId = url.split('/')[3];
            var userId = url.split('/')[5];

            angular.forEach(storage.user_courses[userId], function(userCoruseInfo) {
                if (userCoruseInfo.courseId == courseId) {
                    userCoruseInfo.groupName = null;
                }
            });

            var returnData = {
                "course_id": courseId,
                "user_id": userId
            };

            return [200, returnData, {}];
        });

        // get all assignment status in course for current user
        $httpBackend.whenGET(/\/api\/courses\/\d+\/assignments\/status$/).respond(function(method, url, data, headers){
            var courseId = url.split('/')[3];
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);

            statuses = {}

            // setup default data
            if (storage.course_assignments[courseId]) {
                angular.forEach(storage.course_assignments[courseId], function(assignmentId) {
                    statuses[assignmentId] = {
                        "answers": {
                            "answered": false,
                            "count": 0,
                            "draft_ids": [],
                            "has_draft": true
                        },
                        "comparisons": {
                            "available": true,
                            "count": 0,
                            "left": 3
                        }
                    }
                });
            }

            // get all answers in course
            if (storage.course_answers[courseId]) {
                angular.forEach(storage.course_answers[courseId], function(answerId) {
                    var answer = storage.answers[answerId-1];

                    // if answer is by current user, set answered to true for assignment
                    if (answer.user_id == currentUser.id) {
                        statuses[answer.assignment_id]['answers']['answered'] = true;
                        statuses[answer.assignment_id]['answers']['count']++;
                    }
                });
            }

            return [200, {"statuses": statuses}, {}];
        });

        // get current user's criteria
        $httpBackend.whenGET('/api/criteria').respond({
            "objects": storage.criteria
        });

        // create new criterion
        $httpBackend.whenPOST('/api/criteria').respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var id = storage.criteria.length + 1;
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);

            var newCriterion = {
                "id": id,
                "user_id": currentUser.id,
                "name": data.name,
                "description": data.description,
                "default": data.default,
                "compared": false,
                "created": "Mon, 18 Apr 2016 17:38:23 -0000",
                "modified": "Mon, 18 Apr 2016 17:38:23 -0000"
            };

            storage.criteria.push(newCriterion);

            return [200, newCriterion, {}];
        });

        // update criterion by id
        $httpBackend.whenPOST(/\/api\/criteria\/\d+$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);
            var id = url.split('/').pop();

            storage.criteria[id-1] = angular.merge(storage.criteria[id-1], data);

            return [200, storage.criteria[id-1], {}];
        });

        // End Courses



        // Start Assignments

        $httpBackend.whenGET(/\/api\/courses\/\d+\/assignments$/).respond(function(method, url, data, headers) {
            var id = url.replace('/assignments', '').split('/').pop();

            var assignmentList = [];

            if (storage.course_assignments[id]) {
                angular.forEach(storage.course_assignments[id], function(assignmentId) {
                    assignmentList.push(storage.assignments[assignmentId-1]);
                });
            }

            return [200, { 'objects': assignmentList }, {}]
        });

        $httpBackend.whenPOST(/\/api\/courses\/\d+\/assignments$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var courseId = url.replace('/assignments', '').split('/').pop();
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);

            var newAssignment = {
                "id": null,
                "name": null,
                "number_of_comparisons": null,
                "total_comparisons_required": null,
                "total_steps_required": null,
                "answer_end": null,
                "answer_start": null,
                "students_can_reply": null,
                "compare_end": null,
                "compare_start": null,
                "after_comparing": false,
                "answer_period": false,
                "answer_count": 0,
                "available": false,
                "comment_count": 0,
                "criteria": [],
                "evaluation_count": 0,
                "compared": false,
                "compare_period": false,
                "modified": "Wed, 20 Apr 2016 21:50:31 -0000",
                "enable_self_evaluation": false,
                "content": null,
                "file": [],
                "user": angular.copy(currentUser),
                "pairing_algorithm": null,
                "rank_display_limit": null
            }
            newAssignment = angular.merge(newAssignment, data);
            newAssignment.id = storage.assignments.length + 1;
            newAssignment.total_comparisons_required = newAssignment.number_of_comparisons;
            newAssignment.total_steps_required = newAssignment.total_comparisons_required +
                (newAssignment.enable_self_evaluation ? 1 : 0);

            storage.assignments.push(newAssignment);

            if (!storage.course_assignments[courseId]) {
                storage.course_assignments[courseId] = [];
            }
            storage.course_assignments[courseId].push(newAssignment.id)

            return [200, newAssignment, {}]
        });

        $httpBackend.whenPOST(/\/api\/courses\/\d+\/assignments\/\d+$/).respond(function(method, url, data, headers) {
            data = JSON.parse(data);

            var courseId = url.split('/')[3];
            var assignmentId = url.split('/')[5];

            storage.assignments[assignmentId-1] = angular.merge(storage.assignments[assignmentId-1], data);

            return [200, storage.assignments[assignmentId-1], {}]
        });

        $httpBackend.whenPOST(/\/api\/courses\/\d+\/assignments\/\d+\/criteria\/\d+$/).respond({
            'active': true,
            'criterion': default_criterion
        });

        // get assignment by course id and assignment id
        $httpBackend.whenGET(/\/api\/courses\/\d+\/assignments\/\d+$/).respond(function(method, url, data, headers) {
            var courseId = url.split('/')[3];
            var assignmentId = url.split('/')[5];

            return [200, storage.assignments[assignmentId-1], {}]
        });

        // get assignment comments
        $httpBackend.whenGET(/\/api\/courses\/\d+\/assignments\/\d+\/comments$/).respond(function(method, url, data, headers) {
            var courseId = url.split('/')[3];
            var assignmentId = url.split('/')[5];

            return [200, {objects: []}, {}]
        });

        // get assignment status for current user
        $httpBackend.whenGET(/\/api\/courses\/\d+\/assignments\/\d+\/status$/).respond(function(method, url, data, headers){
            var courseId = url.split('/')[3];
            var currentUser = angular.copy(storage.users[storage.loginDetails.id-1]);
            var assignmentId = url.split('/')[5];

            // setup default data
            status = {
                "answers": {
                    "answered": false,
                    "count": 0,
                    "draft_ids": [],
                    "has_draft": true
                },
                "comparisons": {
                    "available": true,
                    "count": 0,
                    "left": 3
                }
            }

            // get all answers in course
            if (storage.course_answers[courseId]) {
                angular.forEach(storage.course_answers[courseId], function(answerId) {
                    var answer = storage.answers[answerId-1];

                    // if answer is by current user for assignment, set answered to true for assignment
                    if (answer.assignment_id == assignmentId && answer.user_id == currentUser.id) {
                        status['answers']['answered'] = true;
                        status['answers']['count']++;
                    }
                });
            }

            return [200, {"status": status}, {}];
        });

        // get assignment answer comments
        $httpBackend.whenGET(/\/api\/courses\/\d+\/assignments\/\d+\/answer_comments\?.*$/).respond(function(method, url, data, headers) {
            var courseId = url.split('/')[3];
            var assignmentId = url.split('/')[5];

            return [200, [], {}]
        });

        // get assignment answers
        $httpBackend.whenGET(/\/api\/courses\/\d+\/assignments\/\d+\/answers\?.*$/).respond(function(method, url, data, headers) {
            var courseId = url.split('/')[3];
            var assignmentId = url.split('/')[5];

            return [200, {
                objects: [],
                page: 1,
                pages: 1,
                per_page: 20,
                total: 0
            }, {}]
        });

        // End Assignments
    })
    .run(function($httpBackend) {
        $httpBackend.whenGET(/.*/).passThrough();
    });
};