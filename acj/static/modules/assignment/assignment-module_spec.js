describe('course-module', function () {
	var $httpBackend, sessionRequestHandler;
	var id = 1;
	var mockSession = {
		"id": id,
		"permissions": {
			"Course": {
				"create": true,
				"delete": true,
				"edit": true,
				"manage": true,
				"read": true
			},
			"Assignment": {
				"create": true,
				"delete": true,
				"edit": true,
				"manage": true,
				"read": true
			},
			"User": {
				"create": true,
				"delete": true,
				"edit": true,
				"manage": true,
				"read": true
			}
		}
	};
	var mockUser = {
		avatar: "63a9f0ea7bb98050796b649e85481845",
		created: "Tue, 27 May 2014 00:02:38 -0000",
		displayname: "root",
		email: null,
		firstname: "John",
		fullname: "John Smith",
		id: id,
		lastname: "Smith",
		last_online: "Tue, 12 Aug 2014 20:53:31 -0000",
		modified: "Tue, 12 Aug 2014 20:53:31 -0000",
		username: "root",
		system_role: "System Administrator"
	};
	var mockCourse = {
		"available": true,
		"created": "Fri, 09 Jan 2015 17:23:59 -0000",
		"description": null,
		"id": 1,
		"modified": "Fri, 09 Jan 2015 17:23:59 -0000",
		"name": "Test Course"
	};
    var mockCritiera = {
        "objects": [
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:50:47 -0000",
                "default": true,
                "description": "<p>Choose the response that you think is the better of the two.</p>",
                "id": 1,
                "modified": "Mon, 06 Jun 2016 19:50:47 -0000",
                "name": "Which is better?",
                "user_id": 1
            },
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:52:10 -0000",
                "default": true,
                "description": "<p>This is a test criteria</p>\n",
                "id": 2,
                "modified": "Mon, 06 Jun 2016 19:52:10 -0000",
                "name": "Test Criteria",
                "user_id": 1
            }
        ]
    };

	var mockAssignment = {
        "after_comparing": false,
        "answer_count": 12,
        "answer_end": "Wed, 15 Jun 2016 06:59:00 -0000",
        "answer_period": true,
        "answer_start": "Thu, 02 Jun 2016 07:00:00 -0000",
        "available": true,
        "comment_count": 3,
        "compare_end": "Wed, 22 Jun 2016 06:59:00 -0000",
        "compare_period": true,
        "compare_start": "Mon, 06 Jun 2016 06:59:00 -0000",
        "compared": true,
        "course_id": 1,
        "created": "Mon, 06 Jun 2016 19:52:27 -0000",
        "criteria": [
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:50:47 -0000",
                "default": true,
                "description": "<p>Choose the response that you think is the better of the two.</p>",
                "id": 1,
                "modified": "Mon, 06 Jun 2016 19:50:47 -0000",
                "name": "Which is better?",
                "user_id": 1
            },
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:52:23 -0000",
                "default": false,
                "description": "",
                "id": 3,
                "modified": "Mon, 06 Jun 2016 19:52:23 -0000",
                "name": "Which sounds better?",
                "user_id": 1
            }
        ],
        "description": "<p>This is the description</p>\n",
        "enable_self_evaluation": true,
        "evaluation_count": 17,
        "file": null,
        "id": 1,
        "modified": "Tue, 07 Jun 2016 22:00:38 -0000",
        "name": "Test Assignment",
        "number_of_comparisons": 3,
        "self_evaluation_count": 4,
        "students_can_reply": true,
        "user": {
            "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
            "displayname": "root",
            "fullname": "thkx UeNV",
            "id": 1
        },
        "user_id": 1
    };

    var mockStudents = {
        "objects": [
            {
                "group_name": "Group 1",
                "id": 3,
                "name": "Student One"
            },
            {
                "group_name": "Group 1",
                "id": 4,
                "name": "Student Two"
            },
            {
                "group_name": "Group 1",
                "id": 5,
                "name": "Student Three"
            },
            {
                "group_name": "Group 1",
                "id": 6,
                "name": "Student Four"
            },
            {
                "group_name": "Group 2",
                "id": 7,
                "name": "Student Five"
            },
            {
                "group_name": "Group 2",
                "id": 8,
                "name": "Student Sx"
            },
            {
                "group_name": "Group 2",
                "id": 9,
                "name": "Student Seven"
            },
            {
                "group_name": "Group 2",
                "id": 10,
                "name": "Student Eight"
            },
            {
                "group_name": "Group 3",
                "id": 11,
                "name": "Student Nine"
            },
            {
                "group_name": null,
                "id": 12,
                "name": "Student Ten"
            }
        ]
    };

    var mockInstructorLabels = {
        "instructors": {
            "1": "Instructor"
        }
    };
    var mockAssignmentComments = {
        "objects": [
            {
                "assignment_id": 1,
                "content": "<p>Hi Everyone!</p>\n",
                "course_id": 1,
                "created": "Tue, 07 Jun 2016 19:43:29 -0000",
                "id": 1,
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": 1
                },
                "user_id": 1
            },
            {
                "assignment_id": 1,
                "content": "<p>Help me please</p>\n",
                "course_id": 1,
                "created": "Tue, 07 Jun 2016 19:43:45 -0000",
                "id": 2,
                "user": {
                    "avatar": "27e062bf3df59edebb5db9f89952c8b3",
                    "displayname": "student6",
                    "fullname": "Student Sx",
                    "id": 8
                },
                "user_id": 8
            },
            {
                "assignment_id": 1,
                "content": "<p>Ok does this help?</p>\n",
                "course_id": 1,
                "created": "Tue, 07 Jun 2016 19:44:23 -0000",
                "id": 3,
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": 1
                },
                "user_id": 1
            }
        ]
    };
    var mockAnswers = {
        "objects": [
            {
                "assignment_id": 1,
                "comment_count": 0,
                "content": "<p>I&#39;m the instructor</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 21:07:57 -0000",
                "file": null,
                "flagged": true,
                "id": 12,
                "private_comment_count": 0,
                "public_comment_count": 0,
                "scores": [],
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": 1
                },
                "user_id": 1
            },
            {
                "assignment_id": 1,
                "comment_count": 0,
                "content": "<p>TA 1</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:40:39 -0000",
                "file": null,
                "flagged": false,
                "id": 11,
                "private_comment_count": 0,
                "public_comment_count": 0,
                "scores": [],
                "user": {
                    "avatar": "b4cd29f38b87efce1490b0755785e237",
                    "displayname": "Instructor One",
                    "fullname": "Instructor One",
                    "id": 2
                },
                "user_id": 2
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Answer 9</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:38:50 -0000",
                "file": null,
                "flagged": false,
                "id": 6,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 100
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 100
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 100
                    }
                ],
                "user": {
                    "avatar": "7c8cd5da17441ff04bf445736964dd16",
                    "displayname": "student9",
                    "fullname": "Student Nine",
                    "id": 11
                },
                "user_id": 11
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Answer 6</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:38:22 -0000",
                "file": null,
                "flagged": false,
                "id": 4,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 78
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 78
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 100
                    }
                ],
                "user": {
                    "avatar": "27e062bf3df59edebb5db9f89952c8b3",
                    "displayname": "student6",
                    "fullname": "Student Sx",
                    "id": 8
                },
                "user_id": 8
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Answer 10</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:38:12 -0000",
                "file": null,
                "flagged": false,
                "id": 3,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 78
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 78
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 78
                    }
                ],
                "user": {
                    "avatar": "2c62e6068c765179e1aed9bc2bfd4689",
                    "displayname": "student10",
                    "fullname": "Student Ten",
                    "id": 12
                },
                "user_id": 12
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Answer 8</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:40:07 -0000",
                "file": null,
                "flagged": false,
                "id": 9,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 68
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 68
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 68
                    }
                ],
                "user": {
                    "avatar": "8aa7fb36a4efbbf019332b4677b528cf",
                    "displayname": "student8",
                    "fullname": "Student Eight",
                    "id": 10
                },
                "user_id": 10
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Answer 5</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:39:01 -0000",
                "file": null,
                "flagged": false,
                "id": 7,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 68
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 36
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 36
                    }
                ],
                "user": {
                    "avatar": "9fd9280a7aa3578c8e853745a5fcc18a",
                    "displayname": "student5",
                    "fullname": "Student Five",
                    "id": 7
                },
                "user_id": 7
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Answer 2</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:38:32 -0000",
                "file": null,
                "flagged": false,
                "id": 5,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 68
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 68
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 36
                    }
                ],
                "user": {
                    "avatar": "213ee683360d88249109c2f92789dbc3",
                    "displayname": "student2",
                    "fullname": "Student Two",
                    "id": 4
                },
                "user_id": 4
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Student 3 Answer</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:37:52 -0000",
                "file": null,
                "flagged": false,
                "id": 2,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 68
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 68
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 36
                    }
                ],
                "user": {
                    "avatar": "8e4947690532bc44a8e41e9fb365b76a",
                    "displayname": "student3",
                    "fullname": "Student Three",
                    "id": 5
                },
                "user_id": 5
            },
            {
                "assignment_id": 1,
                "comment_count": 2,
                "content": "<p>Answer 7</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:40:22 -0000",
                "file": null,
                "flagged": false,
                "id": 10,
                "private_comment_count": 2,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 57
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 36
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 78
                    }
                ],
                "user": {
                    "avatar": "72e8744fc2faa17a83dec9bed06b8b65",
                    "displayname": "student7",
                    "fullname": "Student Seven",
                    "id": 9
                },
                "user_id": 9
            },
            {
                "assignment_id": 1,
                "comment_count": 3,
                "content": "<p>Answer 1</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:39:22 -0000",
                "file": null,
                "flagged": false,
                "id": 8,
                "private_comment_count": 3,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 57
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 57
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 36
                    }
                ],
                "user": {
                    "avatar": "5e5545d38a68148a2d5bd5ec9a89e327",
                    "displayname": "student1",
                    "fullname": "Student One",
                    "id": 3
                },
                "user_id": 3
            },
            {
                "assignment_id": 1,
                "comment_count": 3,
                "content": "<p>Hi there guys</p>\n",
                "course_id": 1,
                "created": "Mon, 06 Jun 2016 20:35:29 -0000",
                "file": null,
                "flagged": false,
                "id": 1,
                "private_comment_count": 3,
                "public_comment_count": 0,
                "scores": [
                    {
                        "criterion_id": 1,
                        "normalized_score": 36
                    },
                    {
                        "criterion_id": 2,
                        "normalized_score": 100
                    },
                    {
                        "criterion_id": 3,
                        "normalized_score": 100
                    }
                ],
                "user": {
                    "avatar": "166a50c910e390d922db4696e4c7747b",
                    "displayname": "student4",
                    "fullname": "Student Four",
                    "id": 6
                },
                "user_id": 6
            }
        ],
        "page": 1,
        "pages": 1,
        "per_page": 20,
        "total": 12
    };

    var mockAnswerComments = [
        {
            "answer_id": 6,
            "assignment_id": 1,
            "comment_type": "Evaluation",
            "content": "<p>kkkk</p>\n",
            "course_id": 1,
            "created": "Mon, 06 Jun 2016 23:03:55 -0000",
            "id": 13,
            "user": {
                "avatar": "27e062bf3df59edebb5db9f89952c8b3",
                "displayname": "student6",
                "fullname": "Student Sx",
                "id": 8
            },
            "user_id": 8
        }
    ];

    var mockGroups = {
        "objects": [
            "Group 1",
            "Group 2",
            "Group 3",
        ]
    };

	beforeEach(module('ubc.ctlt.acj.course'));
	beforeEach(inject(function ($injector) {
		$httpBackend = $injector.get('$httpBackend');
		sessionRequestHandler = $httpBackend.when('GET', '/api/session').respond(mockSession);
		$httpBackend.when('GET', '/api/users/' + id).respond(mockUser);
	}));

	afterEach(function () {
		$httpBackend.verifyNoOutstandingExpectation();
		$httpBackend.verifyNoOutstandingRequest();
	});

	describe('AssignmentViewController', function () {
		var $rootScope, createController, $location, $modal, $q;
		var controller;
        var toaster;

		beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$modal_, _$q_, _Toaster_) {
			$rootScope = _$rootScope_;
			$location = _$location_;
			$modal = _$modal_;
			$q = _$q_;
			toaster = _Toaster_;
			createController = function (route, params) {
				return $controller('AssignmentViewController', {
					$scope: $rootScope,
					$routeParams: params || {},
					$route: route || {}
				});
			}
		}));

        describe('view:', function() {
            beforeEach(function () {
                controller = createController({}, {courseId: 1, assignmentId: 1});
                $httpBackend.expectGET('/api/courses/1/users/students').respond(mockStudents);
                $httpBackend.expectGET('/api/courses/1/assignments/1/comments').respond(mockAssignmentComments);
                $httpBackend.expectGET('/api/courses/1/users/instructors/labels').respond(mockInstructorLabels);
                $httpBackend.expectGET('/api/courses/1/assignments/1').respond(mockAssignment);
                $httpBackend.expectGET('/api/courses/1/groups').respond(mockGroups);
                $httpBackend.expectGET('/api/courses/1/assignments/1/status').respond({
                    "status": {
                        "answers": {
                            "answered": true,
                            "count": 1
                        },
                        "comparisons": {
                            "available": false,
                            "count": 0
                        }
                    }
                });
                $httpBackend.expectGET('/api/courses/1/assignments/1/answer_comments?self_evaluation=only&user_ids='+id).respond([]);
                $httpBackend.expectGET('/api/courses/1/assignments/1/answers?orderBy=1&page=1&perPage=20').respond(mockAnswers);
                $httpBackend.flush();
            });

            it('should be correctly initialized', function () {
                expect($rootScope.assignment.id).toEqual(mockAssignment.id);
                expect($rootScope.criteria).toEqual(mockAssignment.criteria);
                expect($rootScope.courseId).toEqual(mockCourse.id);

                expect($rootScope.allStudents).toEqual(mockStudents.objects);
                expect($rootScope.students).toEqual(mockStudents.objects);

                expect($rootScope.totalNumAnswers).toEqual(mockAnswers.total);

                expect($rootScope.answerFilters).toEqual({
                    page: 1,
                    perPage: 20,
                    group_name: null,
                    author: null,
                    orderBy: mockAssignment.criteria[0].id
                });
                expect($rootScope.reverse).toBe(true);

                expect($rootScope.self_evaluation_req_met).toBe(false);
                expect($rootScope.self_evaluation).toEqual(1);
                expect($rootScope.loggedInUserId).toEqual(id);
                expect($rootScope.assignment.status.comparisons.available).toBe(false);
                expect($rootScope.canManageAssignment).toBe(true);

                expect($rootScope.answerAvail).toEqual(new Date(mockAssignment.compare_end));

                expect($rootScope.compared_req_met).toBe(false);
                expect($rootScope.evaluation).toEqual(mockAssignment.number_of_comparisons);
                expect($rootScope.see_answers).toBe(false);
                expect($rootScope.warning).toBe(false);

                expect($rootScope.comments.objects).toEqual(mockAssignmentComments.objects);

                expect($rootScope.assignment.status.answers.answered).toBe(true);

                expect($rootScope.instructors).toEqual(mockInstructorLabels.instructors);

                expect($rootScope.showTab('answers')).toBe(true);
                expect($rootScope.showTab('help')).toBe(false);
                expect($rootScope.showTab('participation')).toBe(false);
                expect($rootScope.showTab('comparisons')).toBe(false);
            });

            it('should be able to change tabs', function () {
                $rootScope.setTab('help');
                expect($rootScope.showTab('answers')).toBe(false);
                expect($rootScope.showTab('help')).toBe(true);
                expect($rootScope.showTab('participation')).toBe(false);
                expect($rootScope.showTab('comparisons')).toBe(false);

                $rootScope.setTab('participation');
                expect($rootScope.showTab('answers')).toBe(false);
                expect($rootScope.showTab('help')).toBe(false);
                expect($rootScope.showTab('participation')).toBe(true);
                expect($rootScope.showTab('comparisons')).toBe(false);

                $rootScope.setTab('comparisons');
                $httpBackend.expectGET('/api/courses/1/assignments/1/answers/comparisons').respond({
                    "objects": [],
                    "page": 1,
                    "pages": 0,
                    "per_page": 20,
                    "total": 0
                });
                $httpBackend.flush();
                expect($rootScope.showTab('answers')).toBe(false);
                expect($rootScope.showTab('help')).toBe(false);
                expect($rootScope.showTab('participation')).toBe(false);
                expect($rootScope.showTab('comparisons')).toBe(true);
            });

            it('should be able to delete assignment', function () {
                $httpBackend.expectDELETE('/api/courses/1/assignments/1').respond(mockAssignment);
                $rootScope.deleteAssignment(mockAssignment.course_id, mockAssignment.id);
                $httpBackend.flush();
                expect($location.path()).toEqual('/course/1');
            });

            it('should be able to delete answers', function () {
                answer = mockAnswers.objects[0];

                expect($rootScope.assignment.answer_count).toEqual(12);
                expect($rootScope.assignment.status.answers.answered).toBe(true);

                $rootScope.deleteAnswer(answer, mockAssignment.course_id, mockAssignment.id, answer.id);
                $httpBackend.expectDELETE('/api/courses/1/assignments/1/answers/'+answer.id).respond({id: answer.id});
                $httpBackend.flush();

                expect($rootScope.assignment.answer_count).toEqual(11);
                expect($rootScope.assignment.status.answers.answered).toBe(false);
            });

            it('should be able to delete answers', function () {
                answer = mockAnswers.objects[0];

                expect($rootScope.assignment.answer_count).toEqual(12);
                expect($rootScope.assignment.status.answers.answered).toBe(true);

                $rootScope.deleteAnswer(answer, mockAssignment.course_id, mockAssignment.id, answer.id);
                $httpBackend.expectDELETE('/api/courses/1/assignments/1/answers/'+answer.id).respond({id: answer.id});
                $httpBackend.flush();

                expect($rootScope.assignment.answer_count).toEqual(11);
                expect($rootScope.assignment.status.answers.answered).toBe(false);
            });

            it('should be able to unflag answer', function () {
                answer = mockAnswers.objects[0];

                expect(answer.flagged).toBe(true);

                $rootScope.unflagAnswer(answer, mockAssignment.course_id, mockAssignment.id, answer.id);
                $httpBackend.expectPOST('/api/courses/1/assignments/1/answers/'+answer.id+'/flagged').respond({});
                $httpBackend.flush();

                expect(answer.flagged).toBe(false);
            });

            it('should be able to load answer comments', function () {
                answer = mockAnswers.objects[2];

                expect(answer.comments).toEqual(undefined);

                $rootScope.loadComments(answer);
                $httpBackend.expectGET('/api/courses/1/assignments/1/answer_comments?answer_ids='+answer.id).respond(mockAnswerComments);
                $httpBackend.flush();

                expect(answer.comments.length).toEqual(mockAnswerComments.length);
            });

            describe("answer comments", function() {
                var answer;

                beforeEach(function(){
                    answer = mockAnswers.objects[2];
                    $rootScope.loadComments(answer);
                    $httpBackend.expectGET('/api/courses/1/assignments/1/answer_comments?answer_ids='+answer.id).respond(mockAnswerComments);
                    $httpBackend.flush();
                });

                it('should be able to delete answer comments', function () {
                    comment = mockAnswerComments[0];
                    expect(answer.comments.length).toEqual(mockAnswerComments.length);

                    $rootScope.deleteReply(answer, 0, mockAssignment.course_id, mockAssignment.id, answer.id, comment.id);
                    $httpBackend.expectDELETE('/api/courses/1/assignments/1/answers/'+answer.id+'/comments/'+comment.id).respond({
                        id: comment.id
                    });
                    $httpBackend.flush();

                    expect(answer.comments.length).toEqual(mockAnswerComments.length-1);
                });

            });

            it('should be able to delete assignment comments', function () {
                answer = mockAnswers.objects[2];
                comments = angular.copy(mockAssignmentComments.objects);
                comment = comments[0];

                expect($rootScope.comments.objects).toEqual(comments);
                expect($rootScope.assignment.comment_count).toEqual(comments.length);

                $rootScope.deleteComment(0, mockAssignment.course_id, mockAssignment.id, comment.id);
                $httpBackend.expectDELETE('/api/courses/1/assignments/1/comments/'+comment.id).respond({
                    id: comment.id
                });
                $httpBackend.flush();

                comments.shift();

                expect($rootScope.comments.objects).toEqual(comments);
                expect($rootScope.assignment.comment_count).toEqual(comments.length);
            });
        });
	});

    describe('AssignmentWriteController', function () {
		var $rootScope, createController, $location, $modal, $q;
		var controller;
        var defaultCriteria;
        var otherCriteria;

		beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$modal_, _$q_) {
			$rootScope = _$rootScope_;
			$location = _$location_;
			$modal = _$modal_;
			$q = _$q_;
			createController = function (route, params) {
				return $controller('AssignmentWriteController', {
					$scope: $rootScope,
					$routeParams: params || {},
					$route: route || {}
				});
			}
		}));

        describe('new:', function() {
            beforeEach(function () {
                controller = createController({current: {method: 'new'}}, {courseId: 1});
                $httpBackend.expectGET('/api/criteria').respond(mockCritiera);
                $httpBackend.flush();

                defaultCriteria = mockCritiera.objects[0];
                otherCriteria = angular.copy(mockCritiera.objects);
                otherCriteria.shift();
            });

            it('should be correctly initialized', function () {
                expect($rootScope.assignment).toEqual({
                    criteria: [defaultCriteria],
                    students_can_reply: true,
                    number_of_comparisons: 3
                });
                expect($rootScope.recommended_evaluation).toEqual(3);
                expect($rootScope.availableCriteria).toEqual(otherCriteria);
                expect($rootScope.loggedInUserId).toEqual(id);

                expect($rootScope.canManageCriteriaAssignment).toBe(true);
            });

            it('should add criteria to course from available criteria when add is called', function() {
                $rootScope.assignment.criteria = [];
                $rootScope.availableCriteria = [{id: 1}, {id: 2}];
                $rootScope.add(0);
                expect($rootScope.assignment.criteria).toEqual([{id: 1}]);
                expect($rootScope.availableCriteria).toEqual([{id: 2}]);
            });

            it('should remove criteria from course criteria when remove is called', function() {
                $rootScope.assignment.criteria = [{id: 1, default: true}, {id: 2, default: false}];
                $rootScope.availableCriteria = [];
                $rootScope.remove(0);
                // add to available list when default == true
                expect($rootScope.assignment.criteria).toEqual([{id: 2, default: false}]);
                expect($rootScope.availableCriteria).toEqual([{id: 1, default: true}]);

                $rootScope.remove(0);
                // don't add to available list when default == false
                expect($rootScope.assignment.criteria).toEqual([]);
                expect($rootScope.availableCriteria).toEqual([{id: 1, default: true}]);
            });

            describe('when changeCriterion is called', function() {
                var deferred;
                var criterion;
                var closeFunc;
                beforeEach(function() {
                    criterion = {id: 1, name: 'test'};
                    deferred = $q.defer();
                    closeFunc = jasmine.createSpy('close');
                    spyOn($modal, 'open').and.returnValue({result: deferred.promise, close: closeFunc});
                    $rootScope.changeCriterion(criterion);
                });

                it('should open a modal dialog', function() {
                    expect($modal.open).toHaveBeenCalledWith({
                        animation: true,
                        template: '<criterion-form criterion=criterion></criterion-form>',
                        scope: jasmine.any(Object)
                    })
                });

                it('should listen on CRITERION_UPDATED event and close dialog', function() {
                    var updated = {id: 1, name: 'test1'};
                    $rootScope.$broadcast("CRITERION_UPDATED", updated);
                    expect(criterion).toEqual(updated);
                    expect(closeFunc).toHaveBeenCalled();
                });

                it('should listen to CRITERION_ADDED event and close dialog', function() {
                    $rootScope.assignment.criteria = [];
                    var criteria = {id: 1};
                    $rootScope.$broadcast("CRITERION_ADDED", criteria);
                    expect($rootScope.assignment.criteria).toEqual([criteria]);
                    expect(closeFunc).toHaveBeenCalled();
                });

                it('should un-register listener when dialog is closed', function() {
                    deferred.resolve();
                    $rootScope.$digest();
                    $rootScope.$broadcast('CRITERION_UPDATED');
                    expect(closeFunc).not.toHaveBeenCalled();
                });
            });

            describe('save', function() {
                var toaster;
                beforeEach(inject(function (_Toaster_) {
                    toaster = _Toaster_;
                    spyOn(toaster, 'error');
                }));

                it('should error when answer start is not before answer end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.date.aend.date = $rootScope.date.astart.date;
                    $rootScope.date.aend.time = $rootScope.date.astart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.error).toHaveBeenCalledWith('Answer Period Error', 'Answer end time must be after answer start time.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should error when answer start is not before compare start', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cstart.date = angular.copy($rootScope.date.astart.date);
                    $rootScope.date.cstart.date.setDate($rootScope.date.cstart.date.getDate()-1);
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.error).toHaveBeenCalledWith('Time Period Error', 'Please double-check the answer and evaluation period start and end times.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should error when compare start is not before compare end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cend.date = $rootScope.date.cstart.date;
                    $rootScope.date.cend.time = $rootScope.date.cstart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.error).toHaveBeenCalledWith('Time Period Error', 'Evauluation end time must be after evauluation start time.');
                    expect($location.path()).toEqual(currentPath);
                });

				it('should enable save button even if save failed', function() {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;

                    $httpBackend.expectPOST('/api/courses/1/assignments', $rootScope.assignment)
                        .respond(400, '');
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
					expect($rootScope.submitted).toBe(false);
				});

                it('should be able to save new assignment', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;

                    $httpBackend.expectPOST('/api/courses/1/assignments', $rootScope.assignment)
                        .respond(angular.merge({}, mockAssignment, {id: 2}));
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1');
                    expect($rootScope.submitted).toBe(false);
                });
            });
        });

        describe('edit:', function() {
            beforeEach(function () {
                controller = createController({current: {method: 'edit'}}, {courseId: 1, assignmentId: 1});
                $httpBackend.expectGET('/api/courses/1/assignments/1').respond(mockAssignment);
                $httpBackend.expectGET('/api/criteria').respond(mockCritiera);
                $httpBackend.flush();

                defaultCriteria = mockCritiera.objects[0];
                otherCriteria = angular.copy(mockCritiera.objects);
                otherCriteria.shift();
            });

            it('should be correctly initialized', function () {
                expect($rootScope.assignment.id).toEqual(mockAssignment.id);
                expect($rootScope.assignment.criteria).toEqual(mockAssignment.criteria);
                expect($rootScope.compared).toEqual(mockAssignment.compared);

                expect($rootScope.recommended_evaluation).toEqual(3);
                expect($rootScope.availableCriteria).toEqual(otherCriteria);
                expect($rootScope.loggedInUserId).toEqual(id);

                expect($rootScope.canManageCriteriaAssignment).toBe(true);
            });

            it('should add criteria to course from available criteria when add is called', function() {
                $rootScope.assignment.criteria = [];
                $rootScope.availableCriteria = [{id: 1}, {id: 2}];
                $rootScope.add(0);
                expect($rootScope.assignment.criteria).toEqual([{id: 1}]);
                expect($rootScope.availableCriteria).toEqual([{id: 2}]);
            });

            it('should remove criteria from course criteria when remove is called', function() {
                $rootScope.assignment.criteria = [{id: 1, default: true}, {id: 2, default: false}];
                $rootScope.availableCriteria = [];
                $rootScope.remove(0);
                // add to available list when default == true
                expect($rootScope.assignment.criteria).toEqual([{id: 2, default: false}]);
                expect($rootScope.availableCriteria).toEqual([{id: 1, default: true}]);

                $rootScope.remove(0);
                // don't add to available list when default == false
                expect($rootScope.assignment.criteria).toEqual([]);
                expect($rootScope.availableCriteria).toEqual([{id: 1, default: true}]);
            });

            describe('when changeCriterion is called', function() {
                var deferred;
                var criterion;
                var closeFunc;
                beforeEach(function() {
                    criterion = {id: 1, name: 'test'};
                    deferred = $q.defer();
                    closeFunc = jasmine.createSpy('close');
                    spyOn($modal, 'open').and.returnValue({result: deferred.promise, close: closeFunc});
                    $rootScope.changeCriterion(criterion);
                });

                it('should open a modal dialog', function() {
                    expect($modal.open).toHaveBeenCalledWith({
                        animation: true,
                        template: '<criterion-form criterion=criterion></criterion-form>',
                        scope: jasmine.any(Object)
                    })
                });

                it('should listen on CRITERION_UPDATED event and close dialog', function() {
                    var updated = {id: 1, name: 'test1'};
                    $rootScope.$broadcast("CRITERION_UPDATED", updated);
                    expect(criterion).toEqual(updated);
                    expect(closeFunc).toHaveBeenCalled();
                });

                it('should listen to CRITERION_ADDED event and close dialog', function() {
                    $rootScope.assignment.criteria = [];
                    var criteria = {id: 1};
                    $rootScope.$broadcast("CRITERION_ADDED", criteria);
                    expect($rootScope.assignment.criteria).toEqual([criteria]);
                    expect(closeFunc).toHaveBeenCalled();
                });

                it('should un-register listener when dialog is closed', function() {
                    deferred.resolve();
                    $rootScope.$digest();
                    $rootScope.$broadcast('CRITERION_UPDATED');
                    expect(closeFunc).not.toHaveBeenCalled();
                });
            });

            describe('save', function() {
                var toaster;
                beforeEach(inject(function (_Toaster_) {
                    toaster = _Toaster_;
                    spyOn(toaster, 'error');
                }));

                it('should error when answer start is not before answer end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.date.aend.date = $rootScope.date.astart.date;
                    $rootScope.date.aend.time = $rootScope.date.astart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.error).toHaveBeenCalledWith('Answer Period Error', 'Answer end time must be after answer start time.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should error when answer start is not before compare start', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cstart.date = angular.copy($rootScope.date.astart.date);
                    $rootScope.date.cstart.date.setDate($rootScope.date.cstart.date.getDate()-1);
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.error).toHaveBeenCalledWith('Time Period Error', 'Please double-check the answer and evaluation period start and end times.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should error when compare start is not before compare end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cend.date = $rootScope.date.cstart.date;
                    $rootScope.date.cend.time = $rootScope.date.cstart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.error).toHaveBeenCalledWith('Time Period Error', 'Evauluation end time must be after evauluation start time.');
                    expect($location.path()).toEqual(currentPath);
                });

				it('should enable save button even if save failed', function() {
                    $rootScope.assignment = angular.copy(mockAssignment);

                    $httpBackend.expectPOST('/api/courses/1/assignments/1', $rootScope.assignment)
                        .respond(400, '');
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
					expect($rootScope.submitted).toBe(false);
				});

                it('should be able to save new assignment', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);

                    $httpBackend.expectPOST('/api/courses/1/assignments/1', $rootScope.assignment)
                        .respond($rootScope.assignment);
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1');
                    expect($rootScope.submitted).toBe(false);
                });
            });
        });
	});
});