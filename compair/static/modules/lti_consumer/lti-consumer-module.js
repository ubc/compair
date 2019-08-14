// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.lti.consumer', [
    'ngResource',
    'ngRoute',
    'ng-breadcrumbs',
    'ui.bootstrap',
    'LocalStorageModule',
    'ubc.ctlt.compair.authentication',
    'ubc.ctlt.compair.authorization',
    'ubc.ctlt.compair.toaster',
    'ubc.ctlt.compair.user',
    'ubc.ctlt.compair.course',
    'ubc.ctlt.compair.lti'
]);

/***** Providers *****/
module.factory('LTIConsumerResource',
    ["$resource",
    function($resource)
{
    var ret = $resource('/api/lti/consumers/:id', {id: '@id'});
    ret.MODEL = "LTIConsumer";
    return ret;
}]);

module.controller('LTIConsumerListController',
    ['$scope', '$location', '$route', '$routeParams', 'UserResource', 'LTIConsumerResource',
     'Toaster', 'breadcrumbs', 'LearningRecordStatementHelper', 'resolvedData',
    function($scope, $location, $route, $routeParams, UserResource, LTIConsumerResource,
             Toaster, breadcrumbs, LearningRecordStatementHelper, resolvedData)
    {
        $scope.canManageUsers = resolvedData.canManageUsers;

        $scope.totalNumConsumers = 0;
        $scope.consumerFilters = {
            page: 1,
            perPage: 20,
            orderBy: null,
            reverse: null
        };

        if (!$scope.canManageUsers) {
            $location.path('/');
        }

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            $scope.consumerFilters.orderBy = $scope.predicate;
            $scope.consumerFilters.reverse = $scope.reverse ? true : null;
        };

        $scope.updateConsumerList = function() {
            LTIConsumerResource.get($scope.consumerFilters).$promise.then(
                function(ret) {
                    $scope.consumers = ret.objects;
                    $scope.totalNumConsumers = ret.total;
                }
            );
        };
        $scope.updateConsumerList();

        $scope.updateConsumer = function(consumer) {
            LTIConsumerResource.save(consumer).$promise.then(
                function (ret) {
                    if (ret.active) {
                         Toaster.success("LTI Consumer Activated");
                    } else {
                         Toaster.success("LTI Consumer Deactivated");
                    }
                    $scope.updateConsumerList();
                }
            );
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.orderBy != newValue.orderBy) {
                $scope.consumerFilters.page = 1;
            }
            LearningRecordStatementHelper.filtered_page($scope.consumerFilters);
            $scope.updateConsumerList();
        };
        $scope.$watchCollection('consumerFilters', filterWatcher);
    }]
);

module.controller("LTIConsumerViewController",
    ['$scope', '$location', '$route', '$routeParams', 'UserResource', 'LTIConsumerResource',
     'Toaster', 'breadcrumbs', 'LearningRecordStatementHelper', 'resolvedData',
    function($scope, $location, $route, $routeParams, UserResource, LTIConsumerResource,
             Toaster, breadcrumbs, LearningRecordStatementHelper, resolvedData)
    {
        $scope.consumerId = $routeParams.consumerId;
        $scope.launchUrl = $location.absUrl().replace("app/#"+$location.url(), "") + 'api/lti/auth';

        $scope.consumer = resolvedData.consumer || {};
        $scope.canManageUsers = resolvedData.canManageUsers;

        if (!$scope.canManageUsers) {
            $location.path('/');
        }

        $scope.updateConsumerActive = function() {
            LTIConsumerResource.save($scope.consumer).$promise.then(
                function (ret) {
                    $scope.consumer = ret;
                    if (ret.active) {
                         Toaster.success("LTI Consumer Activated");
                    } else {
                         Toaster.success("LTI Consumer Deactivated");
                    }
                }
            );
        };
    }
]);

module.controller("LTIConsumerWriteController",
    ['$scope', '$location', '$route', '$routeParams', 'UserResource', 'LTIConsumerResource',
     'Toaster', 'breadcrumbs', 'LearningRecordStatementHelper', 'resolvedData',
    function($scope, $location, $route, $routeParams, UserResource, LTIConsumerResource,
             Toaster, breadcrumbs, LearningRecordStatementHelper, resolvedData)
    {
        $scope.consumerId = $routeParams.consumerId;

        $scope.consumer = resolvedData.consumer || {};
        $scope.canManageUsers = resolvedData.canManageUsers;

        $scope.method = $scope.consumer.id ? "edit" : "create";
        $scope.submitted = false;
        
        if ($scope.method == "create") {
            $scope.consumer.active = true;
        }

        if (!$scope.canManageUsers) {
            $location.path('/');
        }
        
        // decide on showing inline errors for LTI consumer add/edit form
        $scope.showErrors = function($event, formValid) {

            // show error if invalid form
            if (!formValid) {
                
                // don't submit
                $event.preventDefault();
                
                // set helper text and Toast
                $scope.helperMsg = "Sorry, this consumer couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this consumer couldn't be saved yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";
                
                // display messages
                $scope.saveAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);
            }
            
        };
        
        $scope.save = function () {
            $scope.submitted = true;

            LTIConsumerResource.save($scope.consumer).$promise.then(
                function (ret) {
                    if ($scope.method == "create") {
                         Toaster.success("LTI Consumer Created");
                    } else if ($scope.method == "edit") {
                         Toaster.success("LTI Consumer Updated");
                    }
                    $location.path('/lti/consumer');
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }
]);

// End anonymous function
})();