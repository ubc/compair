(function () {
	'use strict';

	angular
		.module('ubc.ctlt.acj.criteria')

		.directive('criteriaForm', ['CriteriaResource', 'EditorOptions', '$location', '$routeParams', 'Toaster', function (CriteriaResource, EditorOptions, $location, $routeParams, Toaster) {
			return {
				restrict: 'E',
				scope: {
					criterion: '=?'
				},
				templateUrl: 'modules/criteria/criteria-form-partial.html',
				link: function (scope, element, attrs) {
					scope.editorOptions = EditorOptions.basic;
					scope.criterionSubmitted = false;
					// grab the course id and criterion id to build the edit URL
					scope.courseId = $routeParams['courseId'];
					scope.criterionId = $routeParams['criterionId'];
					// build the edit URL
					scope.editURL = '/course/'+scope.courseId+'/criterion/'+scope.criterionId+'/edit';
					// grab the current URL
					scope.currentURL = $location.path();

					scope.criterionSubmit = function (currentURL, editURL) {
						scope.criterionSubmitted = true;
						CriteriaResource.save({}, scope.criterion, function (ret) {
							alert(scope.criterion.default);
							scope.$emit('CRITERIA_ADDED', ret);
							// action depends on if this is the edit URL or not
							if (currentURL == editURL) {
								Toaster.success("Criterion Updated", "Successfully saved your criterion changesssss.");
								$location.path('/course/'+scope.courseId +'/configure');
							} else {
								resetForm();
							}

						}).$promise.finally(function () {
							scope.criterionSubmitted = false;
						});
					};

					function resetForm() {
						// initialize default attribute to false
						scope.criterion = {'name': '', 'description': '', 'default': false};
					}

					//resetForm();
				}
			}
		}]);
})();
