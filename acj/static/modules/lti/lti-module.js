// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.lti', [
    'ngResource',
    'ngCookies',
    'ngRoute',
    'ng-breadcrumbs',
    'ui.bootstrap',
    'ubc.ctlt.acj.authentication',
    'ubc.ctlt.acj.authorization',
    'ubc.ctlt.acj.toaster',
    'ubc.ctlt.acj.user',
    'ubc.ctlt.acj.course'
]);

/***** Providers *****/
module.factory('LTIResource',
    ["$resource",
    function($resource)
{
    var ret = $resource('/api/lti', {},
        {
            'getStatus': {url: '/api/lti/status'},
            'linkCourse': {method: 'POST', url: '/api/lti/course/:id/link'}
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
        ltiLogoutRedirect: function() {
            this._check_cookies();
            if (this._lti_status != null && this._lti_status.redirect != null) {
                return this._lti_status.redirect;
            };
            return false;
        },
        endActiveSession: function() {
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
        }
    };
}]);

/***** Controllers *****/
module.controller("LTIController",
    ['$rootScope', '$scope', '$location', '$route', "$modal", 'breadcrumbs','Authorize',
     'CourseRole', 'Toaster', 'AuthenticationService', 'LTI', 'LTIResource',
    function($rootScope, $scope, $location, $route, $modal, breadcrumbs, Authorize,
             CourseRole, Toaster, AuthenticationService, LTI, LTIResource) {
        var self = this;

        $scope.status = {};

        LTI.getStatus().then(function(status) {
            $scope.status = status;

            if (!status.valid) {
                LTI.destroy_lit_status();
                // redirect out of here
                return
            }

            // check if user doesn't exist
            if (!status.user.exists) {
                $rootScope.$emit(AuthenticationService.LTI_LOGIN_REQUIRED_EVENT);
                return
            }

            // check if course doesn't exist
            if (!status.course.exists) {
                if (status.course.course_role == CourseRole.instructor) {
                    var modalScope = $scope.$new();
                    modalScope.course = {
                        name: status.course.name,
                    };
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
                                Toaster.success("Course Link Successful", "Successfully linked course " + ret.id + " to LTI context");
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
                    // redirect out of here with proper error message
                }
                return
            }

            // check if assignment set or not
            if (!status.assignment.exists) {
                if (status.course.course_role == CourseRole.instructor) {
                    // redirect to course form
                } else {
                    // redirect out of here with proper error message
                }
                return
            }
        });
    }]
);
// End anonymous function
})();
