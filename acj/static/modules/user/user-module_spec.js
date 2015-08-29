var customMatchers = {
	toEqualData: function (util, customEqualityTesters) {
		return {
			compare: function (actual, expected) {
				return {pass: angular.equals(actual, expected)};
			}
		}
	}
};
describe('user-module', function () {
	var $httpBackend, sessionRequestHandler;
	var id = 1;
	var mockSession = {
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
	var mockUser = {
		avatar: "63a9f0ea7bb98050796b649e85481845",
		created: "Tue, 27 May 2014 00:02:38 -0000",
		displayname: "root",
		email: null,
		firstname: "John",
		fullname: "John Smith",
		id: id,
		lastname: "Smith",
		lastonline: "Tue, 12 Aug 2014 20:53:31 -0000",
		modified: "Tue, 12 Aug 2014 20:53:31 -0000",
		username: "root",
		usertypeforsystem: {
			id: 3,
			name: "System Administrator"
		},
		usertypesforsystem_id: 3
	};
	beforeEach(module('ubc.ctlt.acj.user'));
	beforeEach(function () {
		jasmine.addMatchers(customMatchers);
	});
	beforeEach(inject(function ($injector) {
		$httpBackend = $injector.get('$httpBackend');
		sessionRequestHandler = $httpBackend.when('GET', '/api/session').respond(mockSession);
		$httpBackend.when('GET', '/api/users/' + id).respond(mockUser);
	}));

	afterEach(function () {
		$httpBackend.verifyNoOutstandingExpectation();
		$httpBackend.verifyNoOutstandingRequest();
	});

	describe('UserController', function () {
		var $rootScope, createController, $location;
		var mockTypes = [{id: 1, name: 'Admin'}, {id: 2, name: 'Instructor'}, {id: 3, name: 'Student'}];

		beforeEach(inject(function ($controller, _$rootScope_, _$location_) {
			$rootScope = _$rootScope_;
			$location = _$location_;
			createController = function (route, params) {
				return $controller('UserController', {
					$scope: $rootScope,
					$routeParams: params || {},
					$route: route || {}
				});
			}
		}));

		it('should have correct initial states', function () {
			$httpBackend.expectGET('/api/usertypes').respond(mockTypes);
			var controller = createController();
			expect($rootScope.user).toEqual({});
			expect($rootScope.method).toEqual('new');
			expect($rootScope.password).toEqual({});
			$httpBackend.flush();

			expect($rootScope.ownProfile).toBe(false);
			expect($rootScope.canManageUsers).toBe(true);
		});

		describe('view: ', function () {
			var controller;
			beforeEach(function () {
				$httpBackend.whenGET('/api/usertypes').respond(mockTypes);
			});
			describe('new', function () {
				beforeEach(function () {
					controller = createController({current: {method: 'new'}}, {userId: 2});
				});

				it('should be correctly initialized', function () {
					$httpBackend.flush();
				});

				it('should be able to save new user', function () {
					$rootScope.user = angular.copy(mockUser);
					$rootScope.user.id = undefined;
					$httpBackend.expectPOST('/api/users', $rootScope.user).respond(angular.merge(mockUser, {id: 2}));
					$rootScope.save();
					expect($rootScope.submitted).toBe(true);
					$httpBackend.flush();
					expect($location.path()).toEqual('/user/2');
					expect($rootScope.submitted).toBe(false);
				})
			});

			describe('edit', function () {
				var editUser;

				beforeEach(function () {
					editUser = angular.copy(mockUser);
					editUser.id = 2;
					controller = createController({current: {method: 'edit'}}, {userId: 2});
					$httpBackend.expectGET('/api/users/2').respond(editUser);
					$httpBackend.flush();
				});

				it('should be correctly initialized', function () {
					expect($rootScope.user).toEqualData(editUser);
				});

				it('should be able to save edited user', function () {
					var editedUser = angular.copy(editUser);
					editedUser.username = 'new name';
					$rootScope.user = editedUser;
					$httpBackend.expectPOST('/api/users/2', $rootScope.user).respond(editedUser);
					$rootScope.save();
					expect($rootScope.submitted).toBe(true);
					$httpBackend.flush();
					expect($location.path()).toEqual('/user/2');
					expect($rootScope.submitted).toBe(false);
				});

				it('should be able to change password', function () {
					$rootScope.password = {oldpassword: 'old', newpassword: 'new'};
					$httpBackend.expectPOST('/api/users/' + editUser.id + '/password', $rootScope.password).respond(editUser);
					$rootScope.changePassword();
					expect($rootScope.submitted).toBe(true);
					$httpBackend.flush();
					expect($location.path()).toEqual('/user/' + editUser.id);
					expect($rootScope.submitted).toBe(false);
				});

				it('should enable save button even if save failed', function() {
					$rootScope.user = angular.copy(editUser);
					$httpBackend.expectPOST('/api/users/2', $rootScope.user).respond(400, '');
					$rootScope.save();
					expect($rootScope.submitted).toBe(true);
					$httpBackend.flush();
					expect($rootScope.submitted).toBe(false);
				});
			});

			describe('view', function () {
				var viewUser;
				beforeEach(function () {
					viewUser = angular.copy(mockUser);
					viewUser.id = 2;
					controller = createController({current: {method: 'view'}}, {userId: 2});
					$httpBackend.expectGET('/api/users/2').respond(viewUser);
					$httpBackend.expectGET('/api/users/2/edit').respond({available: 'true'});
					$httpBackend.flush();
				});

				it('should be correctly initialized', function () {
					expect($rootScope.user).toEqualData(viewUser);
					expect($rootScope.canCreateUser).toBe(true);
					expect($rootScope.showEditButton).toEqualData({available: 'true'});
				})
			});
		});
	});
});