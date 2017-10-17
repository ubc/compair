describe('assignment-module', function () {
    var $httpBackend, sessionRequestHandler;
    var id = "1abcABC123-abcABC123_Z";
    var mockSession = {
        "id": id,
        "permissions": {
            "Course": {
                "global": [
                    "create",
                    "delete",
                    "edit",
                    "manage",
                    "read"
                ]
            },
            "Assignment": {
                "global": [
                    "create",
                    "delete",
                    "edit",
                    "manage",
                    "read"
                ]
            },
            "User": {
                "global": [
                    "create",
                    "delete",
                    "edit",
                    "manage",
                    "read"
                ]
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
        system_role: "System Administrator",
        uses_compair_login: true,
        email_notification_method: 'enable'
    };
    var mockCourse = {
        "available": true,
        "start_date": null,
        "end_date": null,
        "assignment_count": 0,
        "student_assignment_count": 0,
        "student_count": 0,
        "created": "Fri, 09 Jan 2015 17:23:59 -0000",
        "id": "1abcABC123-abcABC123_Z",
        "modified": "Fri, 09 Jan 2015 17:23:59 -0000",
        "name": "Test Course",
        "year": 2015,
        "term": "Winter",
        "start_time": null,
        "end_time": null
    };
    var mockCritiera = {
        "objects": [
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:50:47 -0000",
                "default": true,
                "public": true,
                "description": "<p>Choose the response that you think is the better of the two.</p>",
                "id": "1abcABC123-abcABC123_Z",
                "modified": "Mon, 06 Jun 2016 19:50:47 -0000",
                "name": "Which is better?",
                "user_id": "1abcABC123-abcABC123_Z"
            },
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:52:10 -0000",
                "default": true,
                "public": false,
                "description": "<p>This is a test criteria</p>\n",
                "id": "2abcABC123-abcABC123_Z",
                "modified": "Mon, 06 Jun 2016 19:52:10 -0000",
                "name": "Test Criteria",
                "user_id": "1abcABC123-abcABC123_Z"
            }
        ]
    };

    var mockAssignment = {
        "after_comparing": false,
        "answer_count": 12,
        "top_answer_count": 0,
        "answer_end": "Wed, 15 Jun 2016 06:59:00 -0000",
        "answer_period": true,
        "answer_start": "Thu, 02 Jun 2016 07:00:00 -0000",
        "available": true,
        "comment_count": 3,
        "compare_end": "Wed, 22 Jun 2016 06:59:00 -0000",
        "compare_period": true,
        "compare_start": "Mon, 06 Jun 2016 06:59:00 -0000",
        "compared": false,
        "course_id": "1abcABC123-abcABC123_Z",
        "created": "Mon, 06 Jun 2016 19:52:27 -0000",
        "criteria": [
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:50:47 -0000",
                "default": true,
                "public": true,
                "description": "<p>Choose the response that you think is the better of the two.</p>",
                "id": "1abcABC123-abcABC123_Z",
                "modified": "Mon, 06 Jun 2016 19:50:47 -0000",
                "name": "Which is better?",
                "user_id": "1abcABC123-abcABC123_Z",
                "weight": 1
            },
            {
                "compared": true,
                "created": "Mon, 06 Jun 2016 19:52:23 -0000",
                "default": false,
                "public": false,
                "description": "",
                "id": "3abcABC123-abcABC123_Z",
                "modified": "Mon, 06 Jun 2016 19:52:23 -0000",
                "name": "Which sounds better?",
                "user_id": "1abcABC123-abcABC123_Z",
                "weight": 1
            }
        ],
        "description": "<p>This is the description</p>\n",
        "peer_feedback_prompt": null,
        "enable_self_evaluation": true,
        "evaluation_count": 17,
        "file": null,
        "id": "1abcABC123-abcABC123_Z",
        "modified": "Tue, 07 Jun 2016 22:00:38 -0000",
        "name": "Test Assignment",
        "number_of_comparisons": 3,
        "total_comparisons_required": 3,
        "total_steps_required": 4,
        "self_evaluation_count": 4,
        "students_can_reply": true,
        "user": {
            "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
            "displayname": "root",
            "fullname": "thkx UeNV",
            "id": "1abcABC123-abcABC123_Z"
        },
        "user_id": "1abcABC123-abcABC123_Z",
        "pairing_algorithm": "random",
        "educators_can_compare": false,
        "rank_display_limit": 10
    };

    var mockStudents = {
        "objects": [
            {
                "group_name": "Group 1",
                "id": "3abcABC123-abcABC123_Z",
                "name": "Student One"
            },
            {
                "group_name": "Group 1",
                "id": "4abcABC123-abcABC123_Z",
                "name": "Student Two"
            },
            {
                "group_name": "Group 1",
                "id": "5abcABC123-abcABC123_Z",
                "name": "Student Three"
            },
            {
                "group_name": "Group 1",
                "id": "6abcABC123-abcABC123_Z",
                "name": "Student Four"
            },
            {
                "group_name": "Group 2",
                "id": "7abcABC123-abcABC123_Z",
                "name": "Student Five"
            },
            {
                "group_name": "Group 2",
                "id": "8abcABC123-abcABC123_Z",
                "name": "Student Sx"
            },
            {
                "group_name": "Group 2",
                "id": "9abcABC123-abcABC123_Z",
                "name": "Student Seven"
            },
            {
                "group_name": "Group 2",
                "id": "10bcABC123-abcABC123_Z",
                "name": "Student Eight"
            },
            {
                "group_name": "Group 3",
                "id": "11bcABC123-abcABC123_Z",
                "name": "Student Nine"
            },
            {
                "group_name": null,
                "id": "12bcABC123-abcABC123_Z",
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
                "assignment_id": "1abcABC123-abcABC123_Z",
                "content": "<p>Hi Everyone!</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Tue, 07 Jun 2016 19:43:29 -0000",
                "id": "1abcABC123-abcABC123_Z",
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": "1abcABC123-abcABC123_Z"
                },
                "user_id": "1abcABC123-abcABC123_Z",
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "content": "<p>Help me please</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Tue, 07 Jun 2016 19:43:45 -0000",
                "id": "2abcABC123-abcABC123_Z",
                "user": {
                    "avatar": "27e062bf3df59edebb5db9f89952c8b3",
                    "displayname": "student6",
                    "fullname": "Student Sx",
                    "id": "8abcABC123-abcABC123_Z",
                },
                "user_id": "8abcABC123-abcABC123_Z",
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "content": "<p>Ok does this help?</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Tue, 07 Jun 2016 19:44:23 -0000",
                "id": "3abcABC123-abcABC123_Z",
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": "1abcABC123-abcABC123_Z"
                },
                "user_id": "1abcABC123-abcABC123_Z"
            }
        ]
    };
    var mockAnswers = {
        "objects": [
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 0,
                "content": "<p>I&#39;m the instructor</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 21:07:57 -0000",
                "file": null,
                "flagged": true,
                "top_answer": false,
                "id": "12bcABC123-abcABC123_Z",
                "private_comment_count": 0,
                "public_comment_count": 0,
                "score": null,
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": "1abcABC123-abcABC123_Z"
                },
                "user_id": "1abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 0,
                "content": "<p>I&#39;m the instructor</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 21:07:57 -0000",
                "file": null,
                "flagged": true,
                "top_answer": false,
                "id": "100cABC123-abcABC123_Z",
                "private_comment_count": 0,
                "public_comment_count": 0,
                "score": null,
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": "1abcABC123-abcABC123_Z"
                },
                "user_id": "1abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 0,
                "content": "<p>I&#39;m the instructor's second answer</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 21:07:57 -0000",
                "file": null,
                "flagged": true,
                "top_answer": false,
                "id": "101cABC123-abcABC123_Z",
                "private_comment_count": 0,
                "public_comment_count": 0,
                "score": null,
                "user": {
                    "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                    "displayname": "root",
                    "fullname": "thkx UeNV",
                    "id": "1abcABC123-abcABC123_Z"
                },
                "user_id": "1abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 0,
                "content": "<p>TA 1</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:40:39 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "11bcABC123-abcABC123_Z",
                "private_comment_count": 0,
                "public_comment_count": 0,
                "score": null,
                "user": {
                    "avatar": "b4cd29f38b87efce1490b0755785e237",
                    "displayname": "Instructor One",
                    "fullname": "Instructor One",
                    "id": "2abcABC123-abcABC123_Z"
                },
                "user_id": "2abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Answer 9</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:38:50 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "6abcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 1,
                    "normalized_score": 100
                },
                "user": {
                    "avatar": "7c8cd5da17441ff04bf445736964dd16",
                    "displayname": "student9",
                    "fullname": "Student Nine",
                    "id": "11bcABC123-abcABC123_Z"
                },
                "user_id": "11bcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Answer 6</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:38:22 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "4abcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 2,
                    "normalized_score": 78
                },
                "user": {
                    "avatar": "27e062bf3df59edebb5db9f89952c8b3",
                    "displayname": "student6",
                    "fullname": "Student Sx",
                    "id": "8abcABC123-abcABC123_Z"
                },
                "user_id": "8abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Answer 10</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:38:12 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "3abcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 2,
                    "normalized_score": 78
                },
                "user": {
                    "avatar": "2c62e6068c765179e1aed9bc2bfd4689",
                    "displayname": "student10",
                    "fullname": "Student Ten",
                    "id": "12bcABC123-abcABC123_Z"
                },
                "user_id": "12abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Answer 8</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:40:07 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "9abcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 4,
                    "normalized_score": 68
                },
                "user": {
                    "avatar": "8aa7fb36a4efbbf019332b4677b528cf",
                    "displayname": "student8",
                    "fullname": "Student Eight",
                    "id": "10bcABC123-abcABC123_Z"
                },
                "user_id": "10bcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Answer 5</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:39:01 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "7abcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 4,
                    "normalized_score": 68
                },
                "user": {
                    "avatar": "9fd9280a7aa3578c8e853745a5fcc18a",
                    "displayname": "student5",
                    "fullname": "Student Five",
                    "id": "7abcABC123-abcABC123_Z"
                },
                "user_id": "7abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Answer 2</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:38:32 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "5abcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 4,
                    "normalized_score": 68
                },
                "user": {
                    "avatar": "213ee683360d88249109c2f92789dbc3",
                    "displayname": "student2",
                    "fullname": "Student Two",
                    "id": "4abcABC123-abcABC123_Z"
                },
                "user_id": "4abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Student 3 Answer</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:37:52 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "2abcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 4,
                    "normalized_score": 68
                },
                "user": {
                    "avatar": "8e4947690532bc44a8e41e9fb365b76a",
                    "displayname": "student3",
                    "fullname": "Student Three",
                    "id": "5abcABC123-abcABC123_Z"
                },
                "user_id": "5abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 2,
                "content": "<p>Answer 7</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:40:22 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "10bcABC123-abcABC123_Z",
                "private_comment_count": 2,
                "public_comment_count": 0,
                "score": {
                    "rank": 9,
                    "normalized_score": 57
                },
                "user": {
                    "avatar": "72e8744fc2faa17a83dec9bed06b8b65",
                    "displayname": "student7",
                    "fullname": "Student Seven",
                    "id": "9abcABC123-abcABC123_Z",
                },
                "user_id": "9abcABC123-abcABC123_Z",
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 3,
                "content": "<p>Answer 1</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:39:22 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "8abcABC123-abcABC123_Z",
                "private_comment_count": 3,
                "public_comment_count": 0,
                "score": {
                    "rank": 9,
                    "normalized_score": 57
                },
                "user": {
                    "avatar": "5e5545d38a68148a2d5bd5ec9a89e327",
                    "displayname": "student1",
                    "fullname": "Student One",
                    "id": "3abcABC123-abcABC123_Z"
                },
                "user_id": "3abcABC123-abcABC123_Z"
            },
            {
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "comment_count": 3,
                "content": "<p>Hi there guys</p>\n",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Mon, 06 Jun 2016 20:35:29 -0000",
                "file": null,
                "flagged": false,
                "top_answer": false,
                "id": "1abcABC123-abcABC123_Z",
                "private_comment_count": 3,
                "public_comment_count": 0,
                "score": {
                    "rank": 11,
                    "normalized_score": 36
                },
                "user": {
                    "avatar": "166a50c910e390d922db4696e4c7747b",
                    "displayname": "student4",
                    "fullname": "Student Four",
                    "id": "6abcABC123-abcABC123_Z"
                },
                "user_id": "6abcABC123-abcABC123_Z"
            }
        ],
        "page": 1,
        "pages": 1,
        "per_page": 20,
        "total": 12
    };

    var mockAnswerComments = [
        {
            "answer_id": "6abcABC123-abcABC123_Z",
            "assignment_id": "1abcABC123-abcABC123_Z",
            "comment_type": "Evaluation",
            "content": "<p>kkkk</p>\n",
            "course_id": "1abcABC123-abcABC123_Z",
            "created": "Mon, 06 Jun 2016 23:03:55 -0000",
            "id": "13bcABC123-abcABC123_Z",
            "user": {
                "avatar": "27e062bf3df59edebb5db9f89952c8b3",
                "displayname": "student6",
                "fullname": "Student Sx",
                "id": "8abcABC123-abcABC123_Z",
            },
            "user_id": "8abcABC123-abcABC123_Z",
        }
    ];

    var mockGroups = {
        "objects": [
            "Group 1",
            "Group 2",
            "Group 3",
        ]
    };

    var mockComparisonExamplesEmpty = {
        "objects": []
    }

    var mockComparisonExamples = {
        "objects": [
            {
                "answer1": {
                    "assignment_id": "1abcABC123-abcABC123_Z",
                    "course_id": "1abcABC123-abcABC123_Z",
                    "comment_count": 0,
                    "content": "<p>I&#39;m the instructor</p>\n",
                    "course_id": "1abcABC123-abcABC123_Z",
                    "created": "Mon, 06 Jun 2016 21:07:57 -0000",
                    "file": null,
                    "flagged": true,
                    "top_answer": false,
                    "id": "100cABC123-abcABC123_Z",
                    "private_comment_count": 0,
                    "public_comment_count": 0,
                    "score": null,
                    "user": {
                        "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                        "displayname": "root",
                        "fullname": "thkx UeNV",
                        "id": "1abcABC123-abcABC123_Z"
                    },
                    "user_id": "1abcABC123-abcABC123_Z"
                },
                "answer1_id": "100cABC123-abcABC123_Z",
                "answer2": {
                    "assignment_id": "1abcABC123-abcABC123_Z",
                    "course_id": "1abcABC123-abcABC123_Z",
                    "comment_count": 0,
                    "content": "<p>I&#39;m the instructor's second answer</p>\n",
                    "course_id": "1abcABC123-abcABC123_Z",
                    "created": "Mon, 06 Jun 2016 21:07:57 -0000",
                    "file": null,
                    "flagged": true,
                    "top_answer": false,
                    "id": "101cABC123-abcABC123_Z",
                    "private_comment_count": 0,
                    "public_comment_count": 0,
                    "score": null,
                    "user": {
                        "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
                        "displayname": "root",
                        "fullname": "thkx UeNV",
                        "id": "1abcABC123-abcABC123_Z"
                    },
                    "user_id": "1abcABC123-abcABC123_Z"
                },
                "answer2_id": "101cABC123-abcABC123_Z",
                "assignment_id": "1abcABC123-abcABC123_Z",
                "course_id": "1abcABC123-abcABC123_Z",
                "created": "Wed, 17 Aug 2016 16:38:27 -0000",
                "id": "1abcABC123-abcABC123_Z",
                "modified": "Wed, 17 Aug 2016 16:38:27 -0000"
            }
        ]
    };


    beforeEach(module('ubc.ctlt.compair.course'));
    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
        sessionRequestHandler = $httpBackend.when('GET', '/api/session').respond(mockSession);
        $httpBackend.when('GET', '/api/users/' + id).respond(mockUser);
        $httpBackend.whenPOST(/\/api\/statements$/).respond(function(method, url, data, headers) {
            return [200, { 'success':true }, {}];
        });
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('AssignmentViewController', function () {
        var $rootScope, createController, $location, $uibModal, $q, $route;
        var controller;
        var toaster;
        var xAPISettings;

        beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$uibModal_, _$q_, _Toaster_, _xAPISettings_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            $uibModal = _$uibModal_;
            $q = _$q_;
            toaster = _Toaster_;
            createController = function (params, resolvedData) {
                return $controller('AssignmentViewController', {
                    $scope: $rootScope,
                    $routeParams: params || {},
                    resolvedData: resolvedData || {}
                });
            }
            xAPISettings = _xAPISettings_;
            xAPISettings.enabled = true;
            xAPISettings.baseUrl = "https://localhost:8888/";
        }));

        describe('view:', function() {
            beforeEach(function () {
                controller = createController({courseId: "1abcABC123-abcABC123_Z", assignmentId: "1abcABC123-abcABC123_Z"}, {
                    course: angular.copy(mockCourse),
                    assignment: angular.copy(mockAssignment),
                    students: angular.copy(mockStudents),
                    instructorLabels: angular.copy(mockInstructorLabels),
                    loggedInUser: angular.copy(mockUser),
                    canManageAssignment: true,
                });
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/status').respond({
                    "status": {
                        "answers": {
                            "answered": true,
                            "count": 1,
                            "draft_ids": [],
                            "has_draft": true
                        },
                        "comparisons": {
                            "available": false,
                            "count": 0,
                            "left": 3,
                            "self_evaluation_completed": false
                        }
                    }
                });
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/groups').respond(mockGroups);
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answers?page=1&perPage=20').respond(mockAnswers);
                $httpBackend.flush();
            });

            it('should be correctly initialized', function () {
                var expectedStudents = _.sortBy(angular.copy(mockStudents.objects), 'name');
                expectedStudents.unshift({
                    id: "top-picks",
                    name: "Instructor's top picks"
                });

                expect($rootScope.assignment.id).toEqual(mockAssignment.id);
                expect($rootScope.courseId).toEqual(mockCourse.id);

                expect($rootScope.allStudents).toEqual(mockStudents.objects);
                expect($rootScope.students).toEqual(expectedStudents);

                expect($rootScope.totalNumAnswers).toEqual(mockAnswers.total);

                expect($rootScope.answerFilters).toEqual({
                    page: 1,
                    perPage: 20,
                    group: null,
                    author: null,
                    top: null,
                    anonymous: null,
                    orderBy: null
                });

                expect($rootScope.self_evaluation_needed).toBe(true);
                expect($rootScope.loggedInUserId).toEqual(id);
                expect($rootScope.assignment.status.comparisons.available).toBe(false);
                expect($rootScope.canManageAssignment).toBe(true);

                expect($rootScope.answerAvail).toEqual(new Date(mockAssignment.compare_end));

                expect($rootScope.comparisons_left).toEqual(mockAssignment.total_comparisons_required);
                expect($rootScope.see_answers).toBe(false);
                expect($rootScope.warning).toBe(false);

                expect($rootScope.assignment.status.answers.answered).toBe(true);

                expect($rootScope.instructors).toEqual(mockInstructorLabels.instructors);

                expect($rootScope.showTab('answers')).toBe(true);
            });

            it('should be able to change to answers tab', function () {
                $rootScope.setTab('answers');
                $rootScope.$emit('$routeUpdate');
                expect($rootScope.showTab('answers')).toBe(true);
            });

            it('should be able to change to help tab', function () {
                $rootScope.setTab('help');
                $rootScope.$emit('$routeUpdate');
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/comments').respond(mockAssignmentComments);
                $httpBackend.flush();
                expect($rootScope.showTab('help')).toBe(true);
            });

            it('should be able to change to participation tab', function () {
                $rootScope.setTab('participation');
                $rootScope.$emit('$routeUpdate');
                expect($rootScope.showTab('participation')).toBe(true);
            });

            it('should be able to change to your work tab', function () {
                $rootScope.setTab('your_work');
                $rootScope.$emit('$routeUpdate');
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/user/comparisons').respond({
                    "comparisons": [],
                    "self_evaluations": []
                });
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answers?author=1abcABC123-abcABC123_Z').respond({
                    "objects": [],
                    "page": 1,
                    "pages": 0,
                    "per_page": 20,
                    "total": 0
                });
                $httpBackend.flush();
                expect($rootScope.showTab('your_work')).toBe(true);
            });

            it('should be able to change to comparisons tab', function () {
                $rootScope.setTab('comparisons');
                $rootScope.$emit('$routeUpdate');
                expect($rootScope.showTab('comparisons')).toBe(true);
            });

            it('should be able to delete assignment', function () {
                $httpBackend.expectDELETE('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z').respond(mockAssignment);
                $rootScope.deleteAssignment(mockAssignment);
                $httpBackend.flush();
                expect($location.path()).toEqual('/course/1abcABC123-abcABC123_Z');
            });

            it('should be able to delete answers', function () {
                answer = mockAnswers.objects[0];

                expect($rootScope.assignment.answer_count).toEqual(12);
                expect($rootScope.assignment.status.answers.answered).toBe(true);

                $rootScope.deleteAnswer(answer);
                $httpBackend.expectDELETE('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answers/'+answer.id).respond({id: answer.id});
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answers?page=1&perPage=20').respond(mockAnswers);
                $httpBackend.flush();

                expect($rootScope.assignment.answer_count).toEqual(11);
                expect($rootScope.assignment.status.answers.answered).toBe(false);
            });

            it('should be able to toggle top answer state', function () {
                answer = mockAnswers.objects[0];

                expect(answer.top_answer).toBe(false);

                $rootScope.setTopAnswer(answer, true);
                $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answers/'+answer.id+'/top').respond({});
                $httpBackend.flush();

                expect(answer.top_answer).toBe(true);

                $rootScope.setTopAnswer(answer, false);
                $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answers/'+answer.id+'/top').respond({});
                $httpBackend.flush();

                expect(answer.top_answer).toBe(false);
            });


            it('should be able to load answer comments', function () {
                answer = mockAnswers.objects[2];

                expect(answer.comments).toEqual(undefined);

                $rootScope.loadComments(answer);
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answer_comments?answer_ids='+answer.id).respond(mockAnswerComments);
                $httpBackend.flush();

                expect(answer.comments.length).toEqual(mockAnswerComments.length);
            });

            describe("answer comments", function() {
                var answer;

                beforeEach(function(){
                    answer = mockAnswers.objects[2];
                    $rootScope.loadComments(answer);
                    $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answer_comments?answer_ids='+answer.id).respond(mockAnswerComments);
                    $httpBackend.flush();
                });

                it('should be able to delete answer comments', function () {
                    comment = mockAnswerComments[0];
                    expect(answer.comments.length).toEqual(mockAnswerComments.length);

                    $rootScope.deleteReply(answer, 0, mockAssignment.course_id, mockAssignment.id, answer.id, comment.id);
                    $httpBackend.expectDELETE('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/answers/'+answer.id+'/comments/'+comment.id).respond({
                        id: comment.id
                    });
                    $httpBackend.flush();

                    expect(answer.comments.length).toEqual(mockAnswerComments.length-1);
                });

            });

            describe("assignment comments", function() {

                beforeEach(function(){
                    $rootScope.setTab('help');
                    $rootScope.$emit('$routeUpdate');
                    $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/comments').respond(mockAssignmentComments);
                    $httpBackend.flush();
                });

                it('should be properly initialized', function() {
                    expect($rootScope.comments.objects).toEqual(mockAssignmentComments.objects);
                });

                it('should be able to delete assignment comments', function () {
                    comments = angular.copy(mockAssignmentComments.objects);
                    comment = comments[0];

                    expect($rootScope.comments.objects).toEqual(comments);
                    expect($rootScope.assignment.comment_count).toEqual(comments.length);

                    $rootScope.deleteComment(0, mockAssignment.course_id, mockAssignment.id, comment.id);
                    $httpBackend.expectDELETE('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/comments/'+comment.id).respond({
                        id: comment.id
                    });
                    $httpBackend.flush();

                    comments.shift();

                    expect($rootScope.comments.objects).toEqual(comments);
                    expect($rootScope.assignment.comment_count).toEqual(comments.length);
                });
            });

        });
    });

    describe('AssignmentWriteController', function () {
        var $rootScope, createController, $location, $uibModal, $q, modalInstance, $route;
        var controller;
        var defaultCriteria;
        var otherCriteria;

        beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$uibModal_, _$q_, _$route_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            $uibModal = _$uibModal_;
            $q = _$q_;
            $route = _$route_;
            $route.current = {};
            createController = function (params, resolvedData) {
                return $controller('AssignmentWriteController', {
                    $scope: $rootScope,
                    $routeParams: params || {},
                    $route: $route,
                    resolvedData: resolvedData || {}
                });
            }
        }));

        describe('create:', function() {
            beforeEach(function () {
                controller = createController({courseId: "1abcABC123-abcABC123_Z"}, {
                    course: angular.copy(mockCourse),
                    criteria: angular.copy(mockCritiera),
                    loggedInUser: angular.copy(mockUser),
                    canManageAssignment: true,
                });

                defaultCriteria = angular.merge({}, mockCritiera.objects[0], { weight:1 });
                otherCriteria = angular.copy(mockCritiera.objects);
                otherCriteria.shift();
                otherCriteria.forEach(function(criterion) {
                    criterion.weight = 1;
                });
            });

            it('should be correctly initialized', function () {
                expect($rootScope.assignment).toEqual({
                    criteria: [defaultCriteria],
                    students_can_reply: false,
                    educators_can_compare: false,
                    number_of_comparisons: 3,
                    pairing_algorithm: 'adaptive_min_delta',
                    rank_display_limit: null,
                    answer_grade_weight: 1,
                    comparison_grade_weight: 1,
                    self_evaluation_grade_weight: 1
                });
                expect($rootScope.recommended_comparisons).toEqual(3);
                expect($rootScope.availableCriteria).toEqual(otherCriteria);
                expect($rootScope.loggedInUserId).toEqual(id);
                expect($rootScope.comparison_example).toEqual({
                    answer1: {},
                    answer2: {}
                });

                expect($rootScope.canManageAssignment).toBe(true);
            });

            it('should add criteria to course from available criteria when add is called', function() {
                $rootScope.assignment.criteria = [];
                $rootScope.availableCriteria = [{id: "1abcABC123-abcABC123_Z"}, {id: "2abcABC123-abcABC123_Z"}];
                $rootScope.add(0);
                expect($rootScope.assignment.criteria).toEqual([{id: "1abcABC123-abcABC123_Z"}]);
                expect($rootScope.availableCriteria).toEqual([{id: "2abcABC123-abcABC123_Z"}]);
            });

            it('should remove criteria from course criteria when remove is called', function() {
                $rootScope.assignment.criteria = [{id: "1abcABC123-abcABC123_Z", default: true}, {id: "2abcABC123-abcABC123_Z", default: false}];
                $rootScope.availableCriteria = [];
                $rootScope.remove(0);
                // add to available list when default == true
                expect($rootScope.assignment.criteria).toEqual([{id: "2abcABC123-abcABC123_Z", default: false}]);
                expect($rootScope.availableCriteria).toEqual([{id: "1abcABC123-abcABC123_Z", default: true}]);

                $rootScope.remove(0);
                // don't add to available list when default == false
                expect($rootScope.assignment.criteria).toEqual([]);
                expect($rootScope.availableCriteria).toEqual([{id: "1abcABC123-abcABC123_Z", default: true}]);
            });

            describe('when changeCriterion is called', function() {
                var criterion;
                var fakeModal = {
                    result: {
                        then: function(confirmCallback, cancelCallback) {
                            this.confirmCallBack = confirmCallback;
                            this.cancelCallback = cancelCallback;
                        }
                    },
                    close: function( item ) {
                        this.result.confirmCallBack( item );
                    },
                    dismiss: function( type ) {
                        this.result.cancelCallback( type );
                    },
                    opened: {
                        then: function() { }
                    }
                };
                beforeEach(function() {
                    criterion = {id: "1abcABC123-abcABC123_Z", name: 'test', weight: 10};
                    spyOn($uibModal, 'open').and.returnValue(fakeModal);
                    $rootScope.changeCriterion(criterion);
                });

                it('should open a modal dialog', function() {
                    expect($uibModal.open).toHaveBeenCalledWith({
                        animation: true,
                        backdrop: 'static',
                        controller: "CriterionModalController",
                        templateUrl: 'modules/criterion/criterion-modal-partial.html',
                        scope: jasmine.any(Object)
                    })
                });

                it('should update after the close event', function() {
                    var updated = {id: "1abcABC123-abcABC123_Z", name: 'test1'};
                    var expectedUpdate = angular.merge({}, updated, {id: criterion.id, weight: criterion.weight});
                    $rootScope.modalInstance.close(updated);
                    expect(criterion).toEqual(expectedUpdate);
                });
            });

            describe('when changeAnswer is called', function() {
                var fakeModal = {
                    result: {
                        then: function(confirmCallback, cancelCallback) {
                            this.confirmCallBack = confirmCallback;
                            this.cancelCallback = cancelCallback;
                        }
                    },
                    close: function( item ) {
                        this.result.confirmCallBack( item );
                    },
                    dismiss: function( type ) {
                        this.result.cancelCallback( type );
                    },
                    opened: {
                        then: function() { }
                    }
                };
                beforeEach(function() {
                    $rootScope.comparison_example.answer1 = {};
                    spyOn($uibModal, 'open').and.returnValue(fakeModal);
                    $rootScope.changeAnswer($rootScope.comparison_example.answer1, true);
                });

                it('should open a modal dialog', function() {
                    expect($uibModal.open).toHaveBeenCalledWith({
                        animation: true,
                        backdrop: 'static',
                        controller: "ComparisonExampleModalController",
                        templateUrl: 'modules/answer/answer-modal-partial.html',
                        scope: jasmine.any(Object)
                    })
                });

                it('should update after the close event', function() {
                    var updated = {content: 'test1'};
                    $rootScope.modalInstance.close(updated);
                    expect($rootScope.comparison_example.answer1).toEqual(updated);
                });
            });

            describe('save', function() {
                var toaster;
                var mockPracticeAnswer1 = {content: "content A"};
                var mockPracticeAnswer2 = {content: "content B"};
                var expectedCriterion = angular.copy(mockAssignment.criteria[0]);
                expectedCriterion.id = null;
                expectedCriterion.default = false;
                expectedCriterion.public = false;
                var mockNewCriterion = {
                    "compared": false,
                    "created": "Mon, 06 Jun 2016 19:50:47 -0000",
                    "default": false,
                    "public": false,
                    "description": "<p>Choose the response that you think is the better of the two.</p>",
                    "id": "1abcABC123-abcABC123_Z",
                    "modified": "Mon, 06 Jun 2016 19:50:47 -0000",
                    "name": "Which is better?",
                    "user_id": "9abcABC123-abcABC123_Z"
                }
                beforeEach(inject(function (_Toaster_) {
                    toaster = _Toaster_;
                    spyOn(toaster, 'warning');
                }));

                it('should warn when answer start is not before answer end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.date.aend.date = $rootScope.date.astart.date;
                    $rootScope.date.aend.time = $rootScope.date.astart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please set answer end time after answer start time and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when answer start is not before compare start', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cstart.date = angular.copy($rootScope.date.astart.date);
                    $rootScope.date.cstart.date.setDate($rootScope.date.cstart.date.getDate()-1);
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please double-check the answer and comparison start and end times for mismatches and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when compare start is not before compare end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cend.date = $rootScope.date.cstart.date;
                    $rootScope.date.cend.time = $rootScope.date.cstart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please set comparison end time after comparison start time and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should enable save button even if save failed', function() {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;

                    $httpBackend.expectPOST('/api/criteria', expectedCriterion).respond(200, mockNewCriterion);
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments', $rootScope.assignment)
                        .respond(400, '');
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                });

                it('should warn when comparison examples enabled and answer A is not set', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example = {
                        answer1: {},
                        answer2: mockPracticeAnswer2
                    };

                    var currentPath = $location.path();
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please add content for the first answer in your practice pair and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when comparison examples enabled and answer B is not set', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example = {
                        answer1: mockPracticeAnswer1,
                        answer2: {}
                    };

                    var currentPath = $location.path();
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please add content for the second answer in your practice pair and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should be able to save new assignment', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;

                    $httpBackend.expectPOST('/api/criteria', expectedCriterion).respond(200, mockNewCriterion);
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments', $rootScope.assignment)
                        .respond(angular.merge({}, mockAssignment, {id: "2abcABC123-abcABC123_Z"}));
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });

                it('should be able to save new assignment with comparison examples', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example = {
                        answer1: mockPracticeAnswer1,
                        answer2: mockPracticeAnswer2
                    };
                    $httpBackend.expectPOST('/api/criteria', expectedCriterion).respond(200, mockNewCriterion);
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments', $rootScope.assignment)
                        .respond(angular.merge({}, mockAssignment, {id: "2abcABC123-abcABC123_Z"}));
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/2abcABC123-abcABC123_Z/answers', $rootScope.comparison_example.answer1)
                        .respond(angular.merge({}, mockPracticeAnswer1, {id: "100cABC123-abcABC123_Z"}));
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/2abcABC123-abcABC123_Z/answers', $rootScope.comparison_example.answer2)
                        .respond(angular.merge({}, mockPracticeAnswer2, {id: "101cABC123-abcABC123_Z"}));
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/2abcABC123-abcABC123_Z/comparisons/examples', $rootScope.comparison_example)
                        .respond(angular.merge({}, mockComparisonExamples.objects[0], {id: "1abcABC123-abcABC123_Z"}));
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });
            });
        });

        describe('edit:', function() {
            beforeEach(function () {
                controller = createController({courseId: "1abcABC123-abcABC123_Z", assignmentId: "1abcABC123-abcABC123_Z"}, {
                    course: angular.copy(mockCourse),
                    assignment: angular.copy(mockAssignment),
                    assignmentComparisonExamples: angular.copy(mockComparisonExamples),
                    criteria: angular.copy(mockCritiera),
                    loggedInUser: angular.copy(mockUser),
                    canManageAssignment: true,
                });

                defaultCriteria = angular.merge({}, mockCritiera.objects[0], { weight:1 });
                otherCriteria = angular.copy(mockCritiera.objects);
                otherCriteria.shift();
                otherCriteria.forEach(function(criterion) {
                    criterion.weight = 1;
                });
            });

            it('should be correctly initialized', function () {
                expect($rootScope.assignment.id).toEqual(mockAssignment.id);
                expect($rootScope.assignment.criteria).toEqual(mockAssignment.criteria);
                expect($rootScope.assignment.addPractice).toEqual(true);

                expect($rootScope.recommended_comparisons).toEqual(3);
                expect($rootScope.availableCriteria).toEqual(otherCriteria);
                expect($rootScope.loggedInUserId).toEqual(id);
                expect($rootScope.comparison_example.id).toEqual(mockComparisonExamples.objects[0].id);
                expect($rootScope.comparison_example.answer1_id).toEqual(mockComparisonExamples.objects[0].answer1_id);
                expect($rootScope.comparison_example.answer2_id).toEqual(mockComparisonExamples.objects[0].answer2_id);

                expect($rootScope.canManageAssignment).toBe(true);
            });

            it('should add criteria to course from available criteria when add is called', function() {
                $rootScope.assignment.criteria = [];
                $rootScope.availableCriteria = [{id: "1abcABC123-abcABC123_Z"}, {id: "2abcABC123-abcABC123_Z"}];
                $rootScope.add(0);
                expect($rootScope.assignment.criteria).toEqual([{id: "1abcABC123-abcABC123_Z"}]);
                expect($rootScope.availableCriteria).toEqual([{id: "2abcABC123-abcABC123_Z"}]);
            });

            it('should remove criteria from course criteria when remove is called', function() {
                $rootScope.assignment.criteria = [{id: "1abcABC123-abcABC123_Z", default: true}, {id: "2abcABC123-abcABC123_Z", default: false}];
                $rootScope.availableCriteria = [];
                $rootScope.remove(0);
                // add to available list when default == true
                expect($rootScope.assignment.criteria).toEqual([{id: "2abcABC123-abcABC123_Z", default: false}]);
                expect($rootScope.availableCriteria).toEqual([{id: "1abcABC123-abcABC123_Z", default: true}]);

                $rootScope.remove(0);
                // don't add to available list when default == false
                expect($rootScope.assignment.criteria).toEqual([]);
                expect($rootScope.availableCriteria).toEqual([{id: "1abcABC123-abcABC123_Z", default: true}]);
            });

            describe('when changeCriterion is called', function() {
                var criterion;
                var fakeModal = {
                    result: {
                        then: function(confirmCallback, cancelCallback) {
                            this.confirmCallBack = confirmCallback;
                            this.cancelCallback = cancelCallback;
                        }
                    },
                    close: function( item ) {
                        this.result.confirmCallBack( item );
                    },
                    dismiss: function( type ) {
                        this.result.cancelCallback( type );
                    },
                    opened: {
                        then: function() { }
                    }
                };
                beforeEach(function() {
                    criterion = {id: "1abcABC123-abcABC123_Z", name: 'test', weight: 10};
                    spyOn($uibModal, 'open').and.returnValue(fakeModal);
                    $rootScope.changeCriterion(criterion);
                });

                it('should open a modal dialog', function() {
                    expect($uibModal.open).toHaveBeenCalledWith({
                        animation: true,
                        backdrop: 'static',
                        controller: "CriterionModalController",
                        templateUrl: 'modules/criterion/criterion-modal-partial.html',
                        scope: jasmine.any(Object)
                    })
                });

                it('should update after the close event', function() {
                    var updated = {id: "1abcABC123-abcABC123_Z", name: 'test1'};
                    var expectedUpdate = angular.merge({}, updated, {id: criterion.id, weight: criterion.weight});
                    $rootScope.modalInstance.close(updated);
                    expect(criterion).toEqual(expectedUpdate);
                });
            });

            describe('when changeAnswer is called', function() {
                var fakeModal = {
                    result: {
                        then: function(confirmCallback, cancelCallback) {
                            this.confirmCallBack = confirmCallback;
                            this.cancelCallback = cancelCallback;
                        }
                    },
                    close: function( item ) {
                        this.result.confirmCallBack( item );
                    },
                    dismiss: function( type ) {
                        this.result.cancelCallback( type );
                    },
                    opened: {
                        then: function() { }
                    }
                };
                beforeEach(function() {
                    spyOn($uibModal, 'open').and.returnValue(fakeModal);
                    $rootScope.changeAnswer($rootScope.comparison_example.answer1, true);
                });

                it('should open a modal dialog', function() {
                    expect($uibModal.open).toHaveBeenCalledWith({
                        animation: true,
                        backdrop: 'static',
                        controller: "ComparisonExampleModalController",
                        templateUrl: 'modules/answer/answer-modal-partial.html',
                        scope: jasmine.any(Object)
                    })
                });

                it('should update after the close event', function() {
                    var updated = angular.merge({}, $rootScope.comparison_example.answer1, {content: 'test123'}) ;
                    $rootScope.modalInstance.close(updated);
                    expect($rootScope.comparison_example.answer1).toEqual(updated);
                });
            });

            describe('save', function() {
                var toaster;
                beforeEach(inject(function (_Toaster_) {
                    toaster = _Toaster_;
                    spyOn(toaster, 'warning');
                }));

                it('should warn when answer start is not before answer end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.date.aend.date = $rootScope.date.astart.date;
                    $rootScope.date.aend.time = $rootScope.date.astart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please set answer end time after answer start time and save again.');
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
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please double-check the answer and comparison start and end times for mismatches and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when compare start is not before compare end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cend.date = $rootScope.date.cstart.date;
                    $rootScope.date.cend.time = $rootScope.date.cstart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please set comparison end time after comparison start time and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when comparison examples enabled and answer A is not set', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example.answer1.content = "";
                    var currentPath = $location.path();
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please add content for the first answer in your practice pair and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when comparison examples enabled and answer B is not set', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example.answer2.content = "";
                    var currentPath = $location.path();
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please add content for the second answer in your practice pair and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should enable save button even if save failed', function() {
                    $rootScope.assignment = angular.copy(mockAssignment);

                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z', $rootScope.assignment)
                        .respond(400, '');
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                });

                it('should be able to save new assignment', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.addPractice = true;

                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z', $rootScope.assignment)
                        .respond(angular.copy($rootScope.assignment));
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z/comparisons/examples/1abcABC123-abcABC123_Z', $rootScope.comparison_example)
                        .respond(mockComparisonExamples.objects[0]);

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });

                it('should be able to save new assignment and delete old comparison example', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.addPractice = false;

                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/1abcABC123-abcABC123_Z', $rootScope.assignment)
                        .respond(angular.merge({}, mockAssignment, {id: "2abcABC123-abcABC123_Z"}));
                    $httpBackend.expectDELETE('/api/courses/1abcABC123-abcABC123_Z/assignments/2abcABC123-abcABC123_Z/comparisons/examples/1abcABC123-abcABC123_Z')
                        .respond({});

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });
            });
        });

        describe('copy:', function() {
            beforeEach(function () {
                $route.current.method = "copy";
                controller = createController({courseId: "1abcABC123-abcABC123_Z", assignmentId: "1abcABC123-abcABC123_Z"}, {
                    course: angular.copy(mockCourse),
                    assignment: angular.copy(mockAssignment),
                    assignmentComparisonExamples: angular.copy(mockComparisonExamples),
                    criteria: angular.copy(mockCritiera),
                    loggedInUser: angular.copy(mockUser),
                    canManageAssignment: true,
                });

                defaultCriteria = angular.merge({}, mockCritiera.objects[0], { weight:1 });
                otherCriteria = angular.copy(mockCritiera.objects);
                otherCriteria.shift();
                otherCriteria.forEach(function(criterion) {
                    criterion.weight = 1;
                });
            });

            it('should be correctly initialized', function () {
                expect($rootScope.assignment.id).toEqual(undefined);
                expect($rootScope.assignment.criteria).toEqual(mockAssignment.criteria);
                expect($rootScope.assignment.addPractice).toEqual(true);
                expect($rootScope.compared).toEqual(undefined);

                expect($rootScope.recommended_comparisons).toEqual(3);
                expect($rootScope.availableCriteria).toEqual(otherCriteria);
                expect($rootScope.loggedInUserId).toEqual(id);

                expect($rootScope.comparison_example.id).toEqual(undefined);
                expect($rootScope.comparison_example.answer1_id).toEqual(undefined);
                expect($rootScope.comparison_example.answer1.content).toEqual(mockComparisonExamples.objects[0].answer1.content);
                expect($rootScope.comparison_example.answer1.file).toEqual(mockComparisonExamples.objects[0].answer1.file);
                expect($rootScope.comparison_example.answer2_id).toEqual(undefined);
                expect($rootScope.comparison_example.answer2.content).toEqual(mockComparisonExamples.objects[0].answer2.content);
                expect($rootScope.comparison_example.answer2.file).toEqual(mockComparisonExamples.objects[0].answer2.file);

                expect($rootScope.canManageAssignment).toBe(true);
            });

            it('should add criteria to course from available criteria when add is called', function() {
                $rootScope.assignment.criteria = [];
                $rootScope.availableCriteria = [{id: "1abcABC123-abcABC123_Z"}, {id: "2abcABC123-abcABC123_Z"}];
                $rootScope.add(0);
                expect($rootScope.assignment.criteria).toEqual([{id: "1abcABC123-abcABC123_Z"}]);
                expect($rootScope.availableCriteria).toEqual([{id: "2abcABC123-abcABC123_Z"}]);
            });

            it('should remove criteria from course criteria when remove is called', function() {
                $rootScope.assignment.criteria = [{id: "1abcABC123-abcABC123_Z", default: true}, {id: "2abcABC123-abcABC123_Z", default: false}];
                $rootScope.availableCriteria = [];
                $rootScope.remove(0);
                // add to available list when default == true
                expect($rootScope.assignment.criteria).toEqual([{id: "2abcABC123-abcABC123_Z", default: false}]);
                expect($rootScope.availableCriteria).toEqual([{id: "1abcABC123-abcABC123_Z", default: true}]);

                $rootScope.remove(0);
                // don't add to available list when default == false
                expect($rootScope.assignment.criteria).toEqual([]);
                expect($rootScope.availableCriteria).toEqual([{id: "1abcABC123-abcABC123_Z", default: true}]);
            });

            describe('when changeCriterion is called', function() {
                var criterion;
                var fakeModal = {
                    result: {
                        then: function(confirmCallback, cancelCallback) {
                            this.confirmCallBack = confirmCallback;
                            this.cancelCallback = cancelCallback;
                        }
                    },
                    close: function( item ) {
                        this.result.confirmCallBack( item );
                    },
                    dismiss: function( type ) {
                        this.result.cancelCallback( type );
                    },
                    opened: {
                        then: function() { }
                    }
                };
                beforeEach(function() {
                    criterion = {id: "1abcABC123-abcABC123_Z", name: 'test', weight: 10};
                    spyOn($uibModal, 'open').and.returnValue(fakeModal);
                    $rootScope.changeCriterion(criterion);
                });

                it('should open a modal dialog', function() {
                    expect($uibModal.open).toHaveBeenCalledWith({
                        animation: true,
                        backdrop: 'static',
                        controller: "CriterionModalController",
                        templateUrl: 'modules/criterion/criterion-modal-partial.html',
                        scope: jasmine.any(Object)
                    })
                });

                it('should update after the close event', function() {
                    var updated = {id: "1abcABC123-abcABC123_Z", name: 'test1'};
                    var expectedUpdate = angular.merge({}, updated, {id: criterion.id, weight: criterion.weight});
                    $rootScope.modalInstance.close(updated);
                    expect(criterion).toEqual(expectedUpdate);
                });
            });

            describe('when changeAnswer is called', function() {
                var fakeModal = {
                    result: {
                        then: function(confirmCallback, cancelCallback) {
                            this.confirmCallBack = confirmCallback;
                            this.cancelCallback = cancelCallback;
                        }
                    },
                    close: function( item ) {
                        this.result.confirmCallBack( item );
                    },
                    dismiss: function( type ) {
                        this.result.cancelCallback( type );
                    },
                    opened: {
                        then: function() { }
                    }
                };
                beforeEach(function() {
                    spyOn($uibModal, 'open').and.returnValue(fakeModal);
                    $rootScope.changeAnswer($rootScope.comparison_example.answer1, true);
                });

                it('should open a modal dialog', function() {
                    expect($uibModal.open).toHaveBeenCalledWith({
                        animation: true,
                        backdrop: 'static',
                        controller: "ComparisonExampleModalController",
                        templateUrl: 'modules/answer/answer-modal-partial.html',
                        scope: jasmine.any(Object)
                    })
                });

                it('should update after the close event', function() {
                    var updated = angular.merge({}, $rootScope.comparison_example.answer1, {content: 'test123'}) ;
                    $rootScope.modalInstance.close(updated);
                    expect($rootScope.comparison_example.answer1).toEqual(updated);
                });
            });

            describe('save', function() {
                var toaster;
                var mockPracticeAnswer1 = {content: "content A"};
                var mockPracticeAnswer2 = {content: "content B"};
                var expectedCriterion = angular.copy(mockAssignment.criteria[0]);
                expectedCriterion.id = null;
                expectedCriterion.default = false;
                expectedCriterion.public = false;
                var mockNewCriterion = {
                    "compared": false,
                    "created": "Mon, 06 Jun 2016 19:50:47 -0000",
                    "default": false,
                    "public": false,
                    "description": "<p>Choose the response that you think is the better of the two.</p>",
                    "id": "1abcABC123-abcABC123_Z",
                    "modified": "Mon, 06 Jun 2016 19:50:47 -0000",
                    "name": "Which is better?",
                    "user_id": "9abcABC123-abcABC123_Z"
                }
                beforeEach(inject(function (_Toaster_) {
                    toaster = _Toaster_;
                    spyOn(toaster, 'warning');
                }));

                it('should warn when answer start is not before answer end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.date.aend.date = $rootScope.date.astart.date;
                    $rootScope.date.aend.time = $rootScope.date.astart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please set answer end time after answer start time and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when answer start is not before compare start', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cstart.date = angular.copy($rootScope.date.astart.date);
                    $rootScope.date.cstart.date.setDate($rootScope.date.cstart.date.getDate()-1);
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please double-check the answer and comparison start and end times for mismatches and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when compare start is not before compare end', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.availableCheck = true;
                    $rootScope.date.cend.date = $rootScope.date.cstart.date;
                    $rootScope.date.cend.time = $rootScope.date.cstart.time;
                    var currentPath = $location.path();

                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please set comparison end time after comparison start time and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should enable save button even if save failed', function() {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;

                    $httpBackend.expectPOST('/api/criteria', expectedCriterion).respond(200, mockNewCriterion);
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments', $rootScope.assignment)
                        .respond(400, '');
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                });

                it('should warn when comparison examples enabled and answer A is not set', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example = {
                        answer1: {},
                        answer2: mockPracticeAnswer2
                    };

                    var currentPath = $location.path();
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please add content for the first answer in your practice pair and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should warn when comparison examples enabled and answer B is not set', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example = {
                        answer1: mockPracticeAnswer1,
                        answer2: {}
                    };

                    var currentPath = $location.path();
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Assignment Not Saved', 'Please add content for the second answer in your practice pair and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should be able to save new assignment', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;

                    $httpBackend.expectPOST('/api/criteria', expectedCriterion).respond(200, mockNewCriterion);
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments', $rootScope.assignment)
                        .respond(angular.merge({}, mockAssignment, {id: "2abcABC123-abcABC123_Z"}));
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });

                it('should be able to save new assignment with comparison examples', function () {
                    $rootScope.assignment = angular.copy(mockAssignment);
                    $rootScope.assignment.id = undefined;
                    $rootScope.assignment.addPractice = true;
                    $rootScope.comparison_example = {
                        answer1: mockPracticeAnswer1,
                        answer2: mockPracticeAnswer2
                    };
                    $httpBackend.expectPOST('/api/criteria', expectedCriterion).respond(200, mockNewCriterion);
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments', $rootScope.assignment)
                        .respond(angular.merge({}, mockAssignment, {id: "2abcABC123-abcABC123_Z"}));
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/2abcABC123-abcABC123_Z/answers', $rootScope.comparison_example.answer1)
                        .respond(angular.merge({}, mockPracticeAnswer1, {id: "100cABC123-abcABC123_Z"}));
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/2abcABC123-abcABC123_Z/answers', $rootScope.comparison_example.answer2)
                        .respond(angular.merge({}, mockPracticeAnswer2, {id: "101cABC123-abcABC123_Z"}));
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/assignments/2abcABC123-abcABC123_Z/comparisons/examples', $rootScope.comparison_example)
                        .respond(angular.merge({}, mockComparisonExamples.objects[0], {id: "1abcABC123-abcABC123_Z"}));
                    $rootScope.assignmentSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/1abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });
            });
        });
    });
});