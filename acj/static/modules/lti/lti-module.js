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
            'linkCourse': {method: 'POST', url: '/api/lti/course/:id/link'},
            'getMembershipStatus': {method: 'GET', url: '/api/lti/course/:id/membership/status'},
            'updateMembership': {method: 'POST', url: '/api/lti/course/:id/membership'}
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
        },
        isLTISession: function() {
            this._check_cookies();
            return this._lti_status.valid
        },
        getDisplayName: function() {
            this._check_cookies();
            return this._lti_status.user.displayname
        },
        getFirstName: function() {
            this._check_cookies();
            return this._lti_status.user.firstname
        },
        getLastName: function() {
            this._check_cookies();
            return this._lti_status.user.lastname
        },
        getEmail: function() {
            this._check_cookies();
            return this._lti_status.user.email
        },
        getCourseName: function() {
            this._check_cookies();
            return this._lti_status.course.name
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
                                if (ret.warning) {
                                    Toaster.warning("Course Link Successful but Membership Import Failed", ret.warning);
                                } else {
                                    Toaster.success("Course Link Successful", "Successfully linked course to LTI context");
                                }
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
                    Toaster.warning("Course not Ready", "Please wait for your instructor to setup the course and try again.");
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
