String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d)}/g, function(match, number) {
        return typeof args[number] != 'undefined' ? args[number] : match;
    });
};

var myApp = angular.module('myApp', [
    'ngRoute',
    'http-auth-interceptor',
    'ngCookies',
    'ng-breadcrumbs',
    'angular-loading-bar',
    'ubc.ctlt.compair.common',
    'ubc.ctlt.compair.common.xapi',
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
    'ubc.ctlt.compair.navbar',
    'ubc.ctlt.compair.assignment',
    'ubc.ctlt.compair.report',
    'ubc.ctlt.compair.oauth',
    'templates'
]);

myApp.factory('defaultErrorHandlerInterceptor', ['$q', '$log', 'Toaster', function($q, $log, Toaster) {
    return {
        'responseError': function(rejection) {
            switch (rejection.status) {
                case 400:
                case 409:
                    $log.error(rejection.statusText);
                    Toaster.warning(rejection.statusText, rejection.data.error);
                    break;
                case 401:
                    // session interceptor will handle this
                    break;
                case 403:
                    $log.error(rejection.statusText);
                    Toaster.error(rejection.statusText, "Sorry, you don't have permission for this action.");
                    break;
                default:
                    $log.error(rejection.statusText);
                    // TODO Tell them what support to contact
                    Toaster.error(rejection.statusText, "Unable to connect. This might be a server issue or your connection might be down. Please contact support if the problem continues.");

            }
            return $q.reject(rejection);
        }
    }
}]);

