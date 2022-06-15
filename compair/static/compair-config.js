String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d)}/g, function(match, number) {
        return typeof args[number] != 'undefined' ? args[number] : match;
    });
};

var myApp = angular.module('myApp', [
    'ngRoute',
    'http-auth-interceptor',
    'LocalStorageModule',
    'ng-breadcrumbs',
    'angular-loading-bar',
    'ngPromiseExtras',
    'ubc.ctlt.compair.common',
    'ubc.ctlt.compair.learning_records.learning_record',
    'ubc.ctlt.compair.rich.content',
    'ubc.ctlt.compair.answer',
    'ubc.ctlt.compair.attachment',
    'ubc.ctlt.compair.classlist',
    'ubc.ctlt.compair.comment',
    'ubc.ctlt.compair.course',
    'ubc.ctlt.compair.criterion',
    'ubc.ctlt.compair.group',
    'ubc.ctlt.compair.gradebook',
    'ubc.ctlt.compair.home',
    'ubc.ctlt.compair.comparison',
    'ubc.ctlt.compair.login',
    'ubc.ctlt.compair.lti',
    'ubc.ctlt.compair.lti.consumer',
    'ubc.ctlt.compair.lti.context',
    'ubc.ctlt.compair.navbar',
    'ubc.ctlt.compair.assignment',
    'ubc.ctlt.compair.report',
    'localytics.directives',
    'templates'
]);

myApp.factory('StandardErrorHandler',
    ['$log', 'Toaster',
    function($log, Toaster)
{
    return function(error) {
        // ensure data attribute exists
        error.data = error.data || {};

        // title and message set to error.data or defaults
        var title = error.data.title || error.statusText;
        var message = error.data.message || undefined;
        switch (error.status) {
            case 400:
            case 409:
                $log.error(error.status, title, message);
                Toaster.warning(title, message);
                break;
            case 401:
                message = message || "Please log in again.";
                $log.warn(error.status, title, message);
                Toaster.warning(title, message);
                // session interceptor will handle this
                break;
            case 403:
                message = message || "Sorry, you don't have permission for this action.";
                $log.error(error.status, title, message);
                if (error.data.disabled_by_impersonation) {
                    Toaster.warning(title, message);
                } else {
                    Toaster.error(title, message);
                }
                break;
            case 404:
                message = message || "Resource not found.";
                $log.error(error.status, title, message);
                Toaster.error(title, message);
                break;
            default:
                // TODO Tell them what support to contact
                message = message || "Unable to connect. This might be a server issue or your connection might be down. Please contact support if the problem continues.";
                $log.error(error.status, title, message);
                Toaster.error(title, message);
        }
    }
}]);

myApp.factory('defaultErrorHandlerInterceptor',
    ['$rootScope', '$q', 'StandardErrorHandler',
    function($rootScope, $q, StandardErrorHandler)
{
    return {
        'responseError': function(rejection) {
            var config = rejection.config;
            if (config && config.bypassErrorsInterceptor) {
                return $q.reject(rejection);
            }
            if ($rootScope.skipAutoToastAPIErrors !== true) {
                StandardErrorHandler(rejection);
            }
            return $q.reject(rejection);
        }
    }
}]);

myApp.factory('ResolveDeferredRouteData',
    ['$rootScope', '$q', 'StandardErrorHandler', 'Toaster',
    function($rootScope, $q, StandardErrorHandler, Toaster)
{
    return function(promises, priorityOrder) {
        priorityOrder = priorityOrder || [];
        var deferred = $q.defer();
        var orderedKeys = _.concat(priorityOrder, _.pullAll(_.keys(promises), priorityOrder));

        // turn automatic toasting of api errors off since we only want to display
        // the most relevant toaster to the user
        $rootScope.skipAutoToastAPIErrors = true;
        $q.allSettled(promises).then(function (results) {
            $rootScope.skipAutoToastAPIErrors = undefined;
            // check for rejections in order or priority (then all remaining keys)
            for(var index in orderedKeys) {
                var result = results[orderedKeys[index]];
                if (result && result.state == 'rejected') {
                    Toaster.clear();
                    StandardErrorHandler(result.reason);
                    return deferred.reject(result.reason);
                }
            }
            // resolve with results values
            _.forEach(results, function(result, key) {
                results[key] = result.value;
            });
            return deferred.resolve(results);
        });
        return deferred.promise;
    }
}]);

