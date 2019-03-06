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

    var mockDefaultCriterion = {
        "compared": true,
        "created": "Mon, 06 Jun 2016 19:50:47 -0000",
        "default": true,
        "public": true,
        "description": "<p>Choose the response that you think is the better of the two.</p>",
        "id": "1abcABC123-abcABC123_Z",
        "modified": "Mon, 06 Jun 2016 19:50:47 -0000",
        "name": "Which is better?",
        "user_id": "1abcABC123-abcABC123_Z"
    }

    var mockCriterion = {
        "compared": true,
        "created": "Mon, 06 Jun 2016 19:52:10 -0000",
        "default": true,
        "public": false,
        "description": "<p>This is a test criteria</p>\n",
        "id": "2abcABC123-abcABC123_Z",
        "modified": "Mon, 06 Jun 2016 19:52:10 -0000",
        "name": "Test Criteria",
        "user_id": "1abcABC123-abcABC123_Z"
    };
    beforeEach(module('ubc.ctlt.compair.criterion'));
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

    describe('CriterionModalController', function () {
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
                return $controller('CriterionModalController', {
                    $scope: $rootScope,
                    $uibModalInstance: modalInstance,
                    $routeParams: params || {}
                });
            }
        }));

        describe('create:', function () {
            var controller;
            var toaster;
            beforeEach(inject(function (_Toaster_) {
                toaster = _Toaster_;
                spyOn(toaster, 'error');
            }));

            beforeEach(function () {
                controller = createController();
            });

            it('should have correct initial states', function () {
                expect($rootScope.submitted).toBe(false);
                expect($rootScope.method).toEqual("create");
            });

            describe('save:', function () {
                it('should close dialog when save successful', function() {
                    $rootScope.criterion = angular.copy(mockCriterion);
                    $rootScope.criterion.id = undefined;

                    $httpBackend.expectPOST('/api/criteria', $rootScope.criterion).respond(angular.merge({}, mockCriterion, {id: "2abcABC123-abcABC123_Z"}));
                    $rootScope.criterionSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                    expect(modalInstance.close).toHaveBeenCalledWith($rootScope.criterion);
                });
            });
        });

        describe('edit:', function () {
            var controller;
            var toaster;
            beforeEach(inject(function (_Toaster_) {
                toaster = _Toaster_;
                spyOn(toaster, 'error');
            }));

            beforeEach(function () {
                $rootScope.criterion = angular.copy(mockCriterion);
                controller = createController();
                $httpBackend.expectGET('/api/criteria/2abcABC123-abcABC123_Z').respond(mockCriterion);
                $httpBackend.flush();
            });

            it('should have correct initial states', function () {
                expect($rootScope.submitted).toBe(false);
                expect($rootScope.method).toEqual("edit");
            });

            describe('save:', function () {
                it('should close dialog when save successful', function() {
                    $rootScope.criterion = angular.copy(mockCriterion);
                    $rootScope.criterion.name = 'new name';
                    $rootScope.criterion.description = 'new description';

                    $httpBackend.expectPOST('/api/criteria/2abcABC123-abcABC123_Z', $rootScope.criterion).respond($rootScope.criterion);
                    $rootScope.criterionSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                    expect(modalInstance.close).toHaveBeenCalledWith($rootScope.criterion);
                });

                it('should create new criterion when editing a public criterion dialog when save successful', function() {
                    $rootScope.criterion = angular.copy(mockCriterion);
                    $rootScope.criterion.name = 'new name';
                    $rootScope.criterion.description = 'new description';
                    $rootScope.criterion.public = true;

                    var expectedCriterion = angular.merge({}, $rootScope.criterion, {id: null, public: false});
                    var responseCriterion = angular.merge({}, $rootScope.criterion, {id: "2abcABC123-abcABC123_Z", public: false});
                    $httpBackend.expectPOST('/api/criteria', expectedCriterion).respond(responseCriterion);
                    $rootScope.criterionSubmit();
                    expect($rootScope.submitted).toBe(true);
                    $httpBackend.flush();
                    expect($rootScope.submitted).toBe(false);
                    expect(modalInstance.close).toHaveBeenCalledWith($rootScope.criterion);
                });
            });
        });
    });
});