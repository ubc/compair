// When a user makes a judgement between 2 answers, they can decide which answer
// is the better choice according to multiple criteria.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.criteria', 
	[
		'ngResource'
	]
);

/***** Providers *****/
module.factory('CoursesCriteriaResource', function($resource) {
	ret = $resource('/api/courses/:courseId/criteria/:criteriaId', {criteriaId: '@id'});
	ret.MODEL = "CriteriaAndCourses";
	return ret;
});

module.factory('QuestionsCriteriaResource', function($resource) {
	ret = $resource('/api/courses/:courseId/questions/:questionId/criteria/:criteriaId', {criteriaId: '@id'});
	ret.MODEL = "CriteriaAndPostsForQuestions";
	return ret;
});

module.factory('CriteriaResource', function($resource) {
	return $resource('/api/criteria/:criteriaId', {criteriaId: '@id'},
		 {
			 'getDefault': {'url': '/api/criteria/default', cache: true}
		 }
	);
});

/***** Controllers *****/
module.controller(
	'CriterionConfigureController',
	function($scope, $log, $routeParams, $location, CriteriaResource, CoursesCriteriaResource, EditorOptions, Toaster)
	{
		$scope.editorOptions = EditorOptions.basic;
		$scope.criterion = {};
		var courseId = $routeParams['courseId'];
		var criterionId = $routeParams['criterionId'];
		CriteriaResource.get({'criteriaId': criterionId}).$promise.then(
			function (ret) {
				$scope.criterion = ret.criterion;
			},
			function (ret) {
				Toaster.reqerror("Criterion Not Found", ret);
			}
		);
		// update criterion
		$scope.criterionSubmit = function() {
			$scope.criterionSubmitted = true;
			CriteriaResource.save({'criteriaId': criterionId}, $scope.criterion).$promise.then(
				function (ret) {
					$scope.criterionSubmitted = false;
					Toaster.success("Criterion Updated", "Successfully saved your criterion changes.");
					$location.path('/course/' + courseId + '/configure');
				},
				function (ret) {
					$scope.criterionSubmitted = false;
					Toaster.reqerror("Criterion Update Failed", ret);
				}
			);
		};
	}
);

// End anonymous function
})();
