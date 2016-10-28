// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.lti', [
    'ngResource',
    'ngCookies',
    'ngRoute',
    'ng-breadcrumbs',
    'ui.bootstrap',
    'ubc.ctlt.compair.authentication',
    'ubc.ctlt.compair.authorization',
    'ubc.ctlt.compair.toaster',
    'ubc.ctlt.compair.user',
    'ubc.ctlt.compair.course'
]);

/***** Providers *****/
module.factory('LTIResource',
    ["$resource", "Interceptors",
    function($resource, Interceptors)
{
    var ret = $resource('/api/lti', {},
        {
            'getStatus': {url: '/api/lti/status'},
            'linkCourse': {method: 'POST', url: '/api/lti/course/:id/link', interceptor: Interceptors.enrolCacheLTI},
            'getMembershipStatus': {method: 'GET', url: '/api/lti/course/:id/membership/status'},
            'updateMembership': {method: 'POST', url: '/api/lti/course/:id/membership', interceptor: Interceptors.enrolCacheLTI}
        }
    );
    return ret;
}]);

module.factory('LTI',
        ["$rootScope", "$q", "$cookies", "LTIResource",
        function ($rootScope, $q, $cookies, LTIResource) {
    return {
        _lti_status: null,
        _check_cookies: function() {
            if (this._lti_status == null) {
                var cookie_lti_status = $cookies.getObject('current.lti.status');

                if (cookie_lti_status) {
                    this._lti_status = cookie_lti_status;
                }
            }
        },
        ltiLinkUser: function() {
            this._check_cookies();
            return this._lti_status != null && this._lti_status.user &&
                this._lti_status.user.exists == false;
        },
        clearStatus: function() {
            this._lti_status = null;
            $cookies.remove('current.lti.status');
        },
        getStatus: function() {
            var scope = this;
            return LTIResource.getStatus().$promise.then(function (result) {
                scope._lti_status = result.status;
                $cookies.putObject('current.lti.status', scope._lti_status);
                return scope._lti_status;
            });
        },
        isLTISession: function() {
            this._check_cookies();
            return this._lti_status && this._lti_status.valid
        },
        getLTIUser: function() {
            this._check_cookies();
            return this.isLTISession() ? this._lti_status.user : {};
        },
        getCourseName: function() {
            this._check_cookies();
            return this._lti_status ? this._lti_status.course.name : "";
        }
    };
}]);

/***** Controllers *****/
module.controller("LTIController",
    ['$rootScope', '$scope', '$location', '$route', "$modal", 'breadcrumbs','Authorize',
     'CourseRole', 'Toaster', 'AuthenticationService', 'LTI', 'LTIResource', 'Session',
    function($rootScope, $scope, $location, $route, $modal, breadcrumbs, Authorize,
             CourseRole, Toaster, AuthenticationService, LTI, LTIResource, Session) {
        $scope.status = {};

        LTI.getStatus().then(function(status) {
            $scope.status = status;

            // check if valid lti status
            if (!status.valid) {
                // invalid lti session, get out of here
                LTI.destroy_lit_status();
                $location.path('/');

            // check if user doesn't exist
            } else if (!status.user.exists) {
                Session.destroy();
                $rootScope.$emit(AuthenticationService.LTI_LOGIN_REQUIRED_EVENT);

            // check if course doesn't exist
            } else if (!status.course.exists) {
                if (status.course.course_role == CourseRole.instructor) {
                    var modalScope = $scope.$new();
                    var modalInstance = $modal.open({
                        animation: true,
                        backdrop: 'static',
                        keyboard: false,
                        controller: "CourseSelectModalController",
                        templateUrl: 'modules/course/course-select-partial.html',
                        scope: modalScope
                    });

                    modalInstance.result.then(function (selectedCourseId) {
                        LTIResource.linkCourse({id: selectedCourseId}, {},
                            function(ret) {
                                Toaster.success("Course Linked Successfully", "Successfully linked your course as requested.");
                                // reload to refresh status and check what to do next
                                $route.reload();
                            },
                            function(ret) {
                                Toaster.reqerror("LTI Course Linking Error", ret);
                            }
                        );
                    }, function () {
                        // modal dismissed, reload page to update status
                        $route.reload();
                    });
                } else {
                    // student can't setup course, get out of here
                    Toaster.warning("Course Not Yet Ready", "Please wait for your instructor to set up the course and try accessing again.");
                    $location.path('/');
                }
            } else {
                // setup complete, redirect to course or assignment is present
                if (status.assignment.exists) {
                    $location.path('/course/'+status.course.id+"/assignment/"+status.assignment.id);
                } else {
                    $location.path('/course/'+status.course.id);
                }
            }
        });
    }]
);
// End anonymous function
})();
