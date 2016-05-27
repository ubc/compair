describe('Testing a controller', function() {

//    var ctrl, scope, httpMock;
//    beforeEach(module('myApp'));
//    beforeEach(inject(function($controller, $rootScope, $httpBackend, $http) {
//    	$rootScope.$digest();
//    	httpMock = $httpBackend;
//
//        scope = $rootScope.$new();
//        httpMock.when('GET', '/tactical/api/listOrderForms').respond("an order form");
//        ctrl = $controller;
//        ctrl(QuestionController, {
//            $scope: scope,
//            $http: $http
//        });
//    }));
//
//    it("gets the list from the api and assigns it to scope", function() {
//    	httpMock.expectGET('tactical/api/listOrderForms');
//		httpMock.flush();
//		expect(scope.orderFormList).toMatch("an order form");
//    });
});
/*
describe('ACJ', function() {

	describe('Question', function() {

		var scope, ctrl, $httpBackend;
		beforeEach(module('myApp'));

		beforeEach(inject(function($controller, $rootScope, _$httpBackend_, $http) {

			lstQuestion = {
				"id" : 1,
				"author" : "testauthor",
				"time" : "",
				"title" : "testquestion",
				"content" : "",
				"avatar" : "",
				"count" : 1,
				"answered" : false,
				"tags" : [ {} ]
			};
			lstQuiz = {
				"id" : 2,
				"author" : "testauthor",
				"time" : "",
				"title" : "testquiz",
				"content" : "",
				"avatar" : "",
				"count" : 2,
				"tags" : [ {} ]
			};

			$httpBackend = _$httpBackend_;
			$httpBackend.when('GET', '/question/1').respond({
				"course" : "testcourse",
				"tags" : [ {} ],
				"questions" : lstQuestion,
				"quizzes" : lstQuiz
			});

			scope = $rootScope.$new();
			ctrl = $controller;
			ctrl(QuestionController, {
				$scope : scope,
				$http: $http
			});

		}));

		afterEach(function() {
			$httpBackend.verifyNoOutstandingExpectation();
			$httpBackend.verifyNoOutstandingRequest();
		});

		it('1', function() {
			$httpBackend.expectGET('/question/1');
			$httpBackend.flush();
			//expect(scope.discussions.length).toBe(1);
			//expect(scope.quizzes.length).toBe(1);
		});
	});
});
*/