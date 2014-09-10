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

module.factory('CriteriaResource', function($resource) {
	return $resource('/api/criteria/:criteriaId', {criteriaId: '@id'});
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
				Toaster.reqerror("Unable to retrieve the criterion.", ret);
			}
		);
		// update criterion
		$scope.criterionSubmit = function() {
			$scope.criterionSubmitted = true;
			CriteriaResource.save({'criteriaId': criterionId}, $scope.criterion).$promise.then(
				function (ret) {
					//$scope.criterion = {'name': '', 'description': ''}; // reset form
					$scope.criterionSubmitted = false;
					Toaster.success("Successfully updated the criterion.");
					$location.path('/course/' + courseId + '/configure');
				},
				function (ret) {
					$scope.criterionSubmitted = false;
					Toaster.reqerror("Unable to update the criterion.", ret);
				}
			);
		};
	}
);

// End anonymous function
})();
