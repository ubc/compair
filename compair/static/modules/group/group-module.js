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
    'GroupImportController',
    ["$scope", "$log", "$location", "$routeParams", "CourseResource", "Toaster",
     "importService", "ThirdPartyAuthType", "AuthTypesEnabled",
    function($scope, $log, $location, $routeParams, CourseResource, Toaster,
             importService, ThirdPartyAuthType, AuthTypesEnabled)
    {
        $scope.course = {};
        var courseId = $routeParams['courseId'];
        CourseResource.get({'id': courseId}).$promise.then(
            function (ret) {
                $scope.course_name = ret['name'];
            },
            function (ret) {
                Toaster.reqerror("No Course Found For ID "+courseId, ret);
            }
        );

        $scope.userIdentifiers = [];

        if (AuthTypesEnabled.cas) {
            $scope.userIdentifiers.push({'key': ThirdPartyAuthType.cas, 'label': 'CWL Username'});
        }
        if (AuthTypesEnabled.app) {
            $scope.userIdentifiers.push({'key': 'username', 'label': 'ComPAIR Username'});
        }
        $scope.userIdentifiers.push({'key': 'student_number', 'label': 'Student Number'});

        $scope.userIdentifier = $scope.userIdentifiers[0].key;

        $scope.uploader = importService.getUploader(courseId, 'groups');

        $scope.uploader.onBeforeUploadItem = function(item) {
            item.formData.push({'userIdentifier': $scope.userIdentifier});
        };

        $scope.uploader.onCompleteItem = function(fileItem, response, status, headers) {
            $scope.submitted = false;
            importService.onComplete(courseId, response);
        };
        $scope.uploader.onErrorItem = importService.onError();
        $scope.upload = function() {
            $scope.submitted = true;
            $scope.uploader.uploadAll();
        };
    }
]);

module.controller(
    'GroupImportResultsController',
    ["$scope", "$log", "$location", "$routeParams", "CourseResource", "Toaster", "importService",
    function($scope, $log, $location, $routeParams, CourseResource, Toaster, importService)
    {
        $scope.invalids = importService.getResults().invalids;

        $scope.courseId = $routeParams['courseId'];

        // TODO: change "Row" to something more meaningful
        $scope.headers = ['Row', 'Message'];
    }
]);

module.controller(
    'AddGroupModalController',
    ["$rootScope", "$scope", "$uibModalInstance",
    function ($rootScope, $scope, $uibModalInstance) {
        $scope.group = {};

        $scope.cancel = function (ret) {
            $uibModalInstance.dismiss();
        }

        $scope.groupSubmit = function () {
            $uibModalInstance.close($scope.group.name);
        };
    }
]);

})();