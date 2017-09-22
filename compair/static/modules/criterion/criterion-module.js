// When a user makes a comparison between 2 answers, they can decide which answer
// is the better choice according to multiple criteria.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.criterion', [
    'ngResource',
    'ui.bootstrap',
    'ubc.ctlt.compair.common.form',
    'ubc.ctlt.compair.rich.content',
    'ubc.ctlt.compair.toaster'
]);

module.factory('CriterionResource', ['$resource', function($resource) {
    return $resource('/api/criteria/:criterionId', {criterionId: '@id'});
}]);

/***** Controllers *****/
module.controller(
    "CriterionModalController",
    ['$scope', 'CriterionResource', 'Toaster', 'EditorOptions', "$uibModalInstance",
    function ($scope, CriterionResource, Toaster, EditorOptions, $uibModalInstance)
    {
        $scope.criterion = $scope.criterion || {};
        $scope.method = $scope.criterion.id ? 'edit' : 'create';
        $scope.modalInstance = $uibModalInstance;
        $scope.editorOptions = EditorOptions.basic;
        $scope.submitted = false;

        if ($scope.method == 'edit') {
            $scope.criterion = CriterionResource.get({'criterionId': $scope.criterion.id});
        }
        $scope.criterionSubmit = function () {
            $scope.submitted = true;

            // never edit a public criterion. Create a new copy of it instead
            var criterion = angular.copy($scope.criterion);
            if (criterion.public) {
                criterion.id = null;
                criterion.public = false;
            }
            CriterionResource.save({}, criterion).$promise.then(
                function (ret) {
                    $scope.criterion = ret;

                    Toaster.success("Criterion Saved");

                    $uibModalInstance.close($scope.criterion);
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }]
);

// End anonymous function
})();
