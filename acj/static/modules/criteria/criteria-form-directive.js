(function () {
	'use strict';

	angular
		.module('ubc.ctlt.acj.criteria')

		.directive('criteriaForm', ['CriteriaResource', 'EditorOptions', function (CriteriaResource, EditorOptions) {
			return {
				restrict: 'E',
				scope: {
					criterion: '=?'
				},
				templateUrl: 'modules/criteria/criteria-form-partial.html',
				link: function (scope, element, attrs) {
					scope.editorOptions = EditorOptions.basic;
					scope.criterionSubmitted = false;

					scope.criterionSubmit = function () {
						scope.criterionSubmitted = true;
						CriteriaResource.save({}, scope.criterion, function (ret) {
							scope.$emit('CRITERIA_ADDED', ret);
							resetForm();
						}).$promise.finally(function () {
							scope.criterionSubmitted = false;
						});
					};

					function resetForm() {
						// initialize default attribute to false
						scope.criterion = {'name': '', 'description': '', 'default': false};
					}

					if (!scope.criterion) {
						resetForm();
					}
				}
			}
		}]);
})();
