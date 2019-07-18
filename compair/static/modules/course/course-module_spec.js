describe('course-module', function () {
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
        "start_date": "2015-01-02T23:00:00",
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
        "sandbox": false
    };
    beforeEach(module('ubc.ctlt.compair.course'));
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

    describe('CourseController', function () {
        var $rootScope, createController, $location, $uibModal, $q, LearningRecordSettings;

        beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$uibModal_, _$q_, _LearningRecordSettings_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            $uibModal = _$uibModal_;
            $q = _$q_;
            createController = function (params, resolvedData) {
                return $controller('CourseController', {
                    $scope: $rootScope,
                    $routeParams: params || {},
                    resolvedData: resolvedData || {}
                });
            }
            LearningRecordSettings = _LearningRecordSettings_;
            LearningRecordSettings.xapi_enabled = true;
            LearningRecordSettings.caliper_enabled = true;
            LearningRecordSettings.baseUrl = "https://localhost:8888/";
        }));

        it('should have correct initial states', function () {
            //double check nothing to initialize
        });

        describe('view:', function () {
            var controller;
            describe('create', function () {
                var toaster;
                var course = {
                    "name": "Test111",
                    "year": 2015,
                    "term": "Winter",
                    "sandbox": false,
                    "start_date": "2015-01-02T23:00:00",
                    "end_date": null,
                    "assignment_count": 0,
                    "student_assignment_count": 0,
                    "student_count": 0
                };
                beforeEach(inject(function (_Toaster_) {
                    toaster = _Toaster_;
                    spyOn(toaster, 'warning');
                }));

                beforeEach(function () {
                    controller = createController({}, {
                        loggedInUser: angular.copy(mockUser),
                    });
                });

                it('should be correctly initialized', function () {
                    //double check nothing to initialize
                });

                it('should warn when start date is not before end date', function () {
                    $rootScope.course = angular.copy(course);
                    $rootScope.course.id = undefined;
                    $rootScope.date.course_start.date = new Date();
                    $rootScope.date.course_start.time = new Date();
                    $rootScope.date.course_end.date = new Date();
                    $rootScope.date.course_end.time = new Date();
                    $rootScope.date.course_end.date.setDate($rootScope.date.course_end.date.getDate()-1);
                    var currentPath = $location.path();

                    $rootScope.save();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Course Not Saved', 'Please set course end time after course start time and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should be able to save new course', function () {
                    $rootScope.course = angular.copy(course);
                    $rootScope.course.id = undefined;
                    $rootScope.date.course_start.date = new Date(2015,1,2,0,0,0,0);
                    $rootScope.date.course_start.time = new Date(2015,1,2,0,0,0,0);
                    $httpBackend.expectPOST('/api/courses', $rootScope.course).respond(angular.merge({}, course, {id: "2abcABC123-abcABC123_Z"}));
                    $rootScope.save();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/2abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });
            });

            describe('edit', function () {
                var editCourse;
                var toaster;
                beforeEach(inject(function (_Toaster_) {
                    toaster = _Toaster_;
                    spyOn(toaster, 'warning');
                }));

                beforeEach(function () {
                    editCourse = angular.copy(mockCourse);
                    editCourse.id = "2abcABC123-abcABC123_Z";
                    controller = createController({courseId: editCourse.id}, {
                        course: editCourse,
                        loggedInUser: angular.copy(mockUser),
                    });
                });

                it('should be correctly initialized', function () {
                    expect($rootScope.course).toEqualData(_.merge(editCourse));
                    expect($rootScope.course).toEqualData(editCourse);
                });

                it('should warn when start date is not before end date', function () {
                    $rootScope.date.course_start.date = new Date();
                    $rootScope.date.course_start.time = new Date();
                    $rootScope.date.course_end.date = new Date();
                    $rootScope.date.course_end.time = new Date();
                    $rootScope.date.course_end.date.setDate($rootScope.date.course_end.date.getDate()-1);
                    var currentPath = $location.path();

                    $rootScope.save();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Course Not Saved', 'Please set course end time after course start time and save again.');
                    expect($location.path()).toEqual(currentPath);
                });

                it('should be able to save edited course', function () {
                    $rootScope.course.name = 'new name';
                    $rootScope.course.year = 2016;
                    $rootScope.course.term = "Summer";
                    $rootScope.course.sandbox = false;
                    $httpBackend.expectPOST('/api/courses/2abcABC123-abcABC123_Z', $rootScope.course).respond($rootScope.course);
                    $rootScope.save();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($location.path()).toEqual('/course/2abcABC123-abcABC123_Z');
                    expect($rootScope.submitted).toBe(false);
                });

                it('should enable save button even if save failed', function() {
                    $httpBackend.expectPOST('/api/courses/2abcABC123-abcABC123_Z', $rootScope.course).respond(400, '');
                    $rootScope.save();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                });
            });
        });
    });

    describe('CourseSelectModalController', function () {
        var $rootScope, createController, $location, $uibModal, $q;

        beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$uibModal_, _$q_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            $uibModal = _$uibModal_;
            $q = _$q_;
            modalInstance = {
                close: jasmine.createSpy('modalInstance.close'),
                dismiss: jasmine.createSpy('modalInstance.dismiss'),
                result: {
                    then: jasmine.createSpy('modalInstance.result.then')
                }
            };
            createController = function (params) {
                return $controller('CourseSelectModalController', {
                    $scope: $rootScope,
                    $uibModalInstance: modalInstance,
                    $routeParams: params || {}
                });
            }
        }));

        describe('view:', function () {
            var controller;
            var toaster;
            var courses = [
                {
                    "available": false,
                    "created": "2016-07-29T19:34:40",
                    "assignment_count": 0,
                    "student_assignment_count": 0,
                    "student_count": 0,
                    "end_date": "2017-04-28T23:00:00",
                    "id": "1abcABC123-abcABC123_Z",
                    "lti_linked": false,
                    "groups_locked": false,
                    "modified": "2016-08-18T16:44:39",
                    "name": "Another course",
                    "start_date": "2017-01-02T23:00:00",
                    "term": "Summer",
                    "year": 2016,
                    "sandbox": false
                },
                {
                    "available": true,
                    "created": "2016-10-04T21:32:54",
                    "assignment_count": 0,
                    "student_assignment_count": 0,
                    "student_count": 0,
                    "end_date": "2017-02-11T07:59:00",
                    "id": "2abcABC123-abcABC123_Z",
                    "lti_linked": false,
                    "groups_locked": false,
                    "modified": "2016-10-04T21:32:54",
                    "name": "test course",
                    "start_date": "2016-10-03T07:00:00",
                    "term": "asdasdasd",
                    "year": 2016,
                    "sandbox": false
                }
            ]
            beforeEach(inject(function (_Toaster_) {
                toaster = _Toaster_;
                spyOn(toaster, 'warning');
            }));

            beforeEach(function () {
                controller = createController();
                $httpBackend.expectGET('/api/users/courses?page=1&perPage=10').respond({
                    'objects': courses,
                    'page': 1,
                    'pages': 1,
                    'per_page': 10,
                    'total': 2
                });
                $httpBackend.flush();
            });

            it('should have correct initial states', function () {
                expect($rootScope.submitted).toBe(false);
                expect($rootScope.totalNumCourses).toEqual(courses.length);
                expect($rootScope.courseFilters).toEqual({
                    page: 1,
                    perPage: 10
                });
                expect($rootScope.courses).toEqual(courses);
                expect($rootScope.showDuplicateForm).toBe(false);
                expect($rootScope.course).toEqual({
                    year: new Date().getFullYear(),
                    name: ""
                });
                expect($rootScope.format).toEqual('dd-MMMM-yyyy');
            });

            describe('select existing:', function () {
                it('should close dialog when existing course selected', function() {
                    $rootScope.selectCourse(courses[0].id);
                    expect(modalInstance.close).toHaveBeenCalledWith(courses[0].id);
                });
            });

            describe('select new:', function () {
                var course = {
                    "name": "Test111",
                    "year": 2015,
                    "term": "Winter",
                    "sandbox": false,
                    "start_date": "2015-01-02T23:00:00",
                    "end_date": null,
                    "assignment_count": 0,
                    "student_assignment_count": 0,
                    "student_count": 0
                };

                it('should warn when start date is not before end date', function () {
                    $rootScope.course = angular.copy(course);
                    $rootScope.course.id = undefined;
                    $rootScope.date.course_start.date = new Date();
                    $rootScope.date.course_start.time = new Date();
                    $rootScope.date.course_end.date = new Date();
                    $rootScope.date.course_end.time = new Date();
                    $rootScope.date.course_end.date.setDate($rootScope.date.course_end.date.getDate()-1);

                    $rootScope.save();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Course Not Saved', 'Please set course end time after course start time and save again.');
                    expect(modalInstance.close.calls.count()).toEqual(0);
                });

                it('should be able to save new course', function () {
                    $rootScope.course = angular.copy(course);
                    var newCourseId = "3abcABC123-abcABC123_Z"
                    $rootScope.course.id = undefined;
                    $rootScope.date.course_start.date = new Date(2015,1,2,0,0,0,0);
                    $rootScope.date.course_start.time = new Date(2015,1,2,0,0,0,0);
                    $httpBackend.expectPOST('/api/courses', $rootScope.course).respond(angular.merge({}, course, {id: newCourseId}));
                    $rootScope.save();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                    expect(modalInstance.close).toHaveBeenCalledWith(newCourseId);
                });
            });
        });
    });

    describe('CourseDuplicateController', function () {
        var $rootScope, createController, $location, $q;

        beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$q_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            $q = _$q_;
            createController = function (params, resolvedData) {
                return $controller('CourseDuplicateController', {
                    $scope: $rootScope,
                    $routeParams: params || {},
                    resolvedData: resolvedData || {}
                });
            }
        }));

        describe('view:', function () {
            var controller;
            var toaster;
            var course = {
                "available": false,
                "created": "2016-07-29T19:34:40",
                "assignment_count": 0,
                "student_assignment_count": 0,
                "student_count": 0,
                "end_date": "2017-04-28T23:00:00",
                "id": "1abcABC123-abcABC123_Z",
                "lti_linked": false,
                "groups_locked": false,
                "modified": "2016-08-18T16:44:39",
                "name": "Another course",
                "start_date": "2017-01-02T23:00:00",
                "term": "Summer",
                "year": 2016,
                "sandbox": false
            };

            var assignments = [
                {
                    "after_comparing": true,
                    "answer_count": 2,
                    "answer_end": "2017-04-09T13:59:00",
                    "answer_period": false,
                    "answer_start": "2017-03-25T14:00:00",
                    "available": false,
                    "compare_end": null,
                    "compare_period": false,
                    "compare_start": null,
                    "compared": false,
                    "course_id": "oMtDpqO7Qu-0m-wYCWRE1A",
                    "created": "2016-10-04T21:32:54",
                    "criteria": [
                        {
                            "compared": true,
                            "created": "2016-06-06T19:50:47",
                            "default": true,
                            "description": "<p>Choose the response that you think is the better of the two.</p>",
                            "id": "1abcABC123-abcABC123_Z",
                            "modified": "2016-06-06T19:50:47",
                            "name": "Which is better?",
                            "public": true,
                            "user_id": "hJYTzpyVQcCnSN3raYtxGQ"
                        }
                    ],
                    "description": "",
                    "peer_feedback_prompt": null,
                    "educators_can_compare": false,
                    "enable_self_evaluation": false,
                    "enable_group_answers": false,
                    "self_eval_start": null,
                    "self_eval_end": null,
                    "self_eval_instructions": null,
                    "evaluation_count": 0,
                    "file": null,
                    "id": "1abcABC123-abcABC123_Z",
                    "lti_course_linked": false,
                    "lti_linked": false,
                    "groups_locked": false,
                    "modified": "2016-10-04T21:32:54",
                    "name": "1234567",
                    "number_of_comparisons": 3,
                    "pairing_algorithm": "random",
                    "rank_display_limit": null,
                    "self_evaluation_count": 0,
                    "students_can_reply": false,
                    "total_comparisons_required": 4,
                    "total_steps_required": 4,
                    "user": {
                        "avatar": "831fdab66736a3de4671777adf80908c",
                        "displayname": "root",
                        "fullname": "thkx UeNV",
                        "fullname_sortable": "UeNV, thkx",
                        "student_number": null,
                        "id": "hJYTzpyVQcCnSN3raYtxGQ"
                    },
                    "user_id": "hJYTzpyVQcCnSN3raYtxGQ"
                },
                {
                    "after_comparing": true,
                    "answer_count": 2,
                    "answer_end": "2017-03-16T13:59:00",
                    "answer_period": false,
                    "answer_start": "2017-03-06T15:00:00",
                    "available": false,
                    "compare_end": "2017-03-25T13:59:00",
                    "compare_period": false,
                    "compare_start": "2017-03-17T15:00:00",
                    "compared": false,
                    "course_id": "oMtDpqO7Qu-0m-wYCWRE1A",
                    "created": "2016-10-04T21:32:54",
                    "criteria": [
                        {
                            "compared": true,
                            "created": "2016-06-06T19:50:47",
                            "default": true,
                            "description": "<p>Choose the response that you think is the better of the two.</p>",
                            "id": "1abcABC123-abcABC123_Z",
                            "modified": "2016-06-06T19:50:47",
                            "name": "Which is better?",
                            "public": true,
                            "user_id": "hJYTzpyVQcCnSN3raYtxGQ"
                        }
                    ],
                    "description": "",
                    "peer_feedback_prompt": null,
                    "self_eval_start": null,
                    "self_eval_end": null,
                    "self_eval_instructions": null,
                    "educators_can_compare": false,
                    "enable_self_evaluation": false,
                    "enable_group_answers": false,
                    "evaluation_count": 0,
                    "file": null,
                    "id": "2abcABC123-abcABC123_Z",
                    "lti_course_linked": false,
                    "lti_linked": false,
                    "groups_locked": false,
                    "modified": "2016-10-04T21:32:54",
                    "name": "1234567890",
                    "number_of_comparisons": 3,
                    "pairing_algorithm": "random",
                    "rank_display_limit": null,
                    "self_evaluation_count": 0,
                    "students_can_reply": false,
                    "total_comparisons_required": 4,
                    "total_steps_required": 4,
                    "user": {
                        "avatar": "831fdab66736a3de4671777adf80908c",
                        "displayname": "root",
                        "fullname": "thkx UeNV",
                        "fullname_sortable": "UeNV, thkx",
                        "student_number": null,
                        "id": "hJYTzpyVQcCnSN3raYtxGQ"
                    },
                    "user_id": "hJYTzpyVQcCnSN3raYtxGQ"
                }
            ];

            beforeEach(inject(function (_Toaster_) {
                toaster = _Toaster_;
                spyOn(toaster, 'warning');
            }));

            beforeEach(function () {
                $rootScope.originalCourse = course;
                controller = createController({courseId: $rootScope.originalCourse.id}, {
                    course: $rootScope.originalCourse
                });
                $httpBackend.expectGET('/api/courses/1abcABC123-abcABC123_Z/assignments').respond({
                    'objects': assignments
                });
                $httpBackend.flush();
            });

            it('should have correct initial states', function () {
                expect($rootScope.submitted).toBe(false);
                expect($rootScope.originalCourse).toEqual(course);
                expect($rootScope.format).toEqual('dd-MMMM-yyyy');
            });

            describe('duplicate existing:', function () {

                it('should set duplicate assignment answer/comparison dates', function () {
                    // course[0].start_date = "2017-01-02T23:00:00" which is a Monday
                    // removing time component for easier comparisons
                    var originalStartDate = new Date(course.start_date);

                    var now = new Date();
                    var past = new Date('2016-10-05T19:10:13.283Z');
                    var present = new Date(course.start_date)
                    var future = new Date('2018-10-05T19:10:13.283Z');

                    // check course start date automatic generation
                    var startOfWeek = new Date();
                    // -day of week+1 for converting to ISO 8601 first day of week (monday)
                    // -6 for sundays (since they are d)
                    if (startOfWeek.getDay() == 0) {
                        startOfWeek.setDate(startOfWeek.getDate() - 6);
                    } else {
                        startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay() + 1);
                    }

                    expect($rootScope.duplicateCourse.date.course_start.date.toDateString()).toEqual(startOfWeek.toDateString());

                    // course[0].end_date = "2017-04-28T23:00:00" which is +18 weeks and +4 days ahead of start date
                    var endDateDayDiff = (16 * 7) + 4;

                    // assignments[0].answer_start = "2017-03-25T14:00:00" which is +13 weeks and +5 days ahead of start date
                    var assignment0AnswerStartDayDiff = (11 * 7) + 5;
                    // assignments[0].answer_end = "2017-04-09T13:59:00" which is +15 weeks and +6 days ahead of start date
                    var assignment0AnswerEndDayDiff = (13 * 7) + 6;

                    // assignments[1].answer_start = "2017-03-06T15:00:00" which is +11 weeks and +0 days ahead of start date
                    var assignment1AnswerStartDayDiff = (9 * 7) + 0;
                    // assignments[1].answer_end = "2017-03-16T13:59:00" which is +12 weeks and +3 days ahead of start date
                    var assignment1AnswerEndDayDiff = (10 * 7) + 3;

                    // assignments[1].compare_start = "2017-03-17T15:00:00" which is +12 weeks and +4 days ahead of start date
                    var assignment1CompareStartDayDiff = (10 * 7) + 4;
                    // assignments[1].compare_end = "2017-03-25T13:59:00" which is +13 weeks and +5 days ahead of start date
                    var assignment1CompareEndDayDiff = (11 * 7) + 5;

                    // check course end date automatic generation
                    var expectedDay = new Date(startOfWeek);
                    expectedDay.setDate(startOfWeek.getDate() + endDateDayDiff);
                    expect($rootScope.duplicateCourse.date.course_end.date.toDateString()).toEqual(expectedDay.toDateString());

                    // check assignment
                    var testDates = [now, past, present, future];
                    angular.forEach(testDates, function(testDate) {
                        startOfWeek = testDate;
                        // +1 for converting to ISO 8601 first day of week (monday)
                        startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay() + 1);

                        for (var dayIndex = 0; dayIndex < 7; dayIndex++) {
                            var day = new Date(startOfWeek);
                            day.setDate(startOfWeek.getDate() + dayIndex);

                            $rootScope.duplicateCourse.date.course_start.date = day;
                            $rootScope.adjustDuplicateAssignmentDates();

                            // check assignment 0 dates
                            expectedDay = new Date(startOfWeek);
                            expectedDay.setDate(startOfWeek.getDate() + assignment0AnswerStartDayDiff);
                            expect($rootScope.duplicateAssignments[0].date.astart.date.toDateString()).toEqual(expectedDay.toDateString());

                            expectedDay = new Date(startOfWeek);
                            expectedDay.setDate(startOfWeek.getDate() + assignment0AnswerEndDayDiff);
                            expect($rootScope.duplicateAssignments[0].date.aend.date.toDateString()).toEqual(expectedDay.toDateString());

                            expect($rootScope.duplicateAssignments[0].availableCheck).toBe(undefined);
                            expect($rootScope.duplicateAssignments[0].date.cstart.date).toEqual(null);
                            expect($rootScope.duplicateAssignments[0].date.cend.date).toEqual(null);

                            // check assignment 1 dates
                            expectedDay = new Date(startOfWeek);
                            expectedDay.setDate(startOfWeek.getDate() + assignment1AnswerStartDayDiff);
                            expect($rootScope.duplicateAssignments[1].date.astart.date.toDateString()).toEqual(expectedDay.toDateString());

                            expectedDay = new Date(startOfWeek);
                            expectedDay.setDate(startOfWeek.getDate() + assignment1AnswerEndDayDiff);
                            expect($rootScope.duplicateAssignments[1].date.aend.date.toDateString()).toEqual(expectedDay.toDateString());

                            expect($rootScope.duplicateAssignments[1].availableCheck).toBe(true);

                            expectedDay = new Date(startOfWeek);
                            expectedDay.setDate(startOfWeek.getDate() + assignment1CompareStartDayDiff);
                            expect($rootScope.duplicateAssignments[1].date.cstart.date.toDateString()).toEqual(expectedDay.toDateString());

                            expectedDay = new Date(startOfWeek);
                            expectedDay.setDate(startOfWeek.getDate() + assignment1CompareEndDayDiff);
                            expect($rootScope.duplicateAssignments[1].date.cend.date.toDateString()).toEqual(expectedDay.toDateString());
                        }
                    })
                });

                it('should warn when course start date is not before end date', function () {
                    $rootScope.duplicateCourse.date.course_start.date = new Date();
                    $rootScope.duplicateCourse.date.course_start.time = new Date();
                    $rootScope.duplicateCourse.date.course_end.date = new Date();
                    $rootScope.duplicateCourse.date.course_end.time = new Date();
                    $rootScope.duplicateCourse.date.course_end.date.setDate($rootScope.duplicateCourse.date.course_end.date.getDate()-1);

                    $rootScope.duplicate();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Course Not Duplicated', 'Please set course end time after course start time and try again.');
                    expect($location.path()).toEqual('');
                });

                it('should warn when assignment answer start date is not before end date', function () {
                    $rootScope.duplicateAssignments[0].date.astart.date = new Date();
                    $rootScope.duplicateAssignments[0].date.astart.time = new Date();
                    $rootScope.duplicateAssignments[0].date.aend.date = new Date();
                    $rootScope.duplicateAssignments[0].date.aend.time = new Date();
                    $rootScope.duplicateAssignments[0].date.aend.date.setDate($rootScope.duplicateAssignments[0].date.aend.date.getDate()-1);

                    $rootScope.duplicate();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Course Not Duplicated', 'Please set answer end time for "'+$rootScope.duplicateAssignments[0].name+'" after answer start time and try again.');
                    expect($location.path()).toEqual('');
                });

                it('should warn when answer start is not before compare start', function () {
                    $rootScope.duplicateAssignments[0].availableCheck = true;
                    $rootScope.duplicateAssignments[0].date.cstart.date = angular.copy($rootScope.duplicateAssignments[0].date.astart.date);
                    $rootScope.duplicateAssignments[0].date.cstart.date.setDate($rootScope.duplicateAssignments[0].date.cstart.date.getDate()-1);

                    $rootScope.duplicate();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Course Not Duplicated', 'Please set comparison start time for "'+$rootScope.duplicateAssignments[0].name+'" after answer start time and try again.');
                    expect($location.path()).toEqual('');
                });

                it('should warn when compare start is not before compare end', function () {
                    $rootScope.duplicateAssignments[0].availableCheck = true;
                    $rootScope.duplicateAssignments[0].date.cstart.date = angular.copy($rootScope.duplicateAssignments[0].date.astart.date);
                    $rootScope.duplicateAssignments[0].date.cstart.date.setDate($rootScope.duplicateAssignments[0].date.cstart.date.getDate()+1);
                    $rootScope.duplicateAssignments[0].date.cend.date = $rootScope.duplicateAssignments[0].date.cstart.date;
                    $rootScope.duplicateAssignments[0].date.cend.time = $rootScope.duplicateAssignments[0].date.cstart.time;

                    $rootScope.duplicate();
                    expect($rootScope.submitted).toBe(false);
                    expect(toaster.warning).toHaveBeenCalledWith('Course Not Duplicated', 'Please set comparison end time for "'+$rootScope.duplicateAssignments[0].name+'" after comparison start time and try again.');
                    expect($location.path()).toEqual('');
                });

                it('should be able to save new course', function () {
                    var newCourseId = "3abcABC123-abcABC123_Z"
                    $httpBackend.expectPOST('/api/courses/1abcABC123-abcABC123_Z/duplicate', $rootScope.duplicateCourse).respond(
                        angular.merge({}, course, $rootScope.duplicateCourse, {id: newCourseId})
                    );
                    $rootScope.duplicate();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                    expect($location.path()).toEqual('/course/3abcABC123-abcABC123_Z');
                });
            });
        });
    });
});