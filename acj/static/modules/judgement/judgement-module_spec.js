describe('judgement-module', function () {
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
	beforeEach(module('ubc.ctlt.acj.judgement'));
	beforeEach(inject(function ($injector) {
		$httpBackend = $injector.get('$httpBackend');
		sessionRequestHandler = $httpBackend.when('GET', '/api/session').respond(mockSession);
		$httpBackend.when('GET', '/api/users/' + id).respond(mockUser);
	}));

	afterEach(function () {
		$httpBackend.verifyNoOutstandingExpectation();
		$httpBackend.verifyNoOutstandingRequest();
	});

	describe('JudgementController', function () {
		var $rootScope, createController, $location, $modal, $q;
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
		var mockQuestion = {
			"question": {
				"after_judging": false,
				"answer_end": "Mon, 14 Sep 2015 04:00:00 -0000",
				"answer_period": false,
				"answer_start": "Mon, 23 Feb 2015 21:50:00 -0000",
				"answers_count": 115,
				"available": true,
				"can_reply": false,
				"comments_count": 1,
				"criteria": [{
					"active": true,
					"criterion": {
						"created": "Fri, 09 Jan 2015 22:47:02 -0000",
						"default": true,
						"description": "criterionn 1",
						"id": 4,
						"judged": true,
						"modified": "Fri, 09 Jan 2015 22:47:02 -0000",
						"name": "Which answer has the better critical idea?",
						"users_id": 50
					},
					"id": 12
				}, {
					"active": true,
					"criterion": {
						"created": "Fri, 09 Jan 2015 22:50:06 -0000",
						"default": true,
						"description": "criterion 2",
						"id": 5,
						"judged": true,
						"modified": "Fri, 09 Jan 2015 22:50:06 -0000",
						"name": "Which answer is more effectively articulated? Explain the reason for your preference.",
						"users_id": 50
					},
					"id": 13
				}],
				"evaluation_count": 252,
				"id": 9,
				"judge_end": "Thu, 15 Sep 2016 16:00:00 -0000",
				"judge_start": "Tue, 15 Sep 2015 04:00:00 -0000",
				"judged": true,
				"judging_period": true,
				"modified": "Fri, 25 Sep 2015 07:40:19 -0000",
				"num_judgement_req": 3,
				"post": {
					"content": "<p><strong>For your answer, write ONLY the premise of 20-60 words. Do not include your notes. Consider spending 10-15 minutes making the notes, but not much longer for this exercise. I strongly recommend marking up a hard copy, as we do in class: paste the poem into a word document and print yourself a working copy.</strong></p>\n\n<p>Transplanted<br />\n&nbsp;&nbsp;&nbsp; ---by Lorna Crozier<br />\n<br />\nThis heart met the air. Grew in the hours<br />\nbetween the first body and the next<br />\na taste for things outside it: the heat<br />\nof high intensity, wind grieving<br />\nin the poplar leaves, the smell of steam<br />\nwafting through the open window<br />\nfrom the hot dog vendor&#39;s cart. Often it skips<br />\n<br />\na beat - grouse explode from ditches,<br />\na man flies through the windshield,<br />\na face the heart once knew<br />\nweeps in the corridor that gives nothing back<br />\nbut unloveliness and glare.<br />\n<br />\nLike a shovel that hits the earth, then rises,<br />\nand hits the earth again, it feels its own<br />\ndull blows. Some nights it is a sail billowing<br />\nwith blood, a raw fist punching.<br />\nSome nights, beneath the weight of blankets,<br />\nflesh and bones, the heart remembers. Feels those<br />\nsurgical gloves close around it, and goes cold.</p>\n",
					"created": "Wed, 18 Feb 2015 20:33:14 -0000",
					"files": [],
					"id": 2081,
					"modified": "Wed, 18 Feb 2015 20:44:41 -0000",
					"user": {
						"avatar": "b893bcb68fbeef6738437fa1deca0a28",
						"created": "Wed, 07 Jan 2015 18:06:09 -0000",
						"displayname": "Tiffany Potter",
						"id": 50,
						"lastonline": "Sun, 13 Sep 2015 07:32:04 -0000"
					}
				},
				"selfevaltype_id": 1,
				"title": "Read the poem below, and make notes on syntax, figurative language, patterns of diction and imagery, and form. Then, imagining that you are writing a 1200-word essay, write a critical premise of 20-60 words as we have discussed in class."
			}
		};

		var mockPair = {
			"answers": [{
				"comments_count": 3,
				"content": "This is answer 1",
				"created": "Sat, 29 Aug 2015 08:00:19 -0000",
				"files": [],
				"flagged": false,
				"id": 407,
				"posts_id": 4076,
				"private_comments_count": 3,
				"public_comments_count": 0,
				"questions_id": 9,
				"scores": [
					{
						"answers_id": 407,
						"criteriaandquestions_id": 12,
						"id": 645,
						"normalized_score": 75,
						"rounds": 6,
						"score": 2.19318,
						"wins": 3
					},
					{
						"answers_id": 407,
						"criteriaandquestions_id": 13,
						"id": 646,
						"normalized_score": 0,
						"rounds": 6,
						"score": 0.0,
						"wins": 0
					}
				],
				"user_avatar": "63a9f0ea7bb98050796b649e85481845",
				"user_displayname": "root",
				"user_id": 1
			}, {
				"comments_count": 4,
				"content": "This is answer 2",
				"created": "Tue, 24 Feb 2015 04:09:28 -0000",
				"files": [],
				"flagged": false,
				"id": 279,
				"posts_id": 2177,
				"private_comments_count": 4,
				"public_comments_count": 0,
				"questions_id": 9,
				"scores": [
					{
						"answers_id": 279,
						"criteriaandquestions_id": 12,
						"id": 445,
						"normalized_score": 75,
						"rounds": 8,
						"score": 2.19318,
						"wins": 3
					},
					{
						"answers_id": 279,
						"criteriaandquestions_id": 13,
						"id": 446,
						"normalized_score": 40,
						"rounds": 8,
						"score": 1.46212,
						"wins": 2
					}
				],
				"user_avatar": "25242646dab1876796ab95f036a8fc82",
				"user_displayname": "student_95322345",
				"user_id": 162
			}],
			"id": 1479
		};

		var mockComments = [{
			"answer_id": 279,
			"content": "<p>test123213t4453123123</p>\n",
			"course_id": 3,
			"created": "Thu, 24 Sep 2015 00:22:34 -0000",
			"evaluation": true,
			"id": 3703,
			"selfeval": false,
			"type": 0,
			"user_avatar": "63a9f0ea7bb98050796b649e85481845",
			"user_displayname": "root",
			"user_id": 1
		}];

		beforeEach(inject(function ($controller, _$rootScope_, _$location_, _$modal_, _$q_) {
			$rootScope = _$rootScope_;
			$location = _$location_;
			$modal = _$modal_;
			$q = _$q_;
			createController = function (route, params) {
				return $controller('JudgementController', {
					$scope: $rootScope,
					$route: route || {},
					$routeParams: params || {}
				});
			}
		}));

		it('should have correct initial states', function () {
			$httpBackend.expectGET('/api/courses/3/questions/9').respond(mockQuestion);
			$httpBackend.expectGET('/api/courses/3/questions/9/judgements/pair').respond(mockPair);
			$httpBackend.expectGET('/api/courses/3/questions/9/judgements/users/1/count').respond({"count": 0.0});
			$httpBackend.expectGET('/api/courses/3/questions/9/answer_comments?answer_ids=279,407&user_ids=1').respond(mockComments);
			createController({}, {courseId:3, questionId:9});
			expect($rootScope.question).toEqual({});
			expect($rootScope.current).toBe(undefined);
			$httpBackend.flush();

			expect($rootScope.question).toEqualData(mockQuestion.question);
			var pair = angular.copy(mockPair);
			pair.answers[0].comment = {};
			pair.answers[1].comment = mockComments[0];
			expect($rootScope.answerPair).toEqualData(pair);
			expect($rootScope.current).toEqual(1);
		});

		describe('actions:', function() {
			var $mockRoute, controller;
			var mockJudgementResponse = {
				"objects": [
					{
						"answerpairing": {
							"answers_id1": 407,
							"answers_id2": 279,
							"id": 1479,
							"questions_id": 9
						},
						"answers_id_winner": 407,
						"id": 1592,
						"question_criterion": {
							"active": true,
							"criterion": {
								"created": "Fri, 09 Jan 2015 22:47:02 -0000",
								"default": true,
								"description": "criteria 1",
								"id": 4,
								"judged": true,
								"modified": "Fri, 09 Jan 2015 22:47:02 -0000",
								"name": "Which answer has the better critical idea?",
								"users_id": 50
							},
							"id": 12
						},
						"users_id": 201
					},
					{
						"answerpairing": {
							"answers_id1": 407,
							"answers_id2": 279,
							"id": 1479,
							"questions_id": 9
						},
						"answers_id_winner": 279,
						"id": 1593,
						"question_criterion": {
							"active": true,
							"criterion": {
								"created": "Fri, 09 Jan 2015 22:50:06 -0000",
								"default": true,
								"description": "criteria 2",
								"id": 5,
								"judged": true,
								"modified": "Fri, 09 Jan 2015 22:50:06 -0000",
								"name": "Which answer is more effectively articulated? Explain the reason for your preference.",
								"users_id": 50
							},
							"id": 13
						},
						"users_id": 201
					}
				]
			};

			beforeEach(function() {
				$httpBackend.whenGET('/api/courses/3/questions/9').respond(mockQuestion);
				$httpBackend.whenGET('/api/courses/3/questions/9/judgements/pair').respond(mockPair);
				$httpBackend.whenGET('/api/courses/3/questions/9/judgements/users/1/count').respond({"count": 0.0});
				$httpBackend.whenGET('/api/courses/3/questions/9/answer_comments?answer_ids=279,407&user_ids=1').respond(mockComments);
				$mockRoute = jasmine.createSpyObj('route', ['reload']);
				controller = createController($mockRoute, {courseId:3, questionId:9});
				$httpBackend.flush();
			});

			it('should load the comment saved before when the same answer is shown', function() {
				expect($rootScope.answerPair.answers[1].comment).toEqualData(mockComments[0]);
			});

			it('should submit judgement when judgementSubmit is called', function() {
				var expectedJudgement = {
					"answerpair_id": 1479,
					"judgements": [
						{"question_criterion_id": 12, "answer_id_winner":407},
						{"question_criterion_id": 13, "answer_id_winner":279}
					]
				};
				// save answer feedback/comments
				var expectedAnswerComment1 = {"content":"Feedback 1","evaluation":true};
				var expectedAnswerComment2 = angular.extend({}, mockComments[0], {"content":"Feedback 2","evaluation":true});
				$rootScope.answerPair.answers[0].comment.content = 'Feedback 1';
				$rootScope.answerPair.answers[1].comment.content = 'Feedback 2';
				// save judgement selection and comments
				$rootScope.question.criteria[0].winner = mockPair.answers[0].id;
				$rootScope.question.criteria[0].comment = 'criteria comment 1';
				$rootScope.question.criteria[1].winner = mockPair.answers[1].id;
				$rootScope.question.criteria[1].comment = 'criteria comment 2';
				var expectedJudgementComments = {judgements: mockJudgementResponse.objects};
				expectedJudgementComments.judgements[0].comment = 'criteria comment 1';
				expectedJudgementComments.judgements[1].comment = 'criteria comment 2';
				$httpBackend.expectPOST('/api/courses/3/questions/9/judgements', expectedJudgement).respond(mockJudgementResponse);
				$httpBackend.expectPOST('/api/courses/3/questions/9/answers/407/comments', expectedAnswerComment1).respond({});
				$httpBackend.expectPOST('/api/courses/3/questions/9/answers/279/comments/3703', expectedAnswerComment2).respond({});
				$httpBackend.expectPOST('/api/courses/3/questions/9/judgements/comments', expectedJudgementComments).respond({});
				$httpBackend.expectGET('/api/courses/3/questions/9/judgements/users/1/count').respond({"count": 1.0});

				expect($rootScope.preventExit).toBe(true);

				$rootScope.judgementSubmit();
				$httpBackend.flush();

				expect($mockRoute.reload).toHaveBeenCalled();
				expect($rootScope.preventExit).toBe(false);
			})

		});
	});
});