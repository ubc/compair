// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.lti', [
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
    'ubc.ctlt.compair.lti.context'
]);

/***** Providers *****/
module.factory('LTIResource',
    ["$resource", "Interceptors",
    function($resource, Interceptors)
{
    var ret = $resource('/api/lti', {},
        {
            'getStatus': {url: '/api/lti/status'},
            'getMembershipStatus': {method: 'GET', url: '/api/lti/course/:id/membership/status'},
            'updateMembership': {method: 'POST', url: '/api/lti/course/:id/membership', interceptor: Interceptors.enrolCacheLTI}
        }
    );
    return ret;
}]);

module.factory('LTI',
        ["$rootScope", "$q", "localStorageService", "LTIResource",
        function ($rootScope, $q, localStorageService, LTIResource) {
    return {
        _lti_status: null,
        _check_storage: function() {
            if (this._lti_status == null) {
                var stored_lti_status = localStorageService.get('lti_status');

                if (stored_lti_status) {
                    this._lti_status = stored_lti_status;
                }
            }
        },
        ltiLinkUser: function() {
            this._check_storage();
            return this._lti_status != null && this._lti_status.user &&
                this._lti_status.user.exists == false;
        },
        clearStatus: function() {
            this._lti_status = null;
            localStorageService.remove('lti_status');
        },
        getStatus: function() {
            var scope = this;
            return LTIResource.getStatus().$promise.then(function (result) {
                scope._lti_status = result.status;
                localStorageService.set('lti_status', scope._lti_status);
                return scope._lti_status;
            });
        },
        isLTISession: function() {
            this._check_storage();
            return this._lti_status && this._lti_status.valid
        },
        getLTIUser: function() {
            this._check_storage();
            return this.isLTISession() ? this._lti_status.user : {};
        },
        getCourseName: function() {
            this._check_storage();
            return this._lti_status ? this._lti_status.course.name : "";
        }
    };
}]);

/***** Controllers *****/
module.controller("LTIController",
    ['$rootScope', '$scope', '$location', '$route', "$uibModal", 'breadcrumbs',
     'CourseRole', 'Toaster', 'AuthenticationService', 'LTI', 'LTIContextLinkResource', 'Session',
     'LearningRecordStatementHelper', 'resolvedData',
    function($rootScope, $scope, $location, $route, $uibModal, breadcrumbs,
             CourseRole, Toaster, AuthenticationService, LTI, LTIContextLinkResource, Session,
             LearningRecordStatementHelper, resolvedData)
    {
        $scope.status = resolvedData.ltiStatus;

        // check if valid lti status
        if (!$scope.status.valid) {
            // invalid lti session, get out of here
            LTI.destroy_lit_status();
            $location.path('/');

        // check if user doesn't exist
        } else if (!$scope.status.user.exists) {
            Session.destroy();
            $rootScope.$emit(AuthenticationService.LTI_LOGIN_REQUIRED_EVENT);

        // check if course doesn't exist
        } else if (!$scope.status.course.exists) {
            if ($scope.status.course.course_role == CourseRole.instructor) {
                var modalScope = $scope.$new();
                var modalInstance = $uibModal.open({
                    animation: true,
                    backdrop: 'static',
                    keyboard: false,
                    controller: "CourseSelectModalController",
                    templateUrl: 'modules/course/course-select-partial.html',
                    scope: modalScope
                });
                modalInstance.opened.then(function() {
                    LearningRecordStatementHelper.opened_modal("Select Course");
                });
                modalInstance.result.then(function (selectedCourseId) {
                    LTIContextLinkResource.linkCourse({course_id: selectedCourseId}, {},
                        function(ret) {
                            // refresh permissions
                            Session.expirePermissions();
                            Toaster.success("Course Linked", "Successfully linked your ComPAIR course as requested with an external source.");
                            // reload to refresh status and check what to do next
                            $route.reload();
                        }
                    );
                    LearningRecordStatementHelper.closed_modal("Select Course");
                }, function () {
                    // modal dismissed, reload page to update status
                    $route.reload();
                    LearningRecordStatementHelper.closed_modal("Select Course");
                });
            } else {
                // student can't setup course, get out of here
                Toaster.warning("Course Not Yet Ready", "Please wait for your instructor to set up the course and try accessing again.");
                $location.path('/');
            }
        } else {
            // setup complete, redirect to course or assignment is present
            if ($scope.status.assignment.exists) {
                $location.path('/course/'+$scope.status.course.id+"/assignment/"+$scope.status.assignment.id);
            } else {
                $location.path('/course/'+$scope.status.course.id);
            }
        }
    }]
);

// End anonymous function
})();