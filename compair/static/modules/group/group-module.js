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
        'ubc.ctlt.compair.oauth',
        'ui.bootstrap'
    ]
);

/***** Providers *****/
module.factory(
    "GroupResource",
    ["$resource", "Interceptors",
    function ($resource, Interceptors)
    {
        var url = '/api/courses/:courseId/groups/:groupName';
        var unenrolUrl = '/api/courses/:courseId/users/:userId/groups';
        var ret = $resource(url, {groupName: '@groupName'},
            {
                get: {cache: true, url: url},
                getAllFromSession: {url: url, interceptor: Interceptors.groupSessionInterceptor},
                updateUsersGroup: {method: 'POST', url: '/api/courses/:courseId/users/groups/:groupName', interceptor: Interceptors.enrolCache},
                removeUsersGroup: {method: 'POST', url: '/api/courses/:courseId/users/groups', interceptor: Interceptors.enrolCache},
                enrol: {method: 'POST', url: unenrolUrl+'/:groupName', interceptor: Interceptors.enrolCache},
                unenrol: {method: 'DELETE', url: unenrolUrl, interceptor: Interceptors.enrolCache}
            }
        );

        ret.MODEL = 'Group';
        return ret;
    }
]);

/***** Controllers *****/
module.controller(
    'AddGroupModalController',
    ["$rootScope", "$scope", "$uibModalInstance",
    function ($rootScope, $scope, $uibModalInstance) {
        $scope.group = {};
        $scope.modalInstance = $uibModalInstance;

        $scope.groupSubmit = function () {
            $uibModalInstance.close($scope.group.name);
        };
    }
]);

})();