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
        $scope.saveModalAttempted = false;
        
        if ($scope.method == 'create') {
            // by default, check criterion to be included in default criteria list
            $scope.criterion.default = true;
        } 

        if ($scope.method == 'edit') {
            $scope.criterion = CriterionResource.get({'criterionId': $scope.criterion.id});
        }
        
        // decide on showing inline errors
        $scope.showErrors = function($event, formValid) {

            // show error if invalid form
            if (!formValid) {
                
                // don't submit
                $event.preventDefault();
                
                // set helper text and Toast
                $scope.helperMsg = "Sorry, this criterion couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this criterion couldn't be saved yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";
                
                // display messages
                $scope.saveModalAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);
            
            } else {
                
                // go ahead and submit
                $scope.criterionSubmit();
           
            }
            
        };//closes showErrors
        
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
