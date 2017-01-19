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

module.controller('LTIConsumerController',
    ['$scope', '$location', '$route', '$routeParams', 'UserResource', 'LTIConsumerResource',
     'Toaster', 'breadcrumbs', 'Session', 'Authorize', 'xAPIStatementHelper',
    function($scope, $location, $route, $routeParams, UserResource, LTIConsumerResource,
             Toaster, breadcrumbs, Session, Authorize, xAPIStatementHelper) {

        $scope.totalNumConsumers = 0;
        $scope.consumerFilters = {
            page: 1,
            perPage: 20,
            orderBy: null,
            reverse: null
        };

        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;

            if ($scope.canManageUsers) {
                $scope.updateConsumerList();
                // register watcher here so that we start watching when all filter values are set
                $scope.$watchCollection('consumerFilters', filterWatcher);
            } else {
                $location.path('/');
            }
        });

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
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve LTI consumers.", ret);
                }
            );
        };

        $scope.updateConsumer = function(consumer) {
            LTIConsumerResource.save(consumer).$promise.then(
                function (ret) {
                    if (ret.active) {
                         Toaster.success("LTI Consumer Activated!");
                    } else {
                         Toaster.success("LTI Consumer Deactivated!");
                    }
                    $scope.updateConsumerList();
                },
                function (ret) {
                    if (ret.active) {
                         Toaster.reqerror("LTI Consumer Activation Failed!");
                    } else {
                         Toaster.reqerror("LTI Consumer Deactivation Failed!");
                    }
                }
            );
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.orderBy != newValue.orderBy) {
                $scope.consumerFilters.page = 1;
            }
            xAPIStatementHelper.filtered_page($scope.consumerFilters);
            $scope.updateConsumerList();
        };
    }]
);


module.controller("LTIConsumerWriteController",
    ['$scope', '$location', '$route', '$routeParams', 'UserResource', 'LTIConsumerResource',
     'Toaster', 'breadcrumbs', 'Session', 'Authorize', 'xAPIStatementHelper',
    function($scope, $location, $route, $routeParams, UserResource, LTIConsumerResource,
             Toaster, breadcrumbs, Session, Authorize, xAPIStatementHelper)
    {
        $scope.consumerId = $routeParams['consumerId'];
        $scope.consumer = {};
        $scope.submitted = false;

        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;

            if ($scope.canManageUsers) {
                if ($route.current.method == "new") {
                    // nothing
                } else if ($route.current.method == "edit") {
                    LTIConsumerResource.get({'id': $scope.consumerId}).$promise.then(
                        function (ret) {
                            $scope.consumer = ret;
                        },
                        function (ret) {
                            Toaster.reqerror("Unable to retrieve consumer "+$scope.consumerId, ret);
                        }
                    );
                }
            } else {
                $location.path('/');
            }
        });

        $scope.save = function () {
            $scope.submitted = true;

            LTIConsumerResource.save($scope.consumer).$promise.then(
                function (ret) {
                    $scope.submitted = false;

                    if ($route.current.method == "new") {
                         Toaster.success("LTI Consumer Created!");
                    } else if ($route.current.method == "edit") {
                         Toaster.success("LTI Consumer Updated!");
                    }
                    $location.path('/lti/consumer');
                },
                function (ret) {
                    $scope.submitted = false;
                    if ($route.current.method == "new") {
                         Toaster.reqerror("LTI Consumer Create Failed!");
                    } else if ($route.current.method == "edit") {
                         Toaster.reqerror("LTI Consumer Update Failed!");
                    }
                }
            );
        };
    }
]);

// End anonymous function
})();