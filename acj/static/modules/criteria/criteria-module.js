// When a user makes a judgement between 2 answers, they can decide which answer
// is the better choice according to multiple criteria.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.criteria', [
	'ngResource',
	'ubc.ctlt.acj.common.form'
]);

/***** Providers *****/
module.factory('CoursesCriteriaResource', ['$resource', function($resource) {
	var ret = $resource('/api/courses/:courseId/criteria/:criteriaId', {criteriaId: '@id'});
	ret.MODEL = "CriteriaAndCourses";
	return ret;
}]);

module.factory('QuestionsCriteriaResource', ['$resource', function($resource) {
	var ret = $resource('/api/courses/:courseId/questions/:questionId/criteria/:criteriaId', {criteriaId: '@id'});
	ret.MODEL = "CriteriaAndPostsForQuestions";
	return ret;
}]);

module.factory('CriteriaResource', ['$resource', function($resource) {
	return $resource('/api/criteria/:criteriaId', {criteriaId: '@id'});
}]);

/***** Controllers *****/
module.controller('CriterionConfigureController',
	['$scope', '$routeParams', '$location', 'CriteriaResource', 'Toaster',
	function($scope, $routeParams, $location, CriteriaResource, Toaster) {
		$scope.criterion = {};
		var courseId = $routeParams['courseId'];
		var criterionId = $routeParams['criterionId'];
		CriteriaResource.get({'criteriaId': criterionId}, function (ret) {
			$scope.criterion = ret.criterion;
		});
		// update criterion
		$scope.$on('CRITIERA_ADDED', function() {
			Toaster.success("Criterion Updated", "Successfully saved your criterion changes.");
			$location.path('/course/' + courseId + '/configure');
		});
	}]
);

// End anonymous function
})();
