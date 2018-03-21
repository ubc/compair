describe('xapi-module', function () {
    var $httpBackend;
    var id = "1abcABC123-abcABC123_Z";
    beforeEach(module('ubc.ctlt.compair.common.xapi'));
    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('xAPIStatementHelper', function () {
        var $rootScope, $location, Session, xAPIStatementHelper, xAPI, xAPISettings;
        var absUrlSpy, pathSpy;
        var mockCourse = {
            "available": true,
            "start_date": null,
            "end_date": null,
            "created": "Fri, 09 Jan 2015 17:23:59 -0000",
            "id": "1abcABC123-abcABC123_Z",
            "modified": "Fri, 09 Jan 2015 17:23:59 -0000",
            "name": "Test Course",
            "year": 2015,
            "term": "Winter",
            "sandbox": false,
            "start_time": null,
            "end_time": null
        };
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
            "top_answer_count": 0,
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
            "flagged": false,
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
            "user_id": "1abcABC123-abcABC123_Z"
        };

        var mockAnswer2 = {
            "comment_count": 4,
            "content": "This is answer 2",
            "created": "Tue, 24 Feb 2015 04:09:28 -0000",
            "file": null,
            "flagged": false,
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
            "user_id": "162cABC123-abcABC123_Z"
        };

        var mockComparison = {
            'id': "1abcABC123-abcABC123_Z",
            'course_id': "1abcABC123-abcABC123_Z",
            'assignment_id': "9abcABC123-abcABC123_Z",
            'user_id': id,
            'answer1_id': "407cABC123-abcABC123_Z",
            'answer2_id': "279cABC123-abcABC123_Z",
            'answer1': angular.copy(mockAnswer1),
            'answer2': angular.copy(mockAnswer2),
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
                    'winner': 'answer2',
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
                'id': id
            },
            'created': "Fri, 09 Jan 2015 18:35:58 -0000",
        };

        var mockComment = {
            "answer_id": "279cABC123-abcABC123_Z",
            "content": "<p>test123213t4453123123</p>\n",
            "course_id": "1abcABC123-abcABC123_Z",
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
        };

        var mockFile = {
            "alias": "2_4_122.pdf",
            "id": "1abcABC123-abcABC123_Z",
            "name": "1abcABC123-abcABC123_Z.pdf",
            "extension": "pdf",
            "mimetype": "application/pdf"
        };

        var mockFilters = {
            "orderBy": "Lu0GSS8vQuKz3H6mDIy4Pw",
            "perPage": 20,
            "group": "Group 2",
            "author": "1UwbRtIPQ_2HjAbL5MJYjQ",
            "top": null,
            "page": 1
        };
        var mockSortOrder = "email asc";
        var sectionName = "Page Section !@#$%^&*()1";
        var modalName = "Modal !@#$%^&*()1";

        var mockStatementId = "a8262557-036f-4d8a-8743-0e3a5eb16b62";
        var mockTimestamp = "2016-11-26T00:35:43.389Z";
        var mockRegistration = "caece01c-ea5c-472d-9f9c-be864a3442d5";
        var mockDuration = "PT0.007S";
        var mockLocationAbsUrl = "https://localhost:1888/app/#/mock/location/";
        var mockLocationPath = "/mock/location/";

        beforeEach(inject(function (_$rootScope_, _$location_, Session, _xAPIStatementHelper_, _xAPI_, _xAPISettings_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            xAPIStatementHelper = _xAPIStatementHelper_;
            xAPI = _xAPI_;
            xAPISettings = _xAPISettings_;
            xAPISettings.enabled = true;
            xAPISettings.baseUrl = "https://localhost:8888/";

            spyOn(TinCan.Utils, 'getUUID').and.returnValue(mockStatementId);
            spyOn(window, 'Date').and.returnValue({ toISOString: function() { return mockTimestamp; } });
            spyOn(Session, 'isLoggedIn').and.returnValue(true);

            absUrlSpy = spyOn($location, 'absUrl').and.returnValue(mockLocationAbsUrl);
            pathSpy = spyOn($location, 'path').and.returnValue(mockLocationPath);
        }));

        describe('interacted_answer_solution:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAnswer1);
                invalid.id = null;
                xAPIStatementHelper.interacted_answer_solution(invalid, mockRegistration, mockDuration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/interacted",
                        "display":{"en-US":"interacted"}
                    },
                    "result":{
                        "duration": mockDuration,
                        "response":"This is answer 1",
                        "extensions":{
                            "http://xapi.learninganalytics.ubc.ca/extension/character-count":16,
                            "http://xapi.learninganalytics.ubc.ca/extension/word-count":4
                        }
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/question",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/solution",
                            "name":{"en-US":"Assignment answer"}
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.interacted_answer_solution(mockAnswer1, mockRegistration, mockDuration);
                $httpBackend.flush();
            });
        });

        describe('attached_answer_attachment:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAnswer1);
                invalid.id = null;
                xAPIStatementHelper.attached_answer_attachment(mockFile, invalid, mockRegistration);
            });

            it('should do nothing when no file id provided', function() {
                var invalid = angular.copy(mockFile);
                invalid.id = null;
                xAPIStatementHelper.attached_answer_attachment(invalid, mockAnswer1, mockRegistration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/attach",
                        "display":{"en-US":"attached"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/question",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://activitystrea.ms/schema/1.0/file",
                            "name":{"en-US":"Assignment answer attachment"}
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.attached_answer_attachment(mockFile, mockAnswer1, mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('deleted_answer_attachment:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAnswer1);
                invalid.id = null;
                xAPIStatementHelper.deleted_answer_attachment(mockFile, invalid, mockRegistration);
            });

            it('should do nothing when no file id provided', function() {
                var invalid = angular.copy(mockFile);
                invalid.id = null;
                xAPIStatementHelper.deleted_answer_attachment(invalid, mockAnswer1, mockRegistration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/delete",
                        "display":{"en-US":"deleted"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/question",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://activitystrea.ms/schema/1.0/file",
                            "name":{"en-US":"Assignment answer attachment"}
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.deleted_answer_attachment(mockFile, mockAnswer1, mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('initialize_assignment_question:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                xAPIStatementHelper.initialize_assignment_question(invalid, mockRegistration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US":"initialized"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/question",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name":{"en-US":"Read the poem below, and make notes on syntax, figurative language, patterns of diction and imagery, and form. Then, imagining that you are writing a 1200-word essay, write a critical premise of 20-60 words as we have discussed in class."}
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.initialize_assignment_question(mockAssignment, mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('resume_assignment_question:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                xAPIStatementHelper.resume_assignment_question(invalid, mockRegistration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/resumed",
                        "display":{"en-US":"resumed"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/question",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name":{"en-US":"Read the poem below, and make notes on syntax, figurative language, patterns of diction and imagery, and form. Then, imagining that you are writing a 1200-word essay, write a critical premise of 20-60 words as we have discussed in class."}
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.resume_assignment_question(mockAssignment, mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('exited_assignment_question:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                xAPIStatementHelper.exited_assignment_question(invalid, mockRegistration, mockDuration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/exited",
                        "display":{"en-US":"exited"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "result": {
                        "duration": mockDuration,
                        "success": false,
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/question",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name":{"en-US":"Read the poem below, and make notes on syntax, figurative language, patterns of diction and imagery, and form. Then, imagining that you are writing a 1200-word essay, write a critical premise of 20-60 words as we have discussed in class."}
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.exited_assignment_question(mockAssignment, mockRegistration, mockDuration);
                $httpBackend.flush();
            });
        });

        describe('viewed_page:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://id.tincanapi.com/verb/viewed",
                        "display":{"en-US":"viewed"}
                    },
                    "context":{
                        "contextActivities":{
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://activitystrea.ms/schema/1.0/page"
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.viewed_page();
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://id.tincanapi.com/verb/viewed",
                            "display":{"en-US":"viewed"}
                        },
                        "context":{
                            "contextActivities":{
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://activitystrea.ms/schema/1.0/page"
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.viewed_page();
                    $httpBackend.flush();
                });
            });
        });

        describe('filtered_page:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://xapi.learninganalytics.ubc.ca/verb/filter",
                        "display":{"en-US":"filtered"}
                    },
                    "context":{
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/filters": mockFilters
                        },
                        "contextActivities":{
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://activitystrea.ms/schema/1.0/page"
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.filtered_page(mockFilters);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://xapi.learninganalytics.ubc.ca/verb/filter",
                            "display":{"en-US":"filtered"}
                        },
                        "context":{
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/filters": mockFilters
                            },
                            "contextActivities":{
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://activitystrea.ms/schema/1.0/page"
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.filtered_page(mockFilters);
                    $httpBackend.flush();
                });
            });
        });

        describe('sorted_page:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://xapi.learninganalytics.ubc.ca/verb/sort",
                        "display":{"en-US":"sorted"}
                    },
                    "context":{
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/sort-order": mockSortOrder
                        },
                        "contextActivities":{
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://activitystrea.ms/schema/1.0/page"
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.sorted_page(mockSortOrder);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://xapi.learninganalytics.ubc.ca/verb/sort",
                            "display":{"en-US":"sorted"}
                        },
                        "context":{
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/sort-order": mockSortOrder
                            },
                            "contextActivities":{
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://activitystrea.ms/schema/1.0/page"
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.sorted_page(mockSortOrder);
                    $httpBackend.flush();
                });
            });
        });

        describe('opened_page_section:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/open",
                        "display":{"en-US":"opened"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": sectionName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.opened_page_section(sectionName);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/open",
                            "display":{"en-US":"opened"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": sectionName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.opened_page_section(sectionName);
                    $httpBackend.flush();
                });
            });
        });

        describe('closed_page_section:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/close",
                        "display":{"en-US":"closed"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": sectionName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.closed_page_section(sectionName);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/close",
                            "display":{"en-US":"closed"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": sectionName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.closed_page_section(sectionName);
                    $httpBackend.flush();
                });
            });
        });

        describe('filtered_page_section:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://xapi.learninganalytics.ubc.ca/verb/filter",
                        "display":{"en-US":"filtered"}
                    },
                    "context":{
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/filters": mockFilters
                        },
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": sectionName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.filtered_page_section(sectionName, mockFilters);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://xapi.learninganalytics.ubc.ca/verb/filter",
                            "display":{"en-US":"filtered"}
                        },
                        "context":{
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/filters": mockFilters
                            },
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": sectionName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.filtered_page_section(sectionName, mockFilters);
                    $httpBackend.flush();
                });
            });
        });

        describe('sorted_page_section:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://xapi.learninganalytics.ubc.ca/verb/sort",
                        "display":{"en-US":"sorted"}
                    },
                    "context":{
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/sort-order": mockSortOrder
                        },
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": sectionName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.sorted_page_section(sectionName, mockSortOrder);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://xapi.learninganalytics.ubc.ca/verb/sort",
                            "display":{"en-US":"sorted"}
                        },
                        "context":{
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/sort-order": mockSortOrder
                            },
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": sectionName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.sorted_page_section(sectionName, mockSortOrder);
                    $httpBackend.flush();
                });
            });
        });

        describe('opened_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/open",
                        "display":{"en-US":"opened"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": modalName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.opened_modal(modalName);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/open",
                            "display":{"en-US":"opened"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": modalName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.opened_modal(modalName);
                    $httpBackend.flush();
                });
            });
        });

        describe('closed_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/close",
                        "display":{"en-US":"closed"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": modalName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.closed_modal(modalName);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/close",
                            "display":{"en-US":"closed"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": modalName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.closed_modal(modalName);
                    $httpBackend.flush();
                });
            });
        });

        describe('filtered_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://xapi.learninganalytics.ubc.ca/verb/filter",
                        "display":{"en-US":"filtered"}
                    },
                    "context":{
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/filters": mockFilters
                        },
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": modalName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.filtered_modal(modalName, mockFilters);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://xapi.learninganalytics.ubc.ca/verb/filter",
                            "display":{"en-US":"filtered"}
                        },
                        "context":{
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/filters": mockFilters
                            },
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": modalName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.filtered_modal(modalName, mockFilters);
                    $httpBackend.flush();
                });
            });
        });

        describe('sorted_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://xapi.learninganalytics.ubc.ca/verb/sort",
                        "display":{"en-US":"sorted"}
                    },
                    "context":{
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/sort-order": mockSortOrder
                        },
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": modalName }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.sorted_modal(modalName, mockSortOrder);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://xapi.learninganalytics.ubc.ca/verb/sort",
                            "display":{"en-US":"sorted"}
                        },
                        "context":{
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/sort-order": mockSortOrder
                            },
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": modalName }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.sorted_modal(modalName, mockSortOrder);
                    $httpBackend.flush();
                });
            });
        });

        describe('opened_inline_kaltura_media:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/open",
                        "display":{"en-US":"opened"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("Inline Kaltura Media Attachment"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": "Inline Kaltura Media Attachment" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.opened_inline_kaltura_media(mockFile.name);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/open",
                            "display":{"en-US":"opened"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("Inline Kaltura Media Attachment"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": "Inline Kaltura Media Attachment" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.opened_inline_kaltura_media(mockFile.name);
                    $httpBackend.flush();
                });
            });
        });

        describe('closed_inline_kaltura_media:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/close",
                        "display":{"en-US":"closed"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("Inline Kaltura Media Attachment"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": "Inline Kaltura Media Attachment" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.closed_inline_kaltura_media(mockFile.name);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/close",
                            "display":{"en-US":"closed"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("Inline Kaltura Media Attachment"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": "Inline Kaltura Media Attachment" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.closed_inline_kaltura_media(mockFile.name);
                    $httpBackend.flush();
                });
            });
        });

        describe('opened_attachment_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/open",
                        "display":{"en-US":"opened"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("View Attachment"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": "View Attachment" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.opened_attachment_modal(mockFile.name);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/open",
                            "display":{"en-US":"opened"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("View Attachment"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": "View Attachment" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.opened_attachment_modal(mockFile.name);
                    $httpBackend.flush();
                });
            });
        });

        describe('closed_attachment_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/close",
                        "display":{"en-US":"closed"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("View Attachment"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": "View Attachment" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.closed_attachment_modal(mockFile.name);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/close",
                            "display":{"en-US":"closed"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://localhost:8888/app/attachment/1abcABC123-abcABC123_Z.pdf",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("View Attachment"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": "View Attachment" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.closed_attachment_modal(mockFile.name);
                    $httpBackend.flush();
                });
            });
        });

        describe('opened_embeddable_content_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/open",
                        "display":{"en-US":"opened"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://mock.com/url",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("View Embeddable Content"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": "View Embeddable Content" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.opened_embeddable_content_modal("https://mock.com/url");
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/open",
                            "display":{"en-US":"opened"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://mock.com/url",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("View Embeddable Content"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": "View Embeddable Content" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.opened_embeddable_content_modal("https://mock.com/url");
                    $httpBackend.flush();
                });
            });
        });

        describe('closed_embeddable_content_modal:', function() {
            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/close",
                        "display":{"en-US":"closed"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://mock.com/url",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("View Embeddable Content"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": "View Embeddable Content" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.closed_embeddable_content_modal("https://mock.com/url");
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/close",
                            "display":{"en-US":"closed"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://mock.com/url",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("View Embeddable Content"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": "View Embeddable Content" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.closed_embeddable_content_modal("https://mock.com/url");
                    $httpBackend.flush();
                });
            });
        });

        describe('opened_answer_replies_section:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAnswer1);
                invalid.id = null;
                xAPIStatementHelper.opened_answer_replies_section(invalid);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/open",
                        "display":{"en-US":"opened"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("Answer replies"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": "Answer replies" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.opened_answer_replies_section(mockAnswer1);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/open",
                            "display":{"en-US":"opened"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("Answer replies"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": "Answer replies" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.opened_answer_replies_section(mockAnswer1);
                    $httpBackend.flush();
                });
            });
        });

        describe('closed_answer_replies_section:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAnswer1);
                invalid.id = null;
                xAPIStatementHelper.closed_answer_replies_section(invalid);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://activitystrea.ms/schema/1.0/close",
                        "display":{"en-US":"closed"}
                    },
                    "context":{
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/#"+mockLocationPath,
                                "objectType":"Activity"
                            }],
                            "other":[{
                                "id": mockLocationAbsUrl,
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("Answer replies"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": "Answer replies" }
                        }
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.closed_answer_replies_section(mockAnswer1);
                $httpBackend.flush();
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"

                    var expectedStatement = {
                        "id": mockStatementId,
                        "timestamp": mockTimestamp,
                        "verb":{
                            "id":"http://activitystrea.ms/schema/1.0/close",
                            "display":{"en-US":"closed"}
                        },
                        "context":{
                            "contextActivities":{
                                "parent":[{
                                    "id": "https://localhost:8888/app/#"+expectedLocationPath,
                                    "objectType":"Activity"
                                }],
                                "other":[{
                                    "id": expectedLocationAbsUrl,
                                    "objectType":"Activity"
                                },{
                                    "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("Answer replies"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": "Answer replies" }
                            }
                        }
                    };
                    $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                    xAPIStatementHelper.closed_answer_replies_section(mockAnswer1);
                    $httpBackend.flush();
                });
            });
        });

        describe('initialize_comparison_question:', function() {
            it('should do nothing when no answer id provided', function() {
                xAPIStatementHelper.initialize_comparison_question([], 1, "random", mockRegistration);
            });

            it('should generate a valid statement', function() {
                var comparisonNumber = 1

                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US":"initialized"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/4abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/5abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/comparison/1abcABC123-abcABC123_Z/question",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name": { "en-US": "Assignment comparison #"+comparisonNumber },
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/comparison": comparisonNumber,
                                "http://xapi.learninganalytics.ubc.ca/extension/score-algorithm": "random"
                            }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.initialize_comparison_question(mockComparison, comparisonNumber, "random", mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('resume_comparison_question:', function() {
            it('should do nothing when no answer id provided', function() {
                xAPIStatementHelper.resume_comparison_question([], 1, "random", mockRegistration);
            });

            it('should generate a valid statement', function() {
                var comparisonNumber = 1

                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/resumed",
                        "display":{"en-US":"resumed"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/4abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/5abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/comparison/1abcABC123-abcABC123_Z/question",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name": { "en-US": "Assignment comparison #"+comparisonNumber },
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/comparison": comparisonNumber,
                                "http://xapi.learninganalytics.ubc.ca/extension/score-algorithm": "random"
                            }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.resume_comparison_question(mockComparison, comparisonNumber, "random", mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('exited_comparison_question:', function() {
            it('should do nothing when no answer id provided', function() {
                xAPIStatementHelper.exited_comparison_question([], 1, "random", mockRegistration);
            });

            it('should generate a valid statement', function() {
                var comparisonNumber = 1

                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/exited",
                        "display":{"en-US":"exited"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/4abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/5abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "result": {
                        "duration": mockDuration,
                        "success": false
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/comparison/1abcABC123-abcABC123_Z/question",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name": { "en-US": "Assignment comparison #"+comparisonNumber },
                            "extensions": {
                                "http://xapi.learninganalytics.ubc.ca/extension/comparison": comparisonNumber,
                                "http://xapi.learninganalytics.ubc.ca/extension/score-algorithm": "random"
                            }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.exited_comparison_question(mockComparison, comparisonNumber, "random", mockRegistration, mockDuration);
                $httpBackend.flush();
            });
        });

        describe('interacted_comparison_criterion_solution:', function() {
            it('should do nothing when no comparison id provided', function() {
                var invalid = angular.copy(mockComparison);
                invalid.id = null;
                xAPIStatementHelper.interacted_comparison_criterion_solution(invalid, mockComparison.comparison_criteria[0], mockRegistration);
            });

            it('should do nothing when no comparison_criterion id provided', function() {
                var invalid = angular.copy(mockComparison.comparison_criteria[0]);
                invalid.id = null;
                xAPIStatementHelper.interacted_comparison_criterion_solution(mockComparison, invalid, mockRegistration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/interacted",
                        "display":{"en-US":"interacted"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/comparison/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/4abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/comparison/1abcABC123-abcABC123_Z/question",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "result": {
                        "response": "Undecided"
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/comparison/criterion/1abcABC123-abcABC123_Z",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/solution",
                            "name": { "en-US": "Assignment criterion comparison" }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.interacted_comparison_criterion_solution(mockComparison, mockComparison.comparison_criteria[0], mockRegistration);
                $httpBackend.flush();

                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/interacted",
                        "display":{"en-US":"interacted"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/comparison/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/criterion/5abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/comparison/1abcABC123-abcABC123_Z/question",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "result": {
                        "response": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z"
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/comparison/criterion/2abcABC123-abcABC123_Z",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/solution",
                            "name": { "en-US": "Assignment criterion comparison" }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.interacted_comparison_criterion_solution(mockComparison, mockComparison.comparison_criteria[1], mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('interacted_answer_comment:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockComment);
                invalid.id = null;
                xAPIStatementHelper.interacted_answer_comment(invalid, mockRegistration, mockDuration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/interacted",
                        "display":{"en-US":"interacted"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/question",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "result": {
                        "duration": mockDuration,
                        "response": "<p>test123213t4453123123</p>\n",
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/character-count": 22,
                            "http://xapi.learninganalytics.ubc.ca/extension/word-count": 1
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/answer/comment/3703ABC123-abcABC123_Z",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://activitystrea.ms/schema/1.0/comment",
                            "name": { "en-US": "Assignment answer evaluation comment" }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.interacted_answer_comment(mockComment, mockRegistration, mockDuration);
                $httpBackend.flush();
            });
        });

        describe('initialize_self_evaluation_question:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockComment);
                invalid.id = null;
                xAPIStatementHelper.initialize_self_evaluation_question(invalid, mockRegistration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US":"initialized"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/self-evaluation",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name": { "en-US": "Assignment self-evaluation" }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.initialize_self_evaluation_question(mockComment, mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('resume_self_evaluation_question:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockComment);
                invalid.id = null;
                xAPIStatementHelper.resume_self_evaluation_question(invalid, mockRegistration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/resumed",
                        "display":{"en-US":"resumed"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/self-evaluation",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name": { "en-US": "Assignment self-evaluation" }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.resume_self_evaluation_question(mockComment, mockRegistration);
                $httpBackend.flush();
            });
        });

        describe('exited_self_evaluation_question:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockComment);
                invalid.id = null;
                xAPIStatementHelper.exited_self_evaluation_question(invalid, mockRegistration, mockDuration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/exited",
                        "display":{"en-US":"exited"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "result": {
                        "duration": mockDuration,
                        "success": false
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/self-evaluation",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/question",
                            "name": { "en-US": "Assignment self-evaluation" }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.exited_self_evaluation_question(mockComment, mockRegistration, mockDuration);
                $httpBackend.flush();
            });
        });

        describe('interacted_self_evaluation_review:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockComment);
                invalid.id = null;
                xAPIStatementHelper.interacted_self_evaluation_review(invalid, mockRegistration, mockDuration);
            });

            it('should generate a valid statement', function() {
                var expectedStatement = {
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/interacted",
                        "display":{"en-US":"interacted"}
                    },
                    "context":{
                        "registration": mockRegistration,
                        "contextActivities":{
                            "parent":[{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z/self-evaluation",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id": "https://localhost:8888/app/xapi/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id": "https://localhost:8888/app/xapi/answer/279cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "result": {
                        "duration": mockDuration,
                        "response": "<p>test123213t4453123123</p>\n",
                        "extensions": {
                            "http://xapi.learninganalytics.ubc.ca/extension/character-count": 22,
                            "http://xapi.learninganalytics.ubc.ca/extension/word-count": 1
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/xapi/answer/comment/3703ABC123-abcABC123_Z",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://activitystrea.ms/schema/1.0/review",
                            "name": { "en-US": "Assignment self-evaluation review" }
                        },
                    }
                };
                $httpBackend.expectPOST(/\/api\/statements$/, expectedStatement).respond({});
                xAPIStatementHelper.interacted_self_evaluation_review(mockComment, mockRegistration, mockDuration);
                $httpBackend.flush();
            });
        });
    });
});