// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.lti.context', [
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
module.factory('LTIContextLinkResource',
["$resource", "Interceptors",
function($resource, Interceptors)
{
    var url = '/api/lti/course/:course_id/context/:context_id';
    var ret = $resource(url, {course_id: '@course_id', context_id: '@context_id'},
        {
            'get': { method: 'GET'},
            'linkCourse': { method: 'POST', interceptor: Interceptors.contextCacheLTI },
            'unlinkCourse': { method: 'DELETE', interceptor: Interceptors.contextCacheLTI }
        }
    );
    ret.MODEL = "LTIContext";
    return ret;
}]);

module.controller('LTIContextListController',
    ['$scope', 'LTIContextLinkResource', 'Toaster', 'LearningRecordStatementHelper',
    function($scope, LTIContextLinkResource, Toaster, LearningRecordStatementHelper)
    {
        $scope.course = null;

        $scope.totalNumContexts = 0;
        $scope.contextFilters = {
            page: 1,
            perPage: 20,
            orderBy: null,
            reverse: null,
            search: null
        };

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            $scope.contextFilters.orderBy = $scope.predicate;
            $scope.contextFilters.reverse = $scope.reverse ? true : null;
        };

        $scope.updateContextList = function() {
            var params = angular.copy($scope.contextFilters);

            LTIContextLinkResource.get(params).$promise.then(
                function(ret) {
                    $scope.contexts = ret.objects;
                    $scope.totalNumContexts = ret.total;
                }
            );
        };
        $scope.updateContextList();

        $scope.unlinkContext = function(context) {
            LTIContextLinkResource.unlinkCourse({course_id: context.compair_course_id, context_id: context.id}).$promise.then(
                function (ret) {
                    Toaster.success("Course Unlink", "Successfully unlinked the ComPAIR course as requested from the external source.");
                    $scope.updateContextList();
                }
            );
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.orderBy != newValue.orderBy) {
                $scope.contextFilters.page = 1;
            }
            if (oldValue.search != newValue.search) {
                $scope.contextFilters.page = 1;
            }
            if(newValue.search === "") {
                $scope.contextFilters.search = null;
            }
            LearningRecordStatementHelper.filtered_page($scope.contextFilters);
            $scope.updateContextList();
        };
        $scope.$watchCollection('contextFilters', filterWatcher);
    }
]);

// End anonymous function
})();