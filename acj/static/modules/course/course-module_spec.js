describe('course-module', function () {
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
	var mockCourse = {
		"available": true,
		"created": "Fri, 09 Jan 2015 17:23:59 -0000",
		"description": null,
		"enable_student_create_questions": false,
		"enable_student_create_tags": false,
		"id": 1,
		"modified": "Fri, 09 Jan 2015 17:23:59 -0000",
		"name": "Test Course"
	};
	beforeEach(module('ubc.ctlt.acj.course'));
	beforeEach(inject(function ($injector) {
		$httpBackend = $injector.get('$httpBackend');
		sessionRequestHandler = $httpBackend.when('GET', '/api/session').respond(mockSession);
		$httpBackend.when('GET', '/api/users/' + id).respond(mockUser);
	}));

	afterEach(function () {
		$httpBackend.verifyNoOutstandingExpectation();
		$httpBackend.verifyNoOutstandingRequest();
	});

	describe('CourseController', function () {
		var $rootScope, createController, $location;
		var mockCritiera = {
			"criteria": [{
				"created": "Sat, 06 Sep 2014 02:13:07 -0000",
				"default": true,
				"description": "<p>Choose the response that you think is the better of the two.</p>",
				"id": 1,
				"judged": true,
				"modified": "Sat, 06 Sep 2014 02:13:07 -0000",
				"name": "Which is better?",
				"users_id": 1
			}, {
				"created": "Fri, 09 Jan 2015 18:35:58 -0000",
				"default": false,
				"description": "<p>Explaining what a better idea was</p>\n",
				"id": 2,
				"judged": false,
				"modified": "Fri, 09 Jan 2015 18:35:58 -0000",
				"name": "Which answer has the better idea?",
				"users_id": 46
			}]
		};

		beforeEach(inject(function ($controller, _$rootScope_, _$location_) {
			$rootScope = _$rootScope_;
			$location = _$location_;
			createController = function (route, params) {
				return $controller('CourseController', {
					$scope: $rootScope,
					$routeParams: params || {},
					$route: route || {}
				});
			}
		}));

		it('should have correct initial states', function () {
			$httpBackend.expectGET('/api/criteria').respond(mockCritiera);
			var controller = createController();
			expect($rootScope.course).toEqual({criteria: []});
			expect($rootScope.availableCriteria).toEqual([]);
			$httpBackend.flush();

			expect($rootScope.loggedInUserId).toBe(mockUser.id);
			expect($rootScope.canManageCriteriaCourses).toBe(true);
		});

		describe('view: ', function () {
			var controller;
			beforeEach(function () {
				$httpBackend.whenGET('/api/criteria').respond(mockCritiera);
			});
			describe('new', function () {
				beforeEach(function () {
					controller = createController({current: {method: 'new'}});
				});

				it('should be correctly initialized', function () {
					$httpBackend.flush();
				});

				it('should be able to save new user', function () {
					var course = {
						"name": "Test111", "descriptionCheck": true, "description": "<p>Description</p>\n",
						"criteria": [{"id": 1}]
					};
					$rootScope.course = angular.copy(course);
					$rootScope.course.id = undefined;
					$httpBackend.expectPOST('/api/courses', $rootScope.course).respond(angular.merge({}, course, {id: 2}));
					$httpBackend.expectGET('/api/session/permission').respond(mockSession['permissions']);
					$rootScope.save();
					expect($rootScope.submitted).toBe(true);
					$httpBackend.flush();
					expect($location.path()).toEqual('/course/2');
					expect($rootScope.submitted).toBe(false);
				})
			});

			describe('edit', function () {
				var editCourse;
				var courseCriteria = {
					"objects": [
						{
							"active": true,
							"course_id": 1,
							"created": "Sat, 06 Sep 2014 02:13:07 -0000",
							"default": true,
							"description": "<p>Choose the response that you think is the better of the two.</p>",
							"id": 1,
							"in_question": false,
							"judged": true,
							"modified": "Sat, 06 Sep 2014 02:13:07 -0000",
							"name": "Which is better?",
							"users_id": 1
						}
					]
				};

				beforeEach(function () {
					editCourse = angular.copy(mockCourse);
					editCourse.id = 2;
					controller = createController({current: {method: 'edit'}}, {courseId: 2});
					$httpBackend.expectGET('/api/courses/2').respond(editCourse);
					$httpBackend.expectGET('/api/courses/2/criteria').respond(courseCriteria);
					$httpBackend.flush();
				});

				it('should be correctly initialized', function () {
					expect($rootScope.course).toEqualData(_.merge(editCourse, {criteria: courseCriteria.objects}));
					expect($rootScope.availableCriteria).toEqualData([mockCritiera.criteria[1]]);
				});

				it('should be able to save edited course', function () {
					var editedCourse = angular.copy(editCourse);
					editedCourse.name = 'new name';
					$rootScope.course = editedCourse;
					$httpBackend.expectPOST('/api/courses/2', $rootScope.course).respond(editedCourse);
					$httpBackend.expectGET('/api/session/permission').respond(mockSession['permissions']);
					$rootScope.save();
					expect($rootScope.submitted).toBe(true);
					$httpBackend.flush();
					expect($location.path()).toEqual('/course/2');
					expect($rootScope.submitted).toBe(false);
				});

				it('should be able to remove course criteria', function() {
					$rootScope.availableCriteria = [{id: 1}, {id: 2}];
					$rootScope.course.criteria = [{id: 1}, {id:3}];
					controller.removeCourseCriteria();
					expect($rootScope.availableCriteria).toEqual([{id: 2}]);
				});

				it('should listen to CRITERIA_ADDED event', function() {
					$rootScope.course.criteria = [];
					var criteria = {id: 1};
					$rootScope.$broadcast("CRITERIA_ADDED", criteria);
					expect($rootScope.course.criteria).toEqual([criteria]);
					expect(controller.showForm).toBe(false);
				});

				it('should add criteria to course from available criteria when add is called', function() {
					$rootScope.course.criteria = [];
					$rootScope.availableCriteria = [{id: 1}, {id: 2}];
					$rootScope.add(0);
					expect($rootScope.course.criteria).toEqual([{id: 1}]);
					expect($rootScope.availableCriteria).toEqual([{id: 2}]);
				});

				it('should remove criteria from course criteria when remove is called', function() {
					$rootScope.course.criteria = [{id: 1, default: true}, {id: 2, default: false}];
					$rootScope.availableCriteria = [];
					$rootScope.remove(0);
					// add to available list when default == true
					expect($rootScope.course.criteria).toEqual([{id: 2, default: false}]);
					expect($rootScope.availableCriteria).toEqual([{id: 1, default: true}]);

					$rootScope.remove(0);
					// don't add to available list when default == false
					expect($rootScope.course.criteria).toEqual([]);
					expect($rootScope.availableCriteria).toEqual([{id: 1, default: true}]);
				});

				it('should enable save button even if save failed', function() {
					$rootScope.course = angular.copy(editCourse);
					$httpBackend.expectPOST('/api/courses/2', $rootScope.course).respond(400, '');
					$rootScope.save();
					expect($rootScope.submitted).toBe(true);
					$httpBackend.flush();
					expect($rootScope.submitted).toBe(false);
				});
			});
		});
	});
});