(function () {
    'use strict';

    angular
        .module('ubc.ctlt.compair.criterion')

        .directive('criterionForm', ['CriterionResource', function (CriterionResource) {
            return {
                restrict: 'E',
                scope: {
                    criterion: '=?',
                    editorOptions: '=?'
                },
                templateUrl: 'modules/criterion/criterion-form-partial.html',
                link: function (scope, element, attrs) {
                    scope.criterionSubmitted = false;
                    scope.cancel = function (ret) {
                        scope.$emit('CRITERION_CANCEL', ret);
                    }

                    scope.criterionSubmit = function () {
                        scope.criterionSubmitted = true;
                        CriterionResource.save({}, scope.criterion, function (ret) {
                            if (scope.criterion.id) {
                                scope.$emit('CRITERION_UPDATED', ret);
                            } else {
                                scope.$emit('CRITERION_ADDED', ret);
                            }
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
