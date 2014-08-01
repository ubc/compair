// Controls how judgements are entered for a question's answers.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.judgement', 
	[
		'ubc.ctlt.acj.criteria',
		'ubc.ctlt.acj.toaster'
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

/***** Controllers *****/
module.controller(
	'JudgementController', 
	function($log, $location, $scope, $routeParams, CriteriaResource,
		JudgementResource, Toaster) 
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
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
		$log.debug("here");
		$scope.answerPairError = false;
		JudgementResource.getAnswerPair(
			{'courseId': courseId, 'questionId': questionId}).$promise.then(
				function (ret)
				{
					$scope.answerPair = ret;
				},
				function (ret)
				{
					$scope.answerPairError = true;
					Toaster.reqerror("Unable to retrieve an answer pair.", ret);
				}
		);
		// save judgement to server
		$scope.judgementSubmit = function() {
			var judgement = {};
			judgement['answer1_id'] = $scope.answerPair.answer1.id;
			judgement['answer2_id'] = $scope.answerPair.answer2.id;
			judgement['judgements'] = [];
			angular.forEach($scope.courseCriteria, 
				function(courseCriterion, index) {
					$log.debug(courseCriterion);
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
	}
);

// End anonymous function
})();
