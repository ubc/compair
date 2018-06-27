describe('user-module', function () {
    var $httpBackend;
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
    var mockCourseId = "2abcABC123-abcABC123_Z";
    var mockAssignmentId = "3abcABC123-abcABC123_Z";
    var mockAnswerId = "4abcABC123-abcABC123_Z";
    var mockUserId = "5abcABC123-abcABC123_Z";
    var mockConsumerId = "6abcABC123-abcABC123_Z";
    beforeEach(module('myApp'));

    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
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

    describe('Routes:', function () {
        var $rootScope, $route, $location, toaster, Session, Authorize, $q;

        beforeEach(inject(function (_$rootScope_, _$q_, _$route_, _$location_, _toaster_, _Session_, _Authorize_) {
            $rootScope = _$rootScope_;
            $q = _$q_;
            $route = _$route_;
            $location = _$location_;
            toaster = _toaster_;
            Session = _Session_;
            Authorize = _Authorize_;
            spyOn(toaster, 'error');
            spyOn(Session, 'getUser').and.returnValue($q.when(mockUser));
            spyOn(Authorize, 'can').and.returnValue($q.when(true));
        }));

        describe('"/"', function() {
            var path = '/';

            it('should load correctly', function() {
                $httpBackend.expectGET('modules/home/home-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.CREATE, "Course");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/home/home-partial.html');
                expect($route.current.controller).toBe('HomeController');
            });
        });

        describe('"/course/create"', function() {
            var path = '/course/create';

            it('should load correctly', function() {
                $httpBackend.expectGET('modules/course/course-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/course/course-partial.html');
                expect($route.current.controller).toBe('CourseController');
            });
        });

        describe('"/course/:courseId"', function() {
            var path = '/course/'+mockCourseId;

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments').respond({});
                $httpBackend.expectGET('modules/course/course-assignments-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.EDIT, "Course", mockCourseId);
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.CREATE, "Assignment", mockCourseId);
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/course/course-assignments-partial.html');
                expect($route.current.controller).toBe('CourseAssignmentsController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments').respond({});
                $httpBackend.expectGET('modules/course/course-assignments-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.EDIT, "Course", mockCourseId);
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.CREATE, "Assignment", mockCourseId);
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/course/course-assignments-partial.html');
                expect($route.current.controller).toBe('CourseAssignmentsController');
            });
        });

        describe('"/course/:courseId/edit"', function() {
            var path = '/course/'+mockCourseId+'/edit';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('modules/course/course-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/course/course-partial.html');
                expect($route.current.controller).toBe('CourseController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('modules/course/course-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/course/course-partial.html');
                expect($route.current.controller).toBe('CourseController');
            });
        });

        describe('"/course/:courseId/user"', function() {
            var path = '/course/'+mockCourseId+'/user';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/users').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/classlist/classlist-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.CREATE, "User");
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/classlist/classlist-view-partial.html');
                expect($route.current.controller).toBe('ClassViewController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/users').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/classlist/classlist-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.CREATE, "User");
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/classlist/classlist-view-partial.html');
                expect($route.current.controller).toBe('ClassViewController');
            });
        });

        describe('"/course/:courseId/user/import"', function() {
            var path = '/course/'+mockCourseId+'/user/import';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('modules/classlist/classlist-import-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/classlist/classlist-import-partial.html');
                expect($route.current.controller).toBe('ClassImportController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('modules/classlist/classlist-import-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/classlist/classlist-import-partial.html');
                expect($route.current.controller).toBe('ClassImportController');
            });
        });

        describe('"/course/:courseId/user/import/results"', function() {
            var path = '/course/'+mockCourseId+'/user/import/results';

            it('should load correctly', function() {
                $httpBackend.expectGET('modules/classlist/classlist-import-results-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/classlist/classlist-import-results-partial.html');
                expect($route.current.controller).toBe('ClassImportResultsController');
            });
        });

        describe('"/course/:courseId/assignment/create"', function() {
            var path = '/course/'+mockCourseId+'/assignment/create';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/criteria').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-form-partial.html');
                expect($route.current.controller).toBe('AssignmentWriteController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/criteria').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-form-partial.html');
                expect($route.current.controller).toBe('AssignmentWriteController');
            });
        });

        describe('"/course/:courseId/assignment/:assignmentId"', function() {
            var path = '/course/'+mockCourseId+'/assignment/'+mockAssignmentId;

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/users/students').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/users/instructors').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups/user').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-view-partial.html');
                expect($route.current.controller).toBe('AssignmentViewController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/users/students').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/users/instructors').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups/user').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-view-partial.html');
                expect($route.current.controller).toBe('AssignmentViewController');
            });
        });

        describe('"/course/:courseId/assignment/:assignmentId/edit"', function() {
            var path = '/course/'+mockCourseId+'/assignment/'+mockAssignmentId+'/edit';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/comparisons/examples').respond({});
                $httpBackend.expectGET('/api/criteria').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-form-partial.html');
                expect($route.current.controller).toBe('AssignmentWriteController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/comparisons/examples').respond({});
                $httpBackend.expectGET('/api/criteria').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-form-partial.html');
                expect($route.current.controller).toBe('AssignmentWriteController');
            });
        });

        describe('"/course/:courseId/assignment/:assignmentId/duplicate"', function() {
            var path = '/course/'+mockCourseId+'/assignment/'+mockAssignmentId+'/duplicate';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/comparisons/examples').respond({});
                $httpBackend.expectGET('/api/criteria').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.method).toBe('copy');
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-form-partial.html');
                expect($route.current.controller).toBe('AssignmentWriteController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/comparisons/examples').respond({});
                $httpBackend.expectGET('/api/criteria').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/groups').respond({});
                $httpBackend.expectGET('modules/assignment/assignment-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.method).toBe('copy');
                expect($route.current.templateUrl).toBe('modules/assignment/assignment-form-partial.html');
                expect($route.current.controller).toBe('AssignmentWriteController');
            });
        });

        describe('"/course/:courseId/assignment/:assignmentId/compare"', function() {
            var path = '/course/'+mockCourseId+'/assignment/'+mockAssignmentId+'/compare';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/timer').respond({});
                $httpBackend.expectGET('modules/comparison/comparison-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/comparison/comparison-form-partial.html');
                expect($route.current.controller).toBe('ComparisonController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/timer').respond({});
                $httpBackend.expectGET('modules/comparison/comparison-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "Assignment", mockCourseId);

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/comparison/comparison-form-partial.html');
                expect($route.current.controller).toBe('ComparisonController');
            });
        });

        describe('"/course/:courseId/assignment/:assignmentId/self_evaluation"', function() {
            var path = '/course/'+mockCourseId+'/assignment/'+mockAssignmentId+'/self_evaluation';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond(404, '');
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/status').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/answers/user').respond({});
                $httpBackend.expectGET('modules/comparison/comparison-self_evaluation-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/comparison/comparison-self_evaluation-partial.html');
                expect($route.current.controller).toBe('ComparisonSelfEvalController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/courses/'+mockCourseId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId).respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/status').respond({});
                $httpBackend.expectGET('/api/courses/'+mockCourseId+'/assignments/'+mockAssignmentId+'/answers/user').respond({});
                $httpBackend.expectGET('modules/comparison/comparison-self_evaluation-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/comparison/comparison-self_evaluation-partial.html');
                expect($route.current.controller).toBe('ComparisonSelfEvalController');
            });
        });

        describe('"/report"', function() {
            var path = '/report';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/users/courses/teaching').respond(404, '');
                $httpBackend.expectGET('modules/report/report-create-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/report/report-create-partial.html');
                expect($route.current.controller).toBe('ReportCreateController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/users/courses/teaching').respond({});
                $httpBackend.expectGET('modules/report/report-create-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/report/report-create-partial.html');
                expect($route.current.controller).toBe('ReportCreateController');
            });
        });

        describe('"/user/create"', function() {
            var path = '/user/create';

            it('should load correctly', function() {
                $httpBackend.expectGET('modules/user/user-create-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-create-partial.html');
                expect($route.current.controller).toBe('UserWriteController');
            });
        });

        describe('"/user/:userId/edit"', function() {
            var path = '/user/'+mockUserId+'/edit';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/users/'+mockUserId).respond(404, '');
                $httpBackend.expectGET('modules/user/user-edit-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-edit-partial.html');
                expect($route.current.controller).toBe('UserWriteController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/users/'+mockUserId).respond({});
                $httpBackend.expectGET('modules/user/user-edit-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-edit-partial.html');
                expect($route.current.controller).toBe('UserWriteController');
            });
        });

        describe('"/user/:userId"', function() {
            var path = '/user/'+mockUserId;

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/users/'+mockUserId).respond(404, '');
                $httpBackend.expectGET('/api/users/'+mockUserId+'/edit').respond({});
                $httpBackend.expectGET('modules/user/user-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-view-partial.html');
                expect($route.current.controller).toBe('UserViewController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/users/'+mockUserId).respond({});
                $httpBackend.expectGET('/api/users/'+mockUserId+'/edit').respond({});
                $httpBackend.expectGET('modules/user/user-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-view-partial.html');
                expect($route.current.controller).toBe('UserViewController');
            });
        });

        describe('"/users"', function() {
            var path = '/users';

            it('should load correctly', function() {
                $httpBackend.expectGET('modules/user/user-list-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-list-partial.html');
                expect($route.current.controller).toBe('UserListController');
            });
        });

        describe('"/users/:userId/manage"', function() {
            var path = '/users/'+mockUserId+'/manage';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/users/'+mockUserId).respond(404, '');
                $httpBackend.expectGET('/api/users/'+mockUserId+'/lti/users').respond({});
                $httpBackend.expectGET('/api/users/'+mockUserId+'/third_party/users').respond({});
                $httpBackend.expectGET('modules/user/user-manage-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-manage-partial.html');
                expect($route.current.controller).toBe('UserManageController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/users/'+mockUserId).respond({});
                $httpBackend.expectGET('/api/users/'+mockUserId+'/lti/users').respond({});
                $httpBackend.expectGET('/api/users/'+mockUserId+'/third_party/users').respond({});
                $httpBackend.expectGET('modules/user/user-manage-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/user/user-manage-partial.html');
                expect($route.current.controller).toBe('UserManageController');
            });
        });

        describe('"/lti"', function() {
            var path = '/lti';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/lti/status').respond(404, '');
                $httpBackend.expectGET('modules/lti/lti-setup-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti/lti-setup-partial.html');
                expect($route.current.controller).toBe('LTIController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/lti/status').respond({});
                $httpBackend.expectGET('modules/lti/lti-setup-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).not.toHaveBeenCalled();

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti/lti-setup-partial.html');
                expect($route.current.controller).toBe('LTIController');
            });
        });

        describe('"/lti/consumer"', function() {
            var path = '/lti/consumer';

            it('should load correctly', function() {
                $httpBackend.expectGET('modules/lti_consumer/lti-consumers-list-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti_consumer/lti-consumers-list-partial.html');
                expect($route.current.controller).toBe('LTIConsumerListController');
            });
        });

        describe('"/lti/consumer/create"', function() {
            var path = '/lti/consumer/create';

            it('should load correctly', function() {
                $httpBackend.expectGET('modules/lti_consumer/lti-consumer-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti_consumer/lti-consumer-form-partial.html');
                expect($route.current.controller).toBe('LTIConsumerWriteController');
            });
        });

        describe('"/lti/consumer/:consumerId"', function() {
            var path = '/lti/consumer/'+mockConsumerId;

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/lti/consumers/'+mockConsumerId).respond(404, '');
                $httpBackend.expectGET('modules/lti_consumer/lti-consumer-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti_consumer/lti-consumer-view-partial.html');
                expect($route.current.controller).toBe('LTIConsumerViewController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/lti/consumers/'+mockConsumerId).respond({});
                $httpBackend.expectGET('modules/lti_consumer/lti-consumer-view-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti_consumer/lti-consumer-view-partial.html');
                expect($route.current.controller).toBe('LTIConsumerViewController');
            });
        });

        describe('"/lti/consumer/:consumerId/edit"', function() {
            var path = '/lti/consumer/'+mockConsumerId+'/edit';

            it('should handle pre-loading errors', function() {
                $httpBackend.expectGET('/api/lti/consumers/'+mockConsumerId).respond(404, '');
                $httpBackend.expectGET('modules/lti_consumer/lti-consumer-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);

                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).not.toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti_consumer/lti-consumer-form-partial.html');
                expect($route.current.controller).toBe('LTIConsumerWriteController');
            });

            it('should load correctly', function() {
                $httpBackend.expectGET('/api/lti/consumers/'+mockConsumerId).respond({});
                $httpBackend.expectGET('modules/lti_consumer/lti-consumer-form-partial.html').respond('');

                expect($route.current).toBeUndefined();
                $location.path(path);
                expect($route.current).toBeUndefined();
                $httpBackend.flush();

                expect(Session.getUser).not.toHaveBeenCalled();
                expect(Authorize.can).toHaveBeenCalledWith(Authorize.MANAGE, "User");

                expect(toaster.error).not.toHaveBeenCalled();
                expect($rootScope.routeResolveLoadError).toBeUndefined();
                expect($route.current.templateUrl).toBe('modules/lti_consumer/lti-consumer-form-partial.html');
                expect($route.current.controller).toBe('LTIConsumerWriteController');
            });
        });
    });
});