myApp.config(['$routeProvider', '$logProvider', '$httpProvider', '$locationProvider',
    function ($routeProvider, $logProvider, $httpProvider, $locationProvider) {

    var debugMode = false;

    if (!$httpProvider.defaults.headers.common) {
        $httpProvider.defaults.headers.common = {};
    }
    $httpProvider.defaults.headers.common['If-Modified-Since'] = '0';
    $httpProvider.defaults.headers.common.Accept = 'application/json';
    $httpProvider.interceptors.push('defaultErrorHandlerInterceptor');

    // doesn't work for now. URLs are encoded in address bar
    // $locationProvider.html5Mode(true);
    // $locationProvider.hashPrefix('!');

    $routeProvider
        .when ('/',
            {
                templateUrl: 'modules/home/home-partial.html',
                label: "Home" // breadcrumb label
            })
        .when ('/oauth/create',
            {
                templateUrl: 'modules/oauth/oauth-partial.html',
                label: "Create account", // breadcrumb label
                controller: 'OAuthController',
                method: 'new'
            })
        .when ('/course/new',
            {
                templateUrl: 'modules/course/course-partial.html',
                label: "Add Course",
                controller: 'CourseController',
                controllerAs: 'rc',
                method: 'new'
            })
        .when ('/course/:courseId',
            {
                templateUrl: 'modules/course/course-assignments-partial.html',
                label: "Course Assignments"
            })
        .when ('/course/:courseId/configure',
            {
                templateUrl: 'modules/course/course-partial.html',
                label: "Edit Course",
                controller: 'CourseController',
                controllerAs: 'rc',
                method: 'edit'
            })
        .when ('/course/:courseId/user',
            {
                templateUrl: 'modules/classlist/classlist-view-partial.html',
                label: "Manage Users"
            })
        .when ('/course/:courseId/user/import',
            {
                templateUrl: 'modules/classlist/classlist-import-partial.html',
                label: "Import Users"
            })
        .when ('/course/:courseId/user/import/results',
            {
                templateUrl: 'modules/classlist/classlist-import-results-partial.html',
                label: "Results"
            })
        .when ('/course/:courseId/user/group/import',
           {
                templateUrl: 'modules/group/group-import-partial.html',
                label: "Assign Groups"
           })
        .when ('/course/:courseId/user/group/import/results',
            {
                templateUrl: 'modules/group/group-import-results-partial.html',
                label: "Results"
            })
        .when ('/course/:courseId/assignment/create',
            {
                templateUrl: 'modules/assignment/assignment-create-partial.html',
                label: "Add Assignment",
                method: 'new'
            })
        .when ('/course/:courseId/assignment/:assignmentId',
            {
                templateUrl: 'modules/assignment/assignment-view-partial.html',
                label: "View Assignment"
            })
        .when ('/course/:courseId/assignment/:assignmentId/edit',
            {
                templateUrl: 'modules/assignment/assignment-edit-partial.html',
                label: "Edit Assignment",
                method: 'edit'
            })
        .when ('/course/:courseId/assignment/:assignmentId/answer/create',
            {
                templateUrl: 'modules/answer/answer-create-partial.html',
                label: "Answer",
                method: 'new'
            })
        .when ('/course/:courseId/assignment/:assignmentId/answer/:answerId/edit',
            {
                templateUrl: 'modules/answer/answer-edit-partial.html',
                label: "Edit Answer",
                method: 'edit'
            })
        .when ('/course/:courseId/assignment/:assignmentId/comment/create',
            {
                templateUrl: 'modules/comment/comment-assignment-create-partial.html',
                label: "Comment on Assignment"
            })
        .when ('/course/:courseId/assignment/:assignmentId/comment/:commentId/edit',
            {
                templateUrl: 'modules/comment/comment-assignment-edit-partial.html',
                label: "Edit Comment on Assignment"
            })
        .when('/course/:courseId/assignment/:assignmentId/answer/:answerId/comment/create',
            {
                templateUrl: 'modules/comment/comment-answer-create-partial.html',
                label: "Reply"
            })
        .when('/course/:courseId/assignment/:assignmentId/answer/:answerId/comment/:commentId/edit',
            {
                templateUrl: 'modules/comment/comment-answer-edit-partial.html',
                label: "Edit Reply"
            })
        .when ('/course/:courseId/assignment/:assignmentId/compare',
            {
                templateUrl: 'modules/comparison/comparison-partial.html',
                label: "Compare Answers"
            })
        .when('/course/:courseId/assignment/:assignmentId/self_evaluation',
            {
                templateUrl: 'modules/comparison/comparison-self_evaluation-partial.html',
                label: "Self-Evaluation"
            })
        .when ('/course/:courseId/assignment/:assignmentId/comparisons',
            {
                templateUrl: 'modules/comment/comment-comparison-partial.html',
                label: "Comparisons"
            })
        .when('/course/:courseId/criterion/:criterionId/edit',
            {
                templateUrl: 'modules/criterion/criterion-configure-partial.html',
                label: "Edit Criterion"
            })
        .when('/report',{
                templateUrl: 'modules/report/report-create-partial.html',
                label: "Run Reports"
            })
        .when('/course/:courseId/gradebook',
            {
                templateUrl: 'modules/gradebook/gradebook-partial.html',
                label: "See Activity"
            })
        .when('/user/create',
            {
                templateUrl: 'modules/user/user-create-partial.html',
                label: "Create Account",
                controller: 'UserController',
                method: 'new'
            })
        .when('/user/:userId/edit',
            {
                templateUrl: 'modules/user/user-edit-partial.html',
                label: "User Profile",
                controller: 'UserController',
                method: 'edit'
            })
        .when('/user/:userId',
            {
                templateUrl: 'modules/user/user-view-partial.html',
                label: "User Profile",
                controller: 'UserController',
                method: 'view'
            })
        .when('/lti',
            {
                templateUrl: 'modules/lti/lti-setup-partial.html',
                label: "ComPAIR Setup",
                controller: 'LTIController'
            })
        .otherwise({redirectTo: '/'});

    $logProvider.debugEnabled(debugMode);
}]);

myApp.config(
    [function ()
    {
        // config MathJax
        window.MathJax.Hub.Config({
            skipStartupTypeset: true
        });
        window.MathJax.Hub.Configured();

        // config CKEDITOR
        window.CKEDITOR.plugins.addExternal( 'combinedmath', '/app/lib_extension/ckeditor/plugins/combinedmath/' );
        window.CKEDITOR.on('dialogDefinition', function(ev) {
            var dialogName = ev.data.name;
            var dialog = ev.data.definition.dialog;
            var dialogDefinition = ev.data.definition;

            if (dialogName === 'link') {
                var target = dialogDefinition.getContents('target');
                target.get('linkTargetType')['default'] = '_blank';
                /*
                var options = target.get('linkTargetType').items;

                for (var i = options.length-1; i >= 0; i--) {
                    var value = options[i][1];
                    if (!value.match(/\_blank/i)) {
                        options.splice(i, 1);
                    }
                }
                */
            }
        });
    }
]);

// placeholder for templates module to store templates into cache
// gulp prod will generate the actual templates module and put contents into cache
angular.module('templates', []).run(['$templateCache', function ($templateCache){
}]);