myApp.factory('RouteResolves',
    ["$q", "$route", "Toaster", "Authorize", "Session", "LTI",
     "CourseResource", "AssignmentResource", "ClassListResource", "GroupResource",
     "UserResource", "ComparisonExampleResource", "CriterionResource", "GroupUserResource",
     "AnswerResource", "TimerResource", "GradebookResource", "LTIConsumerResource",
     "UserLTIUsersResource", "UserThirdPartyUsersResource", "AuthTypesEnabled",
    function($q, $route, Toaster, Authorize, Session, LTI,
             CourseResource, AssignmentResource, ClassListResource, GroupResource,
             UserResource, ComparisonExampleResource, CriterionResource, GroupUserResource,
             AnswerResource, TimerResource, GradebookResource, LTIConsumerResource,
             UserLTIUsersResource, UserThirdPartyUsersResource, AuthTypesEnabled)
{
    return {

        // Authorization Users
        canManageUsers: function() {
            return Authorize.can(Authorize.MANAGE, UserResource.MODEL);
        },
        canCreateUsers: function() {
            return Authorize.can(Authorize.CREATE, UserResource.MODEL);
        },
        // Authorization Courses
        canAddCourse: function() {
            return Authorize.can(Authorize.CREATE, CourseResource.MODEL);
        },
        canEditCourse: function() {
            var courseId = $route.current.params.courseId;
            return Authorize.can(Authorize.EDIT, CourseResource.MODEL, courseId);
        },
        // Authorization Assignments
        canCreateAssignment: function() {
            var courseId = $route.current.params.courseId;
            return Authorize.can(Authorize.CREATE, AssignmentResource.MODEL, courseId);
        },
        canManageAssignment: function() {
            var courseId = $route.current.params.courseId;
            return Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, courseId);
        },

        // Get current user
        loggedInUser: function() {
            return Session.getUser();
        },

        // Pre-loading resources by route ids
        consumer: function() {
            var consumerId = $route.current.params.consumerId;
            return LTIConsumerResource.get({'id': consumerId}).$promise;
        },
        user: function() {
            var userId = $route.current.params.userId;
            return UserResource.get({'id': userId}).$promise;
        },
        userEditButton: function() {
            var userId = $route.current.params.userId;
            return UserResource.getEditButton({'id': userId}).$promise;
        },
        course: function() {
            var courseId = $route.current.params.courseId;
            return CourseResource.get({'id': courseId}).$promise;
        },
        courseAssignments: function() {
            var courseId = $route.current.params.courseId;
            return AssignmentResource.get({'courseId': courseId}).$promise;
        },
        classlist: function() {
            var courseId = $route.current.params.courseId;
            return ClassListResource.get({'courseId': courseId}).$promise;
        },
        groups: function() {
            var courseId = $route.current.params.courseId;
            return GroupResource.get({'courseId': courseId}).$promise;
        },
        currentUserGroup: function() {
            var courseId = $route.current.params.courseId;
            return GroupUserResource.getCurrentUserGroup({'courseId': courseId}).$promise;
        },
        students: function() {
            var courseId = $route.current.params.courseId;
            return CourseResource.getStudents({'id': courseId}).$promise;
        },
        instructors: function() {
            var courseId = $route.current.params.courseId;
            return CourseResource.getInstructors({'id': courseId}).$promise;
        },
        assignment: function() {
            var courseId = $route.current.params.courseId;
            var assignmentId = $route.current.params.assignmentId;
            return AssignmentResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise;
        },
        assignmentStatus: function() {
            var courseId = $route.current.params.courseId;
            var assignmentId = $route.current.params.assignmentId;
            return AssignmentResource.getCurrentUserStatus({'courseId': courseId, 'assignmentId': assignmentId}).$promise;
        },
        assignmentComparisonExamples: function() {
            var courseId = $route.current.params.courseId;
            var assignmentId = $route.current.params.assignmentId;
            return ComparisonExampleResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise;
        },
        gradebook: function() {
            var courseId = $route.current.params.courseId;
            var assignmentId = $route.current.params.assignmentId;
            return GradebookResource.get({'courseId': courseId, 'assignmentId': assignmentId}).$promise;
        },
        answer: function() {
            var courseId = $route.current.params.courseId;
            var assignmentId = $route.current.params.assignmentId;
            var answerId = $route.current.params.answerId;
            return AnswerResource.get({'courseId': courseId, 'assignmentId': assignmentId, 'answerId': answerId}).$promise;
        },
        userAnswers: function() {
            var courseId = $route.current.params.courseId;
            var assignmentId = $route.current.params.assignmentId;
            return AnswerResource.user({'courseId': courseId, 'assignmentId': assignmentId}).$promise;
        },
        userLTIs: function() {
            if (AuthTypesEnabled.lti) {
                var userId = $route.current.params.userId;
                return UserLTIUsersResource.get({'id': userId}).$promise;
            }
            return $q.when({'objects':[]});
        },
        userThirdPartyUsers: function() {
            if (AuthTypesEnabled.cas || AuthTypesEnabled.saml) {
                var userId = $route.current.params.userId;
                return UserThirdPartyUsersResource.get({'id': userId}).$promise;
            }
            return $q.when({'objects':[]});
        },

        //other
        timer: function() {
            return TimerResource.get().$promise;
        },
        criteria: function() {
            return CriterionResource.get().$promise;
        },
        coursesAsInstructor: function() {
            return UserResource.getTeachingUserCourses().$promise;
        },
        ltiStatus: function() {
            return LTI.getStatus();
        },
    }
}]);

