describe('Service: Session', function() {
    var sessionService, $httpBackend, localStorageService;
    var id = "1abcABC123-abcABC123_Z";
    var expectedUser = {
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
    var expectedSession = {
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

    beforeEach(module('ubc.ctlt.compair.session'));

    beforeEach(inject(function($injector) {
        $httpBackend = $injector.get('$httpBackend');
        localStorageService = $injector.get('localStorageService');
        sessionService = $injector.get('Session');
    }));

    // make sure no expectations were missed in your tests.
    // (e.g. expectGET or expectPOST)
    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('getUser', function() {
        describe('should call getUser()', function() {
            var user = null;

            beforeEach(function() {
                sessionService.destroy();
                $httpBackend.expectGET('/api/session').respond(expectedSession);
                $httpBackend.expectGET('/api/users/' + id).respond(expectedUser);

                sessionService.getUser().then(function(result) {
                    user = result;
                });
                $httpBackend.flush();
            });

            afterEach(function() {
                sessionService.destroy();
            });

            it('and return user resource', inject(function(UserResource) {
                expect(user instanceof UserResource).toBe(true);
                expect(user.id).toEqual(expectedUser.id);
            }));

            it('and set local storage', inject(function(localStorageService) {
                expect(localStorageService.get('user')).toEqual(expectedUser);
            }));

            it('and cache user in Session', function() {
                expect(sessionService._user.id).toEqual(expectedUser.id);
            });

            it('and return the same object on subsequent calls', function() {
                sessionService.getUser().then(function(result) {
                    expect(result).toBe(user);
                })
            });
        });

        describe('with cached user', function() {
            var user = null;

            it('should get user from local and no remote request', function() {
                sessionService._user = expectedUser;
                sessionService.getUser().then(function(result) {
                    user = result;
                    expect(user).toEqual(expectedUser);
                });
            });

            it('should get user from local storage', inject(function(localStorageService, UserResource) {
                localStorageService.set('user', expectedUser);
                var t = new UserResource;
                angular.extend(t, expectedUser);
                sessionService.getUser().then(function(result) {
                    expect(result).toEqual(t);
                });
            }));
        });
    });

    describe('getPermission', function() {
        describe('should call getPermission()', function() {
            var permissions = null;

            beforeEach(function() {
                sessionService.destroy();
                $httpBackend.expectGET('/api/session/permission').respond(expectedSession.permissions);

                sessionService.getPermissions().then(function(result) {
                    permissions = result;
                });
                $httpBackend.flush();
            });

            afterEach(function() {
                sessionService.destroy();
            });

            it('and return permissions', function() {
                expect(permissions).toEqual(expectedSession.permissions);
            });

            it('and set local storage', inject(function(localStorageService) {
                expect(localStorageService.get('permissions')).toEqual(expectedSession.permissions);
            }));

            it('and cache permission in Session', function() {
                expect(sessionService._permissions).toEqual(expectedSession.permissions);
            });

            it('and return the same object on subsequent calls', function() {
                sessionService.getPermissions().then(function(result) {
                    expect(result).toBe(permissions);
                })
            });
        });

        describe('with cached permission', function() {
            var permissions = null;

            it('should get permissions from local and no remote request', function() {
                sessionService._permissions = expectedSession.permissions;
                sessionService.getPermissions().then(function(result) {
                    expect(result).toEqual(expectedSession.permissions);
                })
            });

            it('should get permissions from local storage', inject(function(localStorageService) {
                localStorageService.set('permissions', expectedSession.permissions);
                expect(sessionService._permissions).toBe(null);
                sessionService.getPermissions().then(function(result) {
                    expect(result).toEqual(expectedSession.permissions);
                })
            }));
        })
    });
});