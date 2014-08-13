describe('Service: Session', function() {
    var mockSession, $httpBackend;
    var id = 1;
    var expectedSession = {
        "id": id,
        "permissions": {
            "Courses": {
                "create": true,
                "delete": true,
                "edit": true,
                "manage": true,
                "read": true
            },
            "PostsForQuestions": {
                "create": true,
                "delete": true,
                "edit": true,
                "manage": true,
                "read": true
            },
            "Users": {
                "create": true,
                "delete": true,
                "edit": true,
                "manage": true,
                "read": true
            }
        }
    };
    var expectedUser = {
        "avatar": "63a9f0ea7bb98050796b649e85481845",
        "created": "Tue, 27 May 2014 00:02:38 -0000",
        "displayname": "root",
        "email": null,
        "firstname": "John",
        "fullname": "John Smith",
        "id": id,
        "lastname": "Smith",
        "lastonline": "Tue, 12 Aug 2014 20:53:31 -0000",
        "modified": "Tue, 12 Aug 2014 20:53:31 -0000",
        "username": "root",
        "usertypeforsystem": {
            "id": 3,
            "name": "System Administrator"
        },
        "usertypesforsystem_id": 3
    };


    beforeEach(function() {
        angular.mock.module('ubc.ctlt.acj.session');

        inject(function($injector) {
            $httpBackend = $injector.get('$httpBackend');
            mockSession = $injector.get('Session');
        });
    });

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
                $httpBackend.expectGET('/session').respond(expectedSession);
                $httpBackend.expectGET('/api/users/' + id).respond(expectedUser);

                mockSession.getUser().then(function(result) {
                    user = result;
                });
                $httpBackend.flush();
            });

            it('and return user resource', inject(function(UserResource) {
                expect(user instanceof UserResource).toBe(true);
                expect(user.id).toEqual(expectedUser.id);
            }));

            it('and set cookie', inject(function($cookieStore) {
                expect($cookieStore.get('current.user')).toEqual(expectedUser);
            }));

            it('and cache user in Session', function() {
                expect(mockSession._user.id).toEqual(expectedUser.id);
            });

            it('and return the same object on subsequent calls', function() {
                mockSession.getUser().then(function(result) {
                    expect(result).toBe(user);
                })
            });
        });

        describe('with cached user', function() {
            var user = null;

            it('should get user from local and no remote request', function() {
                mockSession._user = expectedUser;
                mockSession.getUser().then(function(result) {
                    user = result;
                    expect(user).toEqual(expectedUser);
                });
            });

            it('should get user from cookie', inject(function($cookieStore, UserResource) {
                $cookieStore.put('current.user', expectedUser);
                var t = new UserResource;
                angular.extend(t, expectedUser);
                mockSession.getUser().then(function(result) {
                    expect(result).toEqual(t);
                });
            }));
        });
    });

    describe('getPermission', function() {
        describe('should call getPermission()', function() {
            var permissions = null;

            beforeEach(function() {
                $httpBackend.expectGET('/session/permissions').respond(expectedSession.permissions);

                mockSession.getPermissions().then(function(result) {
                    permissions = result;
                });
                $httpBackend.flush();
            });

            it('and return permissions', function() {
                expect(permissions).toEqual(expectedSession.permissions);
            });

            it('and set cookie', inject(function($cookieStore) {
                expect($cookieStore.get('current.permissions')).toEqual(expectedSession.permissions);
            }));

            it('and cache permission in Session', function() {
                expect(mockSession._permissions).toEqual(expectedSession.permissions);
            });

            it('and return the same object on subsequent calls', function() {
                mockSession.getPermissions().then(function(result) {
                    expect(result).toBe(permissions);
                })
            });
        });

        describe('with cached permission', function() {
            var permissions = null;

            it('should get permissions from local and no remote request', function() {
                mockSession._permissions = expectedSession.permissions;
                mockSession.getPermissions().then(function(result) {
                    expect(result).toEqual(expectedSession.permissions);
                })
            });

            it('should get permissions from cookie', inject(function($cookieStore) {
                $cookieStore.put('current.permissions', expectedSession.permissions);
                expect(mockSession._permissions).toBe(null);
                mockSession.getPermissions().then(function(result) {
                    expect(result).toEqual(expectedSession.permissions);
                })
            }));
        })
    });
});