// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.group',
    [
        'ngResource',
        'ubc.ctlt.compair.attachment',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.login',
        'ubc.ctlt.compair.toaster',
        'ui.bootstrap'
    ]
);

/***** Providers *****/
module.factory(
    "GroupResource",
    ["$resource", "Interceptors",
    function ($resource, Interceptors)
    {
        var url = '/api/courses/:courseId/groups/:groupId';
        var ret = $resource(url, {groupId: '@id'},
            {
                get: {url: url, cache: true, interceptor: Interceptors.enrolCache},
                save: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
                delete: {method: 'DELETE', url: url, interceptor: Interceptors.enrolCache},
            }
        );

        ret.MODEL = 'Group';
        return ret;
    }
]);

module.factory(
    "GroupUserResource",
    ["$resource", "Interceptors",
    function ($resource, Interceptors)
    {
        var url = '/api/courses/:courseId/groups/:groupId/users/:userId';
        var removeUrl = '/api/courses/:courseId/groups/users/:userId';
        var getUrl = '/api/courses/:courseId/groups/user';
        var ret = $resource(url, {groupId: '@groupId'},
            {
                getCurrentUserGroup: {url: getUrl, cache: true, interceptor: Interceptors.enrolCache},
                add: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
                remove: {method: 'DELETE', url: removeUrl, interceptor: Interceptors.enrolCache},
                addUsersToGroup: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
                removeUsersFromGroup: {method: 'POST', url: removeUrl, interceptor: Interceptors.enrolCache},
            }
        );

        ret.MODEL = 'Group';
        return ret;
    }
]);

/***** Controllers *****/
module.controller(
    'AddGroupModalController',
    ["$rootScope", "$scope", "$uibModalInstance", "$filter", "Toaster", "GroupResource",
    function ($rootScope, $scope, $uibModalInstance, $filter, Toaster, GroupResource) {
        $scope.group = {};
        $scope.modalInstance = $uibModalInstance;
        $scope.submitted = false;

        $scope.groupSubmit = function () {
            $scope.submitted = true;

            var groupNameExists = $filter('filter')($scope.groups, {'name':$scope.group.name}, true).length > 0;

            if (groupNameExists) {
                Toaster.warning("Group Not Added", "The group name you have entered already exists. Please enter another group name and press Save.");
                $scope.submitted = false;
            }
            else {
                GroupResource.save({'courseId': $scope.courseId}, $scope.group).$promise.then(
                    function (ret) {
                        $scope.group = ret;
                        $uibModalInstance.close($scope.group.id);
                    }
                ).finally(function() {
                    $scope.submitted = false;
                });
            }
        }
    }
]);

})();