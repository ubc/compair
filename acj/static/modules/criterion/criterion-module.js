// When a user makes a comparison between 2 answers, they can decide which answer
// is the better choice according to multiple criteria.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.criterion', [
	'ngResource',
	'ubc.ctlt.acj.common.form',
    'ubc.ctlt.acj.common.mathjax',
    'ubc.ctlt.acj.common.highlightjs',
]);

module.factory('AssignmentCriterionResource', ['$resource', function($resource) {
	var ret = $resource('/api/courses/:courseId/assignments/:assignmentId/criteria/:criterionId', {criterionId: '@id'});
	ret.MODEL = "AssignmentCriterion";
	return ret;
}]);

module.factory('CriterionResource', ['$resource', function($resource) {
	return $resource('/api/criteria/:criterionId', {criterionId: '@id'});
}]);

/***** Controllers *****/
module.controller('CriterionConfigureController',
	['$scope', '$routeParams', '$location', 'CriterionResource', 'Toaster', 'EditorOptions',
	function($scope, $routeParams, $location, CriterionResource, Toaster, EditorOptions) {
		var criterionId = $routeParams['criterionId'];
        $scope.editorOptions = EditorOptions.basic;
		$scope.criterion = CriterionResource.get({'criterionId': criterionId});

		// update criterion
		$scope.$on('CRITERION_ADDED', function() {
			var courseId = $routeParams['courseId'];
			var assignmentId = $routeParams['assignmentId'];
			Toaster.success("Criterion Updated", "Successfully saved your criterion changes.");
			$location.path('/course/' + courseId + '/assignment/' + assignmentId + '/edit');
		});
	}]
);

// End anonymous function
})();
