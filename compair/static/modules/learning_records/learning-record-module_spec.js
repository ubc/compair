describe('learning-record-module', function () {
    var $httpBackend;
    var id = "1abcABC123-abcABC123_Z";
    beforeEach(module('ubc.ctlt.compair.learning_records.learning_record'));
    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('LearningRecordStatementHelper', function () {
        var $rootScope, $location, Session, LearningRecordStatementHelper, xAPI, LearningRecordSettings;
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
                "student_number": null,
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
        var mockUUID = "caece01c-ea5c-472d-9f9c-be864a3442d5";
        var mockDuration = "PT0.007S";
        var mockStarted = "2016-11-26T00:35:23.389Z";
        var mockEnded = "2016-11-26T00:35:33.389Z";
        var mockLocationAbsUrl = "https://localhost:1888/app/#/mock/location/";
        var mockLocationPath = "/mock/location/";
        var mockTracking =  {
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
        }

        beforeEach(inject(function (_$rootScope_, _$location_, Session, _LearningRecordStatementHelper_, _xAPI_, _LearningRecordSettings_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            LearningRecordStatementHelper = _LearningRecordStatementHelper_;
            xAPI = _xAPI_;
            LearningRecordSettings = _LearningRecordSettings_;
            LearningRecordSettings.xapi_enabled = true;
            LearningRecordSettings.caliper_enabled = true;
            LearningRecordSettings.baseUrl = "https://localhost:8888/";

            spyOn(navigator, 'sendBeacon').and.returnValue(true);
            spyOn(TinCan.Utils, 'getUUID').and.returnValue(mockStatementId);
            spyOn(window, 'Date').and.returnValue({ toISOString: function() { return mockTimestamp; } });
            spyOn(Session, 'isLoggedIn').and.returnValue(true);

            absUrlSpy = spyOn($location, 'absUrl').and.returnValue(mockLocationAbsUrl);
            pathSpy = spyOn($location, 'path').and.returnValue(mockLocationPath);
        }));

        describe('initialize_assignment_question:', function() {
            it('should do nothing when no assignment id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                LearningRecordStatementHelper.initialize_assignment_question(invalid, mockTracking);
                expect(navigator.sendBeacon).not.toHaveBeenCalled();
            });

            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.initialize_assignment_question(mockAssignment, mockTracking);
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US": "initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/question",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/question/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US":"initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent": [{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition": {
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"AssessmentItemEvent",
                    "action":"Started",
                    "profile":"AssessmentProfile",
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/question",
                        "type":"AssessmentItem"
                    },
                    "generated":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/question/attempt/"+mockUUID,
                        "type":"Attempt",
                        "assignable":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/question",
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type": "AssessmentEvent",
                    "action": "Started",
                    "profile": "AssessmentProfile",
                    "object": {
                        "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                        "type": "Assessment"
                    },
                    "generated": {
                        "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                        "type": "Attempt",
                        "assignable": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
            });
        });

        describe('exited_assignment_question:', function() {
            it('should do nothing when no assignment id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                LearningRecordStatementHelper.exited_assignment_question(invalid, mockTracking);
            });

            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.exited_assignment_question(mockAssignment, mockTracking);
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/exited",
                        "display":{"en-US":"exited"}
                    },
                    "result":{
                        "success":false,
                        "duration": mockDuration
                    },
                    "context":{
                        "registration":"caece01c-ea5c-472d-9f9c-be864a3442d5",
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/caece01c-ea5c-472d-9f9c-be864a3442d5",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted,
                                    "duration": mockDuration,
                                    "endedAtTime": mockEnded
                                }
                            }
                        }
                    },
                    "course_id": "1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"AssessmentEvent",
                    "action":"Paused",
                    "profile":"AssessmentProfile",
                    "object":{
                       "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                       "type":"Assessment"
                    },
                    "generated":{
                       "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/caece01c-ea5c-472d-9f9c-be864a3442d5",
                       "type":"Attempt",
                       "assignable":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                       "startedAtTime":mockStarted,
                       "duration":mockDuration,
                       "endedAtTime":mockEnded
                    },
                    "eventTime":mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z"
                 }));
            });
        });


        describe('initialize_comparison_question:', function() {
            it('should do nothing when no assignment id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                LearningRecordStatementHelper.initialize_comparison_question(invalid, 1, mockTracking);
            });

            it('should generate a valid statement', function() {
                var comparisonNumber = 5;
                var evaluation1 = 9;
                var evaluation2 = 10;
                LearningRecordStatementHelper.initialize_comparison_question(mockAssignment, comparisonNumber, mockTracking);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US": "initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/comparison/question/"+comparisonNumber,
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/comparison/question/"+comparisonNumber+"/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US": "initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation1,
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation1+"/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US": "initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation2,
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation2+"/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US":"initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent": [{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition": {
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"AssessmentItemEvent",
                    "action":"Started",
                    "profile":"AssessmentProfile",
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/comparison/question/"+comparisonNumber,
                        "type":"AssessmentItem"
                    },
                    "generated":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/comparison/question/"+comparisonNumber+"/attempt/"+mockUUID,
                        "type":"Attempt",
                        "assignable":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/comparison/question/"+comparisonNumber,
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"AssessmentItemEvent",
                    "action":"Started",
                    "profile":"AssessmentProfile",
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation1,
                        "type":"AssessmentItem"
                    },
                    "generated":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation1+"/attempt/"+mockUUID,
                        "type":"Attempt",
                        "assignable":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation1,
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"AssessmentItemEvent",
                    "action":"Started",
                    "profile":"AssessmentProfile",
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation2,
                        "type":"AssessmentItem"
                    },
                    "generated":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation2+"/attempt/"+mockUUID,
                        "type":"Attempt",
                        "assignable":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/evaluation/question/"+evaluation2,
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type": "AssessmentEvent",
                    "action": "Started",
                    "profile": "AssessmentProfile",
                    "object": {
                        "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                        "type": "Assessment"
                    },
                    "generated": {
                        "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                        "type": "Attempt",
                        "assignable": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
            });
        });

        describe('exited_comparison_question:', function() {
            it('should do nothing when no assignment id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                LearningRecordStatementHelper.exited_comparison_question(invalid, mockTracking);
            });

            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.exited_comparison_question(mockAssignment, mockTracking);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/exited",
                        "display":{"en-US":"exited"}
                    },
                    "result":{
                        "success":false,
                        "duration": mockDuration
                    },
                    "context":{
                        "registration":"caece01c-ea5c-472d-9f9c-be864a3442d5",
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/caece01c-ea5c-472d-9f9c-be864a3442d5",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted,
                                    "duration": mockDuration,
                                    "endedAtTime": mockEnded
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type": "AssessmentEvent",
                    "action": "Paused",
                    "profile": "AssessmentProfile",
                    "object": {
                      "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                      "type": "Assessment"
                    },
                    "generated": {
                      "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                      "type": "Attempt",
                      "assignable": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                      "startedAtTime": mockStarted,
                      "duration": mockDuration,
                      "endedAtTime": mockEnded
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
            });
        });


        describe('initialize_self_evaluation_question:', function() {
            it('should do nothing when no assignment id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                LearningRecordStatementHelper.initialize_self_evaluation_question(invalid, mockTracking);
            });

            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.initialize_self_evaluation_question(mockAssignment, mockTracking);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US": "initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/self-evaluation/question",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            },{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/self-evaluation/question/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/initialized",
                        "display":{"en-US":"initialized"}
                    },
                    "context":{
                        "registration": mockUUID,
                        "contextActivities":{
                            "parent": [{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                        "objectType":"Activity",
                        "definition": {
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"AssessmentItemEvent",
                    "action":"Started",
                    "profile":"AssessmentProfile",
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/self-evaluation/question",
                        "type":"AssessmentItem"
                    },
                    "generated":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/self-evaluation/question/attempt/"+mockUUID,
                        "type":"Attempt",
                        "assignable":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/self-evaluation/question",
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type": "AssessmentEvent",
                    "action": "Started",
                    "profile":"AssessmentProfile",
                    "object": {
                        "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                        "type": "Assessment"
                    },
                    "generated": {
                        "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                        "type": "Attempt",
                        "assignable": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                        "startedAtTime": mockStarted
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
            });
        });


        describe('exited_self_evaluation_question:', function() {
            it('should do nothing when no assignment id provided', function() {
                var invalid = angular.copy(mockAssignment);
                invalid.id = null;
                LearningRecordStatementHelper.exited_self_evaluation_question(invalid, mockTracking);
            });

            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.exited_self_evaluation_question(mockAssignment, mockTracking);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
                    "id": mockStatementId,
                    "timestamp": mockTimestamp,
                    "verb":{
                        "id":"http://adlnet.gov/expapi/verbs/exited",
                        "display":{"en-US":"exited"}
                    },
                    "result":{
                        "success":false,
                        "duration": mockDuration
                    },
                    "context":{
                        "registration":"caece01c-ea5c-472d-9f9c-be864a3442d5",
                        "contextActivities":{
                            "parent":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }],
                            "grouping":[{
                                "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/caece01c-ea5c-472d-9f9c-be864a3442d5",
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://adlnet.gov/expapi/activities/attempt",
                            "extensions":{
                                "http://id.tincanapi.com/extension/attempt":{
                                    "startedAtTime": mockStarted,
                                    "duration": mockDuration,
                                    "endedAtTime": mockEnded
                                }
                            }
                        }
                    },
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type": "AssessmentEvent",
                    "action": "Paused",
                    "profile": "AssessmentProfile",
                    "object": {
                      "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                      "type": "Assessment"
                    },
                    "generated": {
                      "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/attempt/"+mockUUID,
                      "type": "Attempt",
                      "assignable": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z",
                      "startedAtTime": mockStarted,
                      "duration": mockDuration,
                      "endedAtTime": mockEnded
                    },
                    "eventTime": mockTimestamp,
                    "course_id":"1abcABC123-abcABC123_Z",
                }));
            });
        });

        describe('viewed_page:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.viewed_page();

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"NavigationEvent",
                    "action":"NavigatedTo",
                    "profile":"ReadingProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.viewed_page();

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"NavigationEvent",
                        "action":"NavigatedTo",
                        "profile":"ReadingProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('filtered_page:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.filtered_page(mockFilters);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"SearchEvent",
                    "action":"Searched",
                    "profile":"SearchProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl,
                        "filters": mockFilters
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.filtered_page(mockFilters);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"SearchEvent",
                        "action":"Searched",
                        "profile":"SearchProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl,
                            "filters": mockFilters
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('sorted_page:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.sorted_page(mockSortOrder);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"SearchEvent",
                    "action":"Searched",
                    "profile":"SearchProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl,
                        "sortOrder": mockSortOrder
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.sorted_page(mockSortOrder);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"SearchEvent",
                        "action":"Searched",
                        "profile":"SearchProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl,
                            "sortOrder": mockSortOrder
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('opened_page_section:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.opened_page_section(sectionName);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Showed",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "type":"Frame",
                        "name": sectionName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.opened_page_section(sectionName);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Showed",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "type":"Frame",
                            "name": sectionName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('closed_page_section:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.closed_page_section(sectionName);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Hid",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "type":"Frame",
                        "name": sectionName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.closed_page_section(sectionName);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Hid",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "type":"Frame",
                            "name": sectionName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('filtered_page_section:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.filtered_page_section(sectionName, mockFilters);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"SearchEvent",
                    "action":"Searched",
                    "profile":"SearchProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "type":"Frame",
                        "name": sectionName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl,
                        "filters": mockFilters
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.filtered_page_section(sectionName, mockFilters);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"SearchEvent",
                        "action":"Searched",
                        "profile":"SearchProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "type":"Frame",
                            "name": sectionName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl,
                            "filters": mockFilters
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('sorted_page_section:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.sorted_page_section(sectionName, mockSortOrder);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"SearchEvent",
                    "action":"Searched",
                    "profile":"SearchProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(sectionName),
                        "type":"Frame",
                        "name": sectionName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl,
                        "sortOrder": mockSortOrder
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.sorted_page_section(sectionName, mockSortOrder);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"SearchEvent",
                        "action":"Searched",
                        "profile":"SearchProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(sectionName),
                            "type":"Frame",
                            "name": sectionName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl,
                            "sortOrder": mockSortOrder
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('opened_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.opened_modal(modalName);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Showed",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "type":"Frame",
                        "name": modalName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.opened_modal(modalName);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Showed",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "type":"Frame",
                            "name": modalName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('closed_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.closed_modal(modalName);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Hid",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "type":"Frame",
                        "name": modalName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.closed_modal(modalName);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Hid",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "type":"Frame",
                            "name": modalName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('filtered_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.filtered_modal(modalName, mockFilters);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"SearchEvent",
                    "action":"Searched",
                    "profile":"SearchProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "type":"Frame",
                        "name": modalName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl,
                        "filters": mockFilters
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.filtered_modal(modalName, mockFilters);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"SearchEvent",
                        "action":"Searched",
                        "profile":"SearchProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "type":"Frame",
                            "name": modalName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl,
                            "filters": mockFilters
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('sorted_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.sorted_modal(modalName, mockSortOrder);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"SearchEvent",
                    "action":"Searched",
                    "profile":"SearchProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(modalName),
                        "type":"Frame",
                        "name": modalName
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl,
                        "sortOrder": mockSortOrder
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.sorted_modal(modalName, mockSortOrder);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"SearchEvent",
                        "action":"Searched",
                        "profile":"SearchProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(modalName),
                            "type":"Frame",
                            "name": modalName
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl,
                            "sortOrder": mockSortOrder
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('opened_inline_kaltura_media:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.opened_inline_kaltura_media(mockFile.name);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(mockFile.name),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": mockFile.name }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Showed",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(mockFile.name),
                        "type":"Frame",
                        "name": mockFile.name
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.opened_inline_kaltura_media(mockFile.name);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                    "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(mockFile.name),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": mockFile.name }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Showed",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(mockFile.name),
                            "type":"Frame",
                            "name": mockFile.name
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('closed_inline_kaltura_media:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.closed_inline_kaltura_media(mockFile.name);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(mockFile.name),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": mockFile.name }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Hid",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent(mockFile.name),
                        "type":"Frame",
                        "name": mockFile.name
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.closed_inline_kaltura_media(mockFile.name);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                    "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(mockFile.name),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": mockFile.name }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Hid",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent(mockFile.name),
                            "type":"Frame",
                            "name": mockFile.name
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('opened_attachment_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.opened_attachment_modal(mockFile.name);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": mockFile.name }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Showed",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                        "type":"Frame",
                        "name": mockFile.name
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.opened_attachment_modal(mockFile.name);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                    "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": mockFile.name }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Showed",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                            "type":"Frame",
                            "name": mockFile.name
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });


        describe('closed_attachment_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.closed_attachment_modal(mockFile.name);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": mockFile.name }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Hid",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                        "type":"Frame",
                        "name": mockFile.name
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.closed_attachment_modal(mockFile.name);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                    "id": "https://localhost:8888/app/attachment/"+mockFile.name,
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": mockFile.name }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Hid",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent(mockFile.name),
                            "type":"Frame",
                            "name": mockFile.name
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('opened_embeddable_content_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.opened_embeddable_content_modal("https://mock.com/url");

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": "https://mock.com/url" }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Showed",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                        "type":"Frame",
                        "name": "https://mock.com/url"
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.opened_embeddable_content_modal("https://mock.com/url");

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": "https://mock.com/url" }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Showed",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                            "type":"Frame",
                            "name": "https://mock.com/url"
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('closed_embeddable_content_modal:', function() {
            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.closed_embeddable_content_modal("https://mock.com/url");

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                            "name": { "en-US": "https://mock.com/url" }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Hid",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                        "type":"Frame",
                        "name": "https://mock.com/url"
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.closed_embeddable_content_modal("https://mock.com/url");

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://xapi.learninganalytics.ubc.ca/activitytype/modal",
                                "name": { "en-US": "https://mock.com/url" }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Hid",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?modal="+encodeURIComponent("https://mock.com/url"),
                            "type":"Frame",
                            "name": "https://mock.com/url"
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('opened_answer_replies_section:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAnswer1);
                invalid.id = null;
                LearningRecordStatementHelper.opened_answer_replies_section(invalid);
            });

            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.opened_answer_replies_section(mockAnswer1);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": "answer/407cABC123-abcABC123_Z/replies" }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Showed",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                        "type":"Frame",
                        "name": "answer/407cABC123-abcABC123_Z/replies"
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.opened_answer_replies_section(mockAnswer1);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                    "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/answer/407cABC123-abcABC123_Z",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": "answer/407cABC123-abcABC123_Z/replies" }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Showed",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                            "type":"Frame",
                            "name": "answer/407cABC123-abcABC123_Z/replies"
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });

        describe('closed_answer_replies_section:', function() {
            it('should do nothing when no answer id provided', function() {
                var invalid = angular.copy(mockAnswer1);
                invalid.id = null;
                LearningRecordStatementHelper.closed_answer_replies_section(invalid);
            });

            it('should generate a valid statement', function() {
                LearningRecordStatementHelper.closed_answer_replies_section(mockAnswer1);

                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/answer/407cABC123-abcABC123_Z",
                                "objectType":"Activity"
                            }]
                        }
                    },
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                        "objectType":"Activity",
                        "definition":{
                            "type":"http://id.tincanapi.com/activitytype/section",
                            "name": { "en-US": "answer/407cABC123-abcABC123_Z/replies" }
                        }
                    }
                }));
                expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                    "type":"Event",
                    "action":"Hid",
                    "profile":"GeneralProfile",
                    "object":{
                        "id":"https://localhost:8888/app/#"+mockLocationPath,
                        "type":"WebPage"
                    },
                    "target": {
                        "id":"https://localhost:8888/app/#"+mockLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                        "type":"Frame",
                        "name": "answer/407cABC123-abcABC123_Z/replies"
                    },
                    "extensions":{
                        "absoluteUrl": mockLocationAbsUrl
                    },
                    "eventTime": mockTimestamp
                }));
            });

            describe('with additional pound "#":', function() {
                beforeEach(function () {
                    absUrlSpy.and.returnValue(mockLocationAbsUrl+"#answer");
                    pathSpy.and.returnValue(mockLocationPath+"#answer");
                });

                it('should generate a valid statement', function() {
                    expectedLocationPath  = mockLocationPath+"%23answer"
                    expectedLocationAbsUrl = mockLocationAbsUrl+"%23answer"
                    LearningRecordStatementHelper.closed_answer_replies_section(mockAnswer1);

                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/xapi/statements', JSON.stringify({
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
                                    "id": "https://localhost:8888/app/course/1abcABC123-abcABC123_Z/assignment/9abcABC123-abcABC123_Z/answer/407cABC123-abcABC123_Z",
                                    "objectType":"Activity"
                                }]
                            }
                        },
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                            "objectType":"Activity",
                            "definition":{
                                "type":"http://id.tincanapi.com/activitytype/section",
                                "name": { "en-US": "answer/407cABC123-abcABC123_Z/replies" }
                            }
                        }
                    }));
                    expect(navigator.sendBeacon).toHaveBeenCalledWith('/api/learning_records/caliper/events', JSON.stringify({
                        "type":"Event",
                        "action":"Hid",
                        "profile":"GeneralProfile",
                        "object":{
                            "id":"https://localhost:8888/app/#"+expectedLocationPath,
                            "type":"WebPage"
                        },
                        "target": {
                            "id":"https://localhost:8888/app/#"+expectedLocationPath+"?section="+encodeURIComponent("answer/407cABC123-abcABC123_Z/replies"),
                            "type":"Frame",
                            "name": "answer/407cABC123-abcABC123_Z/replies"
                        },
                        "extensions":{
                            "absoluteUrl": expectedLocationAbsUrl
                        },
                        "eventTime": mockTimestamp
                    }));
                });
            });
        });
    });
});