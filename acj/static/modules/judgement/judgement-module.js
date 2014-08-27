// Controls how judgements are entered for a question's answers.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.judgement', 
	[
		'ubc.ctlt.acj.answer',
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.mathjax'
	]
);

/***** Providers *****/
module.factory('JudgementResource',
	function($resource) {
		var resourceUrl = 
			'/api/courses/:courseId/questions/:questionId/judgements';
		var ret = $resource(
			resourceUrl,
			{},
			{
				'getAnswerPair': {url: resourceUrl + '/pair'}
			}
		);
		return ret;
});


/***** Constants *****/
module.constant('required_rounds', 6);

/***** Controllers *****/
module.controller(
	'JudgementController', 
	function($log, $location, $scope, $timeout, $routeParams, $anchorScroll, QuestionResource, AnswerResource,
		CriteriaResource, JudgementResource, Toaster) 
	{
		var courseId = $scope.courseId = $routeParams['courseId'];
		var questionId = $scope.questionId = $routeParams['questionId'];
		
		$scope.question = {};
		QuestionResource.get({'courseId': courseId, 'questionId': questionId}).$promise.then(
			function (ret)
			{
				$scope.question = ret.question;
			},
			function (ret)
			{
				Toaster.reqerror("Unable to load question.", ret);
			}
		);
		
		// get all the criterias we're using for this course
		$scope.courseCriteria = {};
		CriteriaResource.get({'courseId': courseId}).$promise.then(
			function (ret)
			{
				$scope.courseCriteria = ret.objects
			},
			function (ret)
			{
				Toaster.reqerror("Unable to load criteria.", ret);
			}
		);
		// get an answerpair to be judged from the server
		$scope.answerPair = {};
		$scope.answerPairError = false;
		JudgementResource.getAnswerPair(
			{'courseId': courseId, 'questionId': questionId}).$promise.then(
				function (ret)
				{
					$scope.answerPair = ret;
					$scope.answerPair.list = [];
					$scope.answerPair.list.push(ret['answer1']);
					$scope.answerPair.list.push(ret['answer2']);
				},
				function (ret)
				{
					$scope.answerPairError = true;
					Toaster.reqerror("Unable to retrieve an answer pair.", ret);
				}
		);
		
		// enable scrolling to evaluation step 2, when step 2 revealed
		$scope.showNext = function(selector) {
			// ensure hidden step revealed first
			$timeout(function(){
				// jump to revealed step
				window.scrollTo(0, $(selector)[0].offsetTop - 80);
			}, 0);
		};
		
		// save judgement to server
		$scope.judgementSubmit = function() {
			var judgement = {};
			judgement['answer1_id'] = $scope.answerPair.answer1.id;
			judgement['answer2_id'] = $scope.answerPair.answer2.id;
			judgement['judgements'] = [];
			angular.forEach($scope.courseCriteria, 
				function(courseCriterion, index) {
					var criterionWinner = {
						'course_criterion_id': courseCriterion.id,
						'answer_id_winner': courseCriterion.winner
					};
					judgement['judgements'].push(criterionWinner);
				}
			);
			JudgementResource.save(
				{'courseId': courseId, 'questionId': questionId}, judgement).
				$promise.then(
					function() {
						Toaster.success("Judgement Submitted Successfully!");
						$location.path('/course/' + courseId);
					},
					function(ret) {
						Toaster.reqerror("Judgement Submit Failed.", ret);
					}
			);
			
		};

		// flag answer for instructor
		$scope.toggleAnswerFlag = function(answer) {
			var params = {'flagged': !answer['flagged']};
			var resultMsg = 
				"Answer has been flagged as inappropriate or incomplete.";
			if (answer['flagged']) {
				resultMsg = "Answer has been unflagged.";
			}
			AnswerResource.flagged({'courseId':courseId,'questionId':questionId, 
				'answerId': answer['id']}, params).$promise.then(
				function() {
					answer.flagged = params['flagged'];
					Toaster.success(resultMsg);
				},
				function(ret) {
					Toaster.reqerror("Unable to change answer flag.", ret);
				}
			);

		};
	}
);

// End anonymous function
})();
