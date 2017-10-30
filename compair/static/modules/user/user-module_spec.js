describe('user-module', function () {
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
    beforeEach(module('ubc.ctlt.compair.user'));
    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
        sessionRequestHandler = $httpBackend.when('GET', '/api/session').respond(mockSession);
        $httpBackend.when('GET', '/api/users/' + id).respond(mockUser);
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('UserWriteController', function () {
        var $rootScope, createController, $location;

        beforeEach(inject(function ($controller, _$rootScope_, _$location_) {
            $rootScope = _$rootScope_;
            $location = _$location_;
            createController = function (params, resolvedData) {
                return $controller('UserWriteController', {
                    $scope: $rootScope,
                    $routeParams: params || {},
                    resolvedData: resolvedData || {}
                });
            }
        }));

        describe('create', function () {
            var controller;
            beforeEach(function () {
                controller = createController({}, {
                    canManageUsers: true,
                    loggedInUser: angular.copy(mockUser),
                });
            });

            it('should be correctly initialized', function () {
                expect($rootScope.password).toEqual({});
                expect($rootScope.ownProfile).toBe(false);
                expect($rootScope.canManageUsers).toBe(true);
                expect($rootScope.user).toEqual({
                    'uses_compair_login': true,
                    'system_role': 'Student',
                    'email_notification_method': 'enable'
                });
                expect($rootScope.system_roles).toEqual([
                    "Student", "Instructor", "System Administrator"
                ]);
            });

            it('should be able to save new user', function () {
                $rootScope.user = angular.copy(mockUser);
                $rootScope.user.id = undefined;
                $httpBackend.expectPOST('/api/users', $rootScope.user).respond(angular.merge({}, mockUser, {id: "2abcABC123-abcABC123_Z"}));
                $rootScope.save();
                expect($rootScope.submitted).toBe(true);
                $httpBackend.flush();
                expect($location.path()).toEqual('/user/2abcABC123-abcABC123_Z');
                expect($rootScope.submitted).toBe(false);
            })
        });

        describe('edit', function () {
            var controller;
            var editUser;

            beforeEach(function () {
                editUser = angular.merge({}, mockUser, {id: "2abcABC123-abcABC123_Z"});
                controller = createController({userId: editUser.id}, {
                    user: editUser,
                    canManageUsers: true,
                    loggedInUser: angular.copy(mockUser),
                });
            });

            it('should be correctly initialized', function () {
                expect($rootScope.password).toEqual({});
                expect($rootScope.ownProfile).toBe(false);
                expect($rootScope.canManageUsers).toBe(true);
                expect($rootScope.user).toEqualData(editUser);
            });

            it('should be able to save edited user', function () {
                var editedUser = angular.copy(editUser);
                editedUser.username = 'new name';
                $rootScope.user = editedUser;
                $httpBackend.expectPOST('/api/users/2abcABC123-abcABC123_Z', $rootScope.user).respond(editedUser);
                $rootScope.save();
                expect($rootScope.submitted).toBe(true);
                $httpBackend.flush();
                expect($location.path()).toEqual('/user/2abcABC123-abcABC123_Z');
                expect($rootScope.submitted).toBe(false);
            });

            it('should enable save button even if save failed', function() {
                $rootScope.user = angular.copy(editUser);
                $httpBackend.expectPOST('/api/users/2abcABC123-abcABC123_Z', $rootScope.user).respond(400, '');
                $rootScope.save();
                expect($rootScope.submitted).toBe(true);
                $httpBackend.flush();
                expect($rootScope.submitted).toBe(false);
            });
        });
    });

    describe('UserPasswordModalController', function () {
        var $rootScope, createController, $uibModal, $q;

        beforeEach(inject(function ($controller, _$rootScope_, _$uibModal_, _$q_) {
            $rootScope = _$rootScope_;
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
                return $controller('UserPasswordModalController', {
                    $scope: $rootScope,
                    $uibModalInstance: modalInstance,
                    $routeParams: params || {}
                });
            }
        }));

        describe('update password', function () {
            var controller;
            var toaster;
            beforeEach(inject(function (_Toaster_) {
                toaster = _Toaster_;
                spyOn(toaster, 'error');
            }));

            beforeEach(function () {
                $rootScope.user = angular.copy(mockUser);
                controller = createController();
            });

            it('should have correct initial states', function () {
                expect($rootScope.password).toEqual({});
                expect($rootScope.submitted).toBe(false);
            });

            it('should be able to change password and close modal', function() {
                var editUser = angular.copy($rootScope.user);
                $rootScope.password = {oldpassword: 'old', newpassword: 'new'};
                $httpBackend.expectPOST('/api/users/' + editUser.id + '/password', $rootScope.password).respond(editUser);
                $rootScope.changePassword();
                expect($rootScope.submitted).toBe(true);
                $httpBackend.flush();
                expect($rootScope.submitted).toBe(false);
                expect(modalInstance.close).toHaveBeenCalledWith();
            });
        });
    });

    describe('UserViewController', function () {
        var $rootScope, createController;

        beforeEach(inject(function ($controller, _$rootScope_) {
            $rootScope = _$rootScope_;
            createController = function (params, resolvedData) {
                return $controller('UserViewController', {
                    $scope: $rootScope,
                    $routeParams: params || {},
                    resolvedData: resolvedData || {},
                });
            }
        }));

        describe('view', function () {
            var controller;
            var viewUser;
            beforeEach(function () {
                viewUser = angular.merge({}, mockUser, {id: "2abcABC123-abcABC123_Z"});
                controller = createController({userId: viewUser.id}, {
                    user: viewUser,
                    userEditButton: {available: 'true'},
                    canManageUsers: true,
                    loggedInUser: angular.copy(mockUser),
                });
            });

            it('should be correctly initialized', function () {
                expect($rootScope.user).toEqualData(viewUser);
                expect($rootScope.userId).toEqualData(viewUser.id);
                expect($rootScope.canManageUsers).toBe(true);
                expect($rootScope.loggedInUserIsInstructor).toBe(false);
                expect($rootScope.ownProfile).toBe(false);
                expect($rootScope.showEditButton).toEqualData({available: 'true'});
            });

            it('should be able to toggle user email notification settings', function () {
                var editUser = angular.copy(viewUser);
                editUser.email_notification_method = 'disable';
                $rootScope.user = editUser;
                $httpBackend.expectPOST('/api/users/2abcABC123-abcABC123_Z/notification', $rootScope.user).respond(editUser);
                $rootScope.updateNotificationSettings();
                expect($rootScope.submitted).toBe(true);
                $httpBackend.flush();
                expect($rootScope.submitted).toBe(false);
                expect($rootScope.user.email_notification_method).toEqualData('disable');
            });
        });
    });
});