myApp.config(
    ['$routeProvider', '$logProvider', '$httpProvider', '$locationProvider',
     "RouteResolvesProvider", "ResolveDeferredRouteDataProvider",
     "localStorageServiceProvider", "chosenProvider",
    function ($routeProvider, $logProvider, $httpProvider, $locationProvider,
              RouteResolvesProvider, ResolveDeferredRouteDataProvider,
              localStorageServiceProvider, chosenProvider) {

    var debugMode = false;

    localStorageServiceProvider.setStorageType('sessionStorage');
    localStorageServiceProvider.setPrefix('compair');
    localStorageServiceProvider.setStorageCookie(0); // fallback default settings

    chosenProvider.setOption({
        disable_search_threshold: 8,
        search_contains: true,
        enable_split_word_search: true
    });

    if (!$httpProvider.defaults.headers.common) {
        $httpProvider.defaults.headers.common = {};
    }
    $httpProvider.defaults.headers.common['If-Modified-Since'] = '0';
    $httpProvider.defaults.headers.common.Accept = 'application/json';
    $httpProvider.interceptors.push('defaultErrorHandlerInterceptor');

    var RouteResolves = RouteResolvesProvider.$get();
    var ResolveDeferredRouteData = ResolveDeferredRouteDataProvider.$get();

    // doesn't work for now. URLs are encoded in address bar
    // $locationProvider.html5Mode(true);
    // $locationProvider.hashPrefix('!');

    $routeProvider
        .when ('/',
            {
                title: 'Home',
                templateUrl: 'modules/home/home-partial.html',
                label: "Home", // breadcrumb label
                controller: 'HomeController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            loggedInUser: RouteResolves.loggedInUser(),
                            canAddCourse: RouteResolves.canAddCourse(),
                            canManageUsers: RouteResolves.canManageUsers(),
                        });
                    }
                }
            })
        .when ('/course/create',
            {
                title: 'Add Course',
                templateUrl: 'modules/course/course-partial.html',
                label: "Add Course",
                controller: 'CourseController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            loggedInUser: RouteResolves.loggedInUser(),
                        }, ['course']);
                    }
                }
            })
        .when ('/course/:courseId',
            {
                title: 'Course Assignments',
                templateUrl: 'modules/course/course-assignments-partial.html',
                label: "Course Assignments",
                controller: 'CourseAssignmentsController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            courseAssignments: RouteResolves.courseAssignments(),
                            loggedInUser: RouteResolves.loggedInUser(),
                            canEditCourse: RouteResolves.canEditCourse(),
                            canCreateAssignment: RouteResolves.canCreateAssignment(),
                            canManageAssignment: RouteResolves.canManageAssignment(),
                            canManageUsers: RouteResolves.canManageUsers(),
                        }, ['course', 'courseAssignments']);
                    }
                }
            })
        .when ('/course/:courseId/edit',
            {
                title: 'Edit Course',
                templateUrl: 'modules/course/course-partial.html',
                label: "Edit Course",
                controller: 'CourseController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            loggedInUser: RouteResolves.loggedInUser(),
                        }, ['course']);
                    }
                }
            })
        .when ('/course/:courseId/duplicate',
            {
                title: "Duplicate Course",
                templateUrl: 'modules/course/course-duplicate-partial.html',
                label: "Duplicate Course",
                controller: 'CourseDuplicateController'
            })
        .when ('/course/:courseId/user',
            {
                title: "Manage Users",
                templateUrl: 'modules/classlist/classlist-view-partial.html',
                label: "Manage Users",
                controller: 'ClassViewController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            classlist: RouteResolves.classlist(),
                            groups: RouteResolves.groups(),
                            loggedInUser: RouteResolves.loggedInUser(),
                            canManageUsers: RouteResolves.canManageUsers(),
                            canCreateUsers: RouteResolves.canCreateUsers(),
                        }, ['course']);
                    }
                }
            })
        .when ('/course/:courseId/user/import',
            {
                title: "Import Users",
                templateUrl: 'modules/classlist/classlist-import-partial.html',
                label: "Import Users",
                controller: 'ClassImportController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                        }, ['course']);
                    }
                }
            })
        .when ('/course/:courseId/user/import/results',
            {
                title: "Results",
                templateUrl: 'modules/classlist/classlist-import-results-partial.html',
                label: "Results",
                controller: 'ClassImportResultsController',
                resolve: {
                    resolvedData: function() {
                        // no data to preload
                    }
                }
            })
        .when ('/course/:courseId/assignment/create',
            {
                title: "Add Assignment",
                templateUrl: 'modules/assignment/assignment-form-partial.html',
                label: "Add Assignment",
                controller: 'AssignmentWriteController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            criteria: RouteResolves.criteria(),
                            groups: RouteResolves.groups(),
                            loggedInUser: RouteResolves.loggedInUser(),
                            canManageAssignment: RouteResolves.canManageAssignment(),
                        }, ['course', 'criteria']);
                    }
                }
            })
        .when ('/course/:courseId/assignment/:assignmentId',
            {
                title: "Assignment & Results",
                templateUrl: 'modules/assignment/assignment-view-partial.html',
                label: "Assignment & Results",
                controller: 'AssignmentViewController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            assignment: RouteResolves.assignment(),
                            students: RouteResolves.students(),
                            instructors: RouteResolves.instructors(),
                            currentUserGroup: RouteResolves.currentUserGroup(),
                            loggedInUser: RouteResolves.loggedInUser(),
                            canManageAssignment: RouteResolves.canManageAssignment(),
                        }, ['course', 'assignment', 'students', 'instructors', 'currentUserGroup']);
                    }
                },
                reloadOnSearch: false,
            })
        .when ('/assignment/search/enddate',
            {
                title: 'Plan Release Date',
                templateUrl: 'modules/assignment/assignment-search-partial.html',
                label: "Plan Release Date",
                controller: 'AssignmentSearchEndDateController',
                resolve: {
                    resolvedData: function() {
                        // no data to preload
                    }
                }
            })
        .when ('/course/:courseId/assignment/:assignmentId/edit',
            {
                title: "Edit Assignment",
                templateUrl: 'modules/assignment/assignment-form-partial.html',
                label: "Edit Assignment",
                controller: 'AssignmentWriteController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            assignment: RouteResolves.assignment(),
                            assignmentComparisonExamples: RouteResolves.assignmentComparisonExamples(),
                            criteria: RouteResolves.criteria(),
                            groups: RouteResolves.groups(),
                            loggedInUser: RouteResolves.loggedInUser(),
                            canManageAssignment: RouteResolves.canManageAssignment(),
                        }, ['course', 'assignment', 'assignmentComparisonExamples', 'criteria', 'groups']);
                    }
                }
            })
        .when ('/course/:courseId/assignment/:assignmentId/duplicate',
            {
                title: "Duplicate Assignment",
                templateUrl: 'modules/assignment/assignment-form-partial.html',
                label: "Duplicate Assignment",
                controller: 'AssignmentWriteController',
                method: 'copy',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            assignment: RouteResolves.assignment(),
                            assignmentComparisonExamples: RouteResolves.assignmentComparisonExamples(),
                            criteria: RouteResolves.criteria(),
                            groups: RouteResolves.groups(),
                            loggedInUser: RouteResolves.loggedInUser(),
                            canManageAssignment: RouteResolves.canManageAssignment(),
                        }, ['course', 'assignment', 'assignmentComparisonExamples', 'criteria']);
                    }
                }
            })
        .when ('/course/:courseId/assignment/:assignmentId/compare',
            {
                title: "Compare Answer Pairs",
                templateUrl: 'modules/comparison/comparison-form-partial.html',
                label: "Compare Answer Pairs",
                controller: 'ComparisonController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            assignment: RouteResolves.assignment(),
                            loggedInUser: RouteResolves.loggedInUser(),
                            timer: RouteResolves.timer(),
                            canManageAssignment: RouteResolves.canManageAssignment(),
                        }, ['course', 'assignment']);
                    }
                }
            })
        .when('/course/:courseId/assignment/:assignmentId/self_evaluation',
            {
                title: "Self-Evaluation",
                templateUrl: 'modules/comparison/comparison-self_evaluation-partial.html',
                label: "Self-Evaluation",
                controller: 'ComparisonSelfEvalController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            course: RouteResolves.course(),
                            assignment: RouteResolves.assignment(),
                            assignmentStatus: RouteResolves.assignmentStatus(),
                            userAnswers: RouteResolves.userAnswers(),
                            loggedInUser: RouteResolves.loggedInUser(),
                        }, ['course', 'assignment', 'assignmentStatus', 'userAnswers']);
                    }
                }
            })
        .when('/report',{
                title: "Download Reports",
                templateUrl: 'modules/report/report-create-partial.html',
                label: "Download Reports",
                controller: 'ReportCreateController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            coursesAsInstructor: RouteResolves.coursesAsInstructor(),
                        }, ['coursesAsInstructor']);
                    }
                }
            })
        .when('/user/create',
            {
                title: "Add User",
                templateUrl: 'modules/user/user-create-partial.html',
                label: "Add User",
                controller: 'UserWriteController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            canManageUsers: RouteResolves.canManageUsers(),
                            loggedInUser: RouteResolves.loggedInUser(),
                        }, []);
                    }
                }
            })
        .when('/user/:userId/edit',
            {
                title: "Edit User",
                templateUrl: 'modules/user/user-edit-partial.html',
                label: "Edit User",
                controller: 'UserWriteController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            user: RouteResolves.user(),
                            canManageUsers: RouteResolves.canManageUsers(),
                            loggedInUser: RouteResolves.loggedInUser(),
                        }, ['user']);
                    }
                }
            })
        .when('/user/:userId',
            {
                title: "View User",
                templateUrl: 'modules/user/user-view-partial.html',
                label: "View User",
                controller: 'UserViewController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            user: RouteResolves.user(),
                            userEditButton: RouteResolves.userEditButton(),
                            canManageUsers: RouteResolves.canManageUsers(),
                            loggedInUser: RouteResolves.loggedInUser(),
                        }, ['user', 'userEditButton']);
                    }
                }
            })
        .when('/users',
            {
                title: "Manage All Users",
                templateUrl: 'modules/user/user-list-partial.html',
                label: "Manage All Users",
                controller: 'UserListController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            canManageUsers: RouteResolves.canManageUsers(),
                            loggedInUser: RouteResolves.loggedInUser(),
                        }, []);
                    }
                }
            })
        .when('/users/:userId/manage',
            {
                title: "User Courses & Accounts",
                templateUrl: 'modules/user/user-manage-partial.html',
                label: "User Courses & Accounts",
                controller: 'UserManageController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            user: RouteResolves.user(),
                            canManageUsers: RouteResolves.canManageUsers(),
                            userLTIs: RouteResolves.userLTIs(),
                            userThirdPartyUsers: RouteResolves.userThirdPartyUsers()
                        }, ['user']);
                    }
                }
            })
        .when('/lti',
            {
                title: "ComPAIR Setup",
                templateUrl: 'modules/lti/lti-setup-partial.html',
                label: "ComPAIR Setup",
                controller: 'LTIController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            ltiStatus: RouteResolves.ltiStatus()
                        }, []);
                    }
                },
                excludeBreadcrumb: true
            })
        .when('/lti/consumer',
            {
                title: "Manage LTI Consumers",
                templateUrl: 'modules/lti_consumer/lti-consumers-list-partial.html',
                label: "Manage LTI",
                controller: 'LTIConsumerListController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            canManageUsers: RouteResolves.canManageUsers()
                        }, []);
                    }
                },
            })
        .when('/lti/consumer/create',
            {
                title: "Add LTI Consumer",
                templateUrl: 'modules/lti_consumer/lti-consumer-form-partial.html',
                label: "Add LTI Consumer",
                controller: 'LTIConsumerWriteController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            canManageUsers: RouteResolves.canManageUsers()
                        }, []);
                    }
                },
            })
        .when('/lti/consumer/:consumerId/edit',
            {
                title: "Edit LTI Consumer",
                templateUrl: 'modules/lti_consumer/lti-consumer-form-partial.html',
                label: "Edit LTI Consumer",
                controller: 'LTIConsumerWriteController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            consumer: RouteResolves.consumer(),
                            canManageUsers: RouteResolves.canManageUsers()
                        }, ['consumer']);
                    }
                },
            })
        .when('/lti/consumer/:consumerId',
            {
                title: "View LTI Consumer",
                templateUrl: 'modules/lti_consumer/lti-consumer-view-partial.html',
                label: "View LTI Consumer",
                controller: 'LTIConsumerViewController',
                resolve: {
                    resolvedData: function() {
                        return ResolveDeferredRouteData({
                            consumer: RouteResolves.consumer(),
                            canManageUsers: RouteResolves.canManageUsers()
                        }, ['consumer']);
                    }
                },
            })
        .otherwise({redirectTo: '/'});

    $logProvider.debugEnabled(debugMode);
}]);

myApp.run(
    ['$rootScope',
    function ($rootScope)
    {
        //handle routeProvider resolve errors
        $rootScope.$on("$routeChangeError", function(evt, current, previous, rejection) {
            // display error box only if user has no previous or was already showing the error box and got another error
            if (previous === undefined || $rootScope.routeResolveLoadError !== undefined ) {
                $rootScope.routeResolveLoadError = rejection;
            } else {
                $rootScope.routeResolveLoadError = undefined;
            }
        });
        $rootScope.$on("$routeChangeSuccess", function(evt, current, previous) {
            $rootScope.routeResolveLoadError = undefined;
            $rootScope.title = current.$$route.title;
        });
    }
]);

// placeholder for templates module to store templates into cache
// gulp prod will generate the actual templates module and put contents into cache
angular.module('templates', []).run(['$templateCache', function ($templateCache) {

}]);