describe('comparison-module', function () {
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
        fullname_sortable: "Smith, John",
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
    beforeEach(module('ubc.ctlt.compair.comparison'));
    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
        sessionRequestHandler = $httpBackend.when('GET', '/api/session').respond(mockSession);
        $httpBackend.when('GET', '/api/users/' + id).respond(mockUser);
        $httpBackend.whenPOST(/\/api\/learning_records\/xapi\/statements$/).respond(function(method, url, data, headers) {
            return [200, { 'success':true }, {}];
        });
        $httpBackend.whenPOST(/\/api\/learning_records\/caliper\/events$/).respond(function(method, url, data, headers) {
            return [200, { 'success':true }, {}];
        });
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('ComparisonController', function () {
        var $rootScope, createController, $location, $uibModal, $q, LearningRecord, LearningRecordSettings, $route;
        var mockCritiera = {
            "criteria": [{
                "created": "Sat, 06 Sep 2014 02:13:07 -0000",
                "default": true,
                "public": true,
                "description": "<p>Choose the response that you think is the better of the two.</p>",
                "id": "1abcABC123-abcABC123_Z",
                "compared": true,
                "modified": "Sat, 06 Sep 2014 02:13:07 -0000",
                "name": "Which is better?",
                "user_id": "1abcABC123-abcABC123_Z"
            }, {
                "created": "Fri, 09 Jan 2015 18:35:58 -0000",
                "default": false,
                "public": false,
                "description": "<p>Explaining what a better idea was</p>\n",
                "id": "2abcABC123-abcABC123_Z",
                "compared": false,
                "modified": "Fri, 09 Jan 2015 18:35:58 -0000",
                "name": "Which answer has the better idea?",
                "user_id": "46bcABC123-abcABC123_Z",
            }]
        };
        var mockAssignment = {
            'course_id': "1abcABC123-abcABC123_Z",
            "after_comparing": false,
            "answer_end": "Mon, 14 Sep 2015 04:00:00 -0000",
            "answer_period": false,
            "answer_start": "Mon, 23 Feb 2015 21:50:00 -0000",
            "answer_count": 115,
            "available": true,
            "students_can_reply": false,
            "criteria": [
                {
                    "compared": true,
                    "created": "Fri, 09 Jan 2015 22:47:02 -0000",
                    "default": true,
                    "public": false,
                    "description": "criterion 1",
                    "id": "4abcABC123-abcABC123_Z",
                    "modified": "Fri, 09 Jan 2015 22:47:02 -0000",
                    "name": "Which answer has the better critical idea?",
                    "user_id": "50bcABC123-abcABC123_Z",
                    "weight": 1
                },
                {
                    "compared": true,
                    "created": "Fri, 09 Jan 2015 22:50:06 -0000",
                    "default": true,
                    "public": false,
                    "description": "criterion 2",
                    "id": "5abcABC123-abcABC123_Z",
                    "modified": "Fri, 09 Jan 2015 22:50:06 -0000",
                    "name": "Which answer is more effectively articulated? Explain the reason for your preference.",
                    "user_id": "50bcABC123-abcABC123_Z",
                    "weight": 1
                }
            ],
            "evaluation_count": 252,
            "id": "9abcABC123-abcABC123_Z",
            "compare_end": "Thu, 15 Sep 2016 16:00:00 -0000",
            "compare_start": "Tue, 15 Sep 2015 04:00:00 -0000",
            "compared": true,
            "compare_period": true,
            "modified": "Fri, 25 Sep 2015 07:40:19 -0000",
            "peer_feedback_prompt": null,
            "number_of_comparisons": 3,
            "total_comparisons_required": 3,
            "total_steps_required": 4,
            "content": "<p><strong>For your answer, write ONLY the premise of 20-60 words. Do not include your notes. Consider spending 10-15 minutes making the notes, but not much longer for this exercise. I strongly recommend marking up a hard copy, as we do in class: paste the poem into a word document and print yourself a working copy.</strong></p>\n\n<p>Transplanted<br />\n&nbsp;&nbsp;&nbsp; ---by Lorna Crozier<br />\n<br />\nThis heart met the air. Grew in the hours<br />\nbetween the first body and the next<br />\na taste for things outside it: the heat<br />\nof high intensity, wind grieving<br />\nin the poplar leaves, the smell of steam<br />\nwafting through the open window<br />\nfrom the hot dog vendor&#39;s cart. Often it skips<br />\n<br />\na beat - grouse explode from ditches,<br />\na man flies through the windshield,<br />\na face the heart once knew<br />\nweeps in the corridor that gives nothing back<br />\nbut unloveliness and glare.<br />\n<br />\nLike a shovel that hits the earth, then rises,<br />\nand hits the earth again, it feels its own<br />\ndull blows. Some nights it is a sail billowing<br />\nwith blood, a raw fist punching.<br />\nSome nights, beneath the weight of blankets,<br />\nflesh and bones, the heart remembers. Feels those<br />\nsurgical gloves close around it, and goes cold.</p>\n",
            "file": null,
            "user": {
                "avatar": "b893bcb68fbeef6738437fa1deca0a28",
                "displayname": "Tiffany Potter",
                "id": "50bcABC123-abcABC123_Z"
            },
            "enable_self_evaluation": true,
            "enable_group_answers": false,
            "self_eval_start": null,
            "self_eval_end": null,
            "self_eval_instructions": null,
            "pairing_algorithm": "random",
            "educators_can_compare": false,
            "rank_display_limit": 10,
            "name": "Read the poem below, and make notes on syntax, figurative language, patterns of diction and imagery, and form. Then, imagining that you are writing a 1200-word essay, write a critical premise of 20-60 words as we have discussed in class."
        };

        var mockAnswer1 = {
            "comment_count": 3,
            "content": "This is answer 1",
            "created": "Sat, 29 Aug 2015 08:00:19 -0000",
            "file": null,
            "top_answer": false,
            "id": "407cABC123-abcABC123_Z",
            "private_comment_count": 3,
            "public_comment_count": 0,
            "assignment_id": "9abcABC123-abcABC123_Z",
            "course_id": "1abcABC123-abcABC123_Z",
            "score": {
                "rank": 2,
                "normalized_score": 75,
            },
            "user": {
                "id": "1abcABC123-abcABC123_Z",
                "avatar": "63a9f0ea7bb98050796b649e85481845",
                "displayname": "root"
            },
            "user_id": "1abcABC123-abcABC123_Z",
            "group": null,
            "group_id": null
        };

        var mockAnswer2 = {
            "comment_count": 4,
            "content": "This is answer 2",
            "created": "Tue, 24 Feb 2015 04:09:28 -0000",
            "file": null,
            "top_answer": false,
            "id": "279cABC123-abcABC123_Z",
            "private_comment_count": 4,
            "public_comment_count": 0,
            "assignment_id": "9abcABC123-abcABC123_Z",
            "course_id": "1abcABC123-abcABC123_Z",
            "score": {
                "rank": 2,
                "normalized_score": 75,
            },
            "user": {
                "id": "162cABC123-abcABC123_Z",
                "avatar": "25242646dab1876796ab95f036a8fc82",
                "displayname": "student_95322345"
            },
            "user_id": "162cABC123-abcABC123_Z",
            "group": null,
            "group_id": null
        };

        var mockAnswer2Comments = [{
            "answer_id": "279cABC123-abcABC123_Z",
            "content": "<p>test123213t4453123123</p>\n",
            "course_id": "3abcABC123-abcABC123_Z",
            'assignment_id': "9abcABC123-abcABC123_Z",
            "created": "Thu, 24 Sep 2015 00:22:34 -0000",
            "id": "3703ABC123-abcABC123_Z",
            "comment_type": 'Evaluation',
            "draft": false,
            "user": {
                "id": "1abcABC123-abcABC123_Z",
                "avatar": "63a9f0ea7bb98050796b649e85481845",
                "displayname": "root"
            },
            "user_id": "1abcABC123-abcABC123_Z"
        }];

        var mockComparison = {
            'id': "1abcABC123-abcABC123_Z",
            'course_id': "1abcABC123-abcABC123_Z",
            'assignment_id': "9abcABC123-abcABC123_Z",
            'user_id': id,
            'answer1_id': "407cABC123-abcABC123_Z",
            'answer2_id': "279cABC123-abcABC123_Z",
            'answer1': angular.copy(mockAnswer1),
            'answer1_feedback': [],
            'answer2': angular.copy(mockAnswer2),
            'answer2_feedback': angular.copy(mockAnswer2Comments),
            'winner': null,

            'comparison_criteria': [
                {
                    'id': "1abcABC123-abcABC123_Z",
                    'winner': null,
                    'content': '',

                    'criterion_id': "4abcABC123-abcABC123_Z",
                    'criterion': {
                        "created": "Fri, 09 Jan 2015 22:47:02 -0000",
                        "default": true,
                        "public": false,
                        "description": "criterion 1",
                        "id": "4abcABC123-abcABC123_Z",
                        "compared": true,
                        "modified": "Fri, 09 Jan 2015 22:47:02 -0000",
                        "name": "Which answer has the better critical idea?",
                        "user_id": "50bcABC123-abcABC123_Z",
                    }
                }, {
                    'id': "2abcABC123-abcABC123_Z",
                    'winner': null,
                    'content': '',

                    'criterion_id': "5abcABC123-abcABC123_Z",
                    'criterion': {
                        "created": "Fri, 09 Jan 2015 22:50:06 -0000",
                        "default": true,
                        "public": false,
                        "description": "criterion 2",
                        "id": "5abcABC123-abcABC123_Z",
                        "compared": true,
                        "modified": "Fri, 09 Jan 2015 22:50:06 -0000",
                        "name": "Which answer is more effectively articulated? Explain the reason for your preference.",
                        "user_id": "50bcABC123-abcABC123_Z",
                    }
                }
            ],

            'user': {
                'avatar': "63a9f0ea7bb98050796b649e85481845",
                'displayname': "root",
                'fullname': "John Smith",
                'fullname_sortable': "Smith, John",
                "student_number": null,
                'id': id
            },
            'created': "Fri, 09 Jan 2015 18:35:58 -0000",
        };

        var mockNewComment = {
            "answer_id": "407cABC123-abcABC123_Z",
            "evaluation_number": 1,
            "comment_type": "Evaluation",
            "draft": true
        };

        var mockAnswer2Comment = angular.merge(angular.copy(mockAnswer2Comments[0]), {
            "evaluation_number": 2
        });

        var mockTimer = {
            "date": 1467325647825
        };

        var mockUUID = "caece01c-ea5c-472d-9f9c-be864a3442d5";
        var mockDuration = "PT0.007S";
        var mockStarted = "2016-11-26T00:35:23.389Z";
        var mockEnded = "2016-11-26T00:35:33.389Z";
        var mockTracking = {
            getUUID: function() {
                return mockUUID;
            },
            getDuration: function() {
                return mockDuration;
            },
            getStarted: function() {
                return mockStarted;
            },
            getEnded: function() {
                return mockEnded;
            },
            toParams: function() {
                return {
                    attempt_uuid: mockUUID,
                    attempt_started: mockDuration,
                    attempt_ended: new Date(mockStarted),
                    attempt_duration: new Date(mockEnded)
                };
            }
        };

        beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$uibModal_, _$q_, _LearningRecord_, _LearningRecordSettings_, _$route_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            $uibModal = _$uibModal_;
            $q = _$q_;
            LearningRecord = _LearningRecord_;
            $route = _$route_;
            spyOn($route, 'reload');
            createController = function (params, resolvedData) {
                return $controller('ComparisonController', {
                    $scope: $rootScope,
                    $route: $route,
                    $routeParams: params || {},
                    resolvedData: resolvedData || {}
                });
            };
            LearningRecord.generateAttemptTracking = function() {
                return mockTracking;
            };
            LearningRecordSettings = _LearningRecordSettings_;
            LearningRecordSettings.xapi_enabled = true;
            LearningRecordSettings.caliper_enabled = true;
            LearningRecordSettings.baseUrl = "https://localhost:8888/";
        }));

        it('should have correct initial states', function () {
            $httpBackend.expectGET('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/comparisons').respond({
                'comparison':mockComparison,
                'current': 1
            });

            createController({courseId: "3abcABC123-abcABC123_Z", assignmentId: "9abcABC123-abcABC123_Z"}, {
                course: angular.copy(mockCourse),
                assignment: angular.copy(mockAssignment),
                loggedInUser: angular.copy(mockUser),
                timer: angular.copy(mockTimer),
                canManageAssignment: true,
            });
            expect($rootScope.course).toEqualData(mockCourse);
            expect($rootScope.assignment).toEqualData(mockAssignment);
            expect($rootScope.current).toBe(undefined);
            $httpBackend.flush();

            expect($rootScope.comparison).toEqualData(mockComparison);
            expect($rootScope.current).toEqual(1);
            expect($rootScope.tracking).toEqualData(mockTracking);

            answer1 = angular.merge(angular.copy(mockComparison.answer1), {
                "evaluation_number": 1
            });
            answer2 = angular.merge(angular.copy(mockComparison.answer2), {
                "evaluation_number": 2
            });
            expect($rootScope.answer1).toEqualData(answer1);
            expect($rootScope.answer2).toEqualData(answer2);
            expect($rootScope.answer1_feedback).toEqualData(mockNewComment);
            expect($rootScope.answer2_feedback).toEqualData(mockAnswer2Comment);
        });

        describe('actions:', function() {
            var controller;
            var mockComparisonResponse = {
                "comparison": angular.copy(mockComparison)
            };
            mockComparisonResponse.comparison.comparison_criteria[0].winner = "answer1";
            mockComparisonResponse.comparison.comparison_criteria[0].content = 'criterion comment 1';
            mockComparisonResponse.comparison.comparison_criteria[1].winner = "answer2";
            mockComparisonResponse.comparison.comparison_criteria[1].content = 'criterion comment 2';

            beforeEach(function() {
                $httpBackend.expectGET('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/comparisons').respond({
                    'comparison':mockComparison,
                    'current': 1
                });
                controller = createController({courseId: "3abcABC123-abcABC123_Z", assignmentId: "9abcABC123-abcABC123_Z"}, {
                    course: angular.copy(mockCourse),
                    assignment: angular.copy(mockAssignment),
                    loggedInUser: angular.copy(mockUser),
                    timer: angular.copy(mockTimer),
                    canManageAssignment: true,
                });
                $httpBackend.flush();
            });

            it('should load the comment saved before when the same answer is shown', function() {
                expect($rootScope.answer2_feedback).toEqualData(mockAnswer2Comment);
            });

            it('should submit comparisons when comparisonSubmit is called', function() {
                var expectedComparison = angular.merge({
                    "draft": false,
                    "comparison_criteria":[
                        {
                            criterion_id: "4abcABC123-abcABC123_Z",
                            content: 'criterion comment 1',
                            winner: 'answer1'
                        }, {
                            criterion_id: "5abcABC123-abcABC123_Z",
                            content: 'criterion comment 2',
                            winner: 'answer2'
                        }
                    ]
                }, mockTracking.toParams());
                var mockTrackingComment = mockTracking.toParams();
                // save answer feedback/comments
                var expectedAnswerComment1 = angular.extend({}, mockNewComment, {"content":"Feedback 1", "comment_type":'Evaluation', "draft": false}, mockTrackingComment);
                var expectedAnswerComment2 = angular.extend({}, mockAnswer2Comment, {"content":"Feedback 2", "comment_type":'Evaluation', "draft": false}, mockTrackingComment);
                $rootScope.answer1_feedback.content = 'Feedback 1';
                $rootScope.answer2_feedback.content = 'Feedback 2';
                // save comparison selection and comments
                $rootScope.comparison.comparison_criteria[0].winner = 'answer1';
                $rootScope.comparison.comparison_criteria[0].content = 'criterion comment 1';
                $rootScope.comparison.comparison_criteria[1].winner = 'answer2';
                $rootScope.comparison.comparison_criteria[1].content = 'criterion comment 2';
                $httpBackend.expectPOST('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/answers/407cABC123-abcABC123_Z/comments', expectedAnswerComment1).respond({});
                $httpBackend.expectPOST('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/answers/279cABC123-abcABC123_Z/comments/3703ABC123-abcABC123_Z', expectedAnswerComment2).respond({});
                $httpBackend.expectPOST('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/comparisons', expectedComparison).respond(mockComparisonResponse);
                expect($rootScope.preventExit).toBe(true);

                $rootScope.comparisonSubmit();
                $httpBackend.flush();

                expect($route.reload).toHaveBeenCalled();
                expect($rootScope.preventExit).toBe(false);
            })

        });

        describe('draft actions:', function() {
            var controller;
            var mockComparisonResponse = {
                "comparison": angular.copy(mockComparison)
            };
            mockComparisonResponse.comparison.comparison_criteria[0].winner = "answer1";
            mockComparisonResponse.comparison.comparison_criteria[0].content = 'criterion comment 1';
            mockComparisonResponse.comparison.comparison_criteria[1].winner = "answer2";
            mockComparisonResponse.comparison.comparison_criteria[1].content = 'criterion comment 2';

            beforeEach(function() {
                $httpBackend.expectGET('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/comparisons').respond({
                    'comparison':mockComparison,
                    'current': 1
                });
                controller = createController({courseId: "3abcABC123-abcABC123_Z", assignmentId: "9abcABC123-abcABC123_Z"}, {
                    course: angular.copy(mockCourse),
                    assignment: angular.copy(mockAssignment),
                    loggedInUser: angular.copy(mockUser),
                    timer: angular.copy(mockTimer),
                    canManageAssignment: true,
                });
                $rootScope.isDraft = true;
                $httpBackend.flush();
            });

            it('should submit comparison when comparisonSubmit is called', function() {
                var expectedComparison = angular.merge({
                    "draft": true,
                    "comparison_criteria":[
                        {
                            criterion_id: "4abcABC123-abcABC123_Z",
                            content: 'criterion comment 1',
                            winner: 'answer1'
                        }, {
                            criterion_id: "5abcABC123-abcABC123_Z",
                            content: 'criterion comment 2',
                            winner: 'answer2'
                        }
                    ],
                }, mockTracking.toParams());
                var mockTrackingComment = mockTracking.toParams();
                // save answer feedback/comments
                var expectedAnswerComment1 = angular.extend({}, mockNewComment, {"content":"Feedback 1", "comment_type":'Evaluation', "draft": true}, mockTrackingComment);
                var expectedAnswerComment2 = angular.extend({}, mockAnswer2Comment, {"content":"Feedback 2", "comment_type":'Evaluation', "draft": true}, mockTrackingComment);
                $rootScope.answer1_feedback.content = 'Feedback 1';
                $rootScope.answer2_feedback.content = 'Feedback 2';
                // save comparison selection and comments
                $rootScope.comparison.comparison_criteria[0].winner = 'answer1';
                $rootScope.comparison.comparison_criteria[0].content = 'criterion comment 1';
                $rootScope.comparison.comparison_criteria[1].winner = 'answer2';
                $rootScope.comparison.comparison_criteria[1].content = 'criterion comment 2';
                $httpBackend.expectPOST('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/answers/407cABC123-abcABC123_Z/comments', expectedAnswerComment1).respond({});
                $httpBackend.expectPOST('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/answers/279cABC123-abcABC123_Z/comments/3703ABC123-abcABC123_Z', expectedAnswerComment2).respond({});
                $httpBackend.expectPOST('/api/courses/3abcABC123-abcABC123_Z/assignments/9abcABC123-abcABC123_Z/comparisons', expectedComparison).respond(mockComparisonResponse);

                expect($rootScope.preventExit).toBe(true);
                $rootScope.comparisonSubmit();
                expect($rootScope.submitted).toBe(true);
                $httpBackend.flush();

                expect($route.reload).not.toHaveBeenCalled();
                expect($rootScope.preventExit).toBe(true);
                expect($rootScope.submitted).toBe(false);
            })

        });
    });
});