// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.user', [
    'ngResource',
    'ngRoute',
    'ng-breadcrumbs',
    'ubc.ctlt.acj.session',
    'ubc.ctlt.acj.authorization',
    'ubc.ctlt.acj.toaster'
]);

/***** Providers *****/
module.factory('UserResource', ['$resource', function($resource) {
    var User = $resource('/api/users/:id', {id: '@id'}, {
        'getUserCourses': {url: '/api/users/:id/courses'},
        'getTeachingUserCourses': {url: '/api/users/courses/teaching'},
        'getEditButton': {url: '/api/users/:id/edit'},
        'password': {method: 'POST', url: '/api/users/:id/password'}
    });
    User.MODEL = "User";

    User.prototype.isLoggedIn = function() {
        return this.hasOwnProperty('id');
    };

    return User;
}]);

module.constant('SystemRole', {
    student: "Student",
    instructor: "Instructor",
    sys_admin: "System Administrator"
});

module.constant('CourseRole', {
    dropped: "Dropped",
    instructor: "Instructor",
    teaching_assistant: "Teaching Assistant",
    student: "Student"
});

/***** Controllers *****/
module.controller("UserController",
    ['$scope', '$log', '$route', '$routeParams', '$location', 'breadcrumbs', 'Session',
     'UserResource', 'Authorize', 'SystemRole', 'Toaster',
    function($scope, $log, $route, $routeParams, $location, breadcrumbs, Session,
             UserResource, Authorize, SystemRole, Toaster) {
        var userId;
        var self = this;
        var messages = {
            new: {title: 'New User Created', msg: 'User should now have access.'},
            edit: {title: 'User Successfully Updated', msg: 'Your changes were saved.'}
        };
        $scope.user = {};
        $scope.method = 'new';
        $scope.password = {};
        $scope.system_roles = [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]
        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;
        });
        Authorize.can(Authorize.CREATE, UserResource.MODEL).then(function(result) {
            $scope.canCreateUsers = result;
        });
        Session.getUser().then(function(user) {
            $scope.ownProfile = userId == user.id;

            // remove system admin from system roles if current_user is not an admin
            if (user.system_role != SystemRole.sys_admin) {
                $scope.system_roles.pop()
            }
        });

        $scope.save = function() {
            $scope.submitted = true;
            UserResource.save({'id': userId}, $scope.user, function(ret) {
                Toaster.success(messages[$scope.method].title, messages[$scope.method].msg);
                Session.getUser().then(function(user) {
                    // refresh User's info on editing own profile and displaynmae changed
                    if (userId == user.id && $scope.user.displayname != user.displayname) {
                        Session.refresh();
                    }
                });
                $location.path('/user/' + ret.id);
            }).$promise.finally(function() {
                $scope.submitted = false;
            });
        };

        self['new'] = function() {
            $scope.user.system_role = SystemRole.student;
        };

        self.edit = function() {
            userId = $routeParams.userId;
            $scope.user = UserResource.get({'id':userId}, function (ret) {
                breadcrumbs.options = {'User Profile': "{0}'s Profile".format(ret.displayname)};
            });
        };

        self.view = function() {
            self.edit();
            Authorize.can(Authorize.CREATE, UserResource.MODEL).then(function(result) {
                $scope.canCreateUser = result;
            });
            $scope.showEditButton = UserResource.getEditButton({"id":userId});
        };

        $scope.changePassword = function() {
            $scope.submitted = true;
            UserResource.password({'id': $scope.user.id}, $scope.password, function (ret) {
                Toaster.success("Password Successfully Updated", "Your password has been changed.");
                $location.path('/user/' + ret.id);
            }).$promise.finally(function() {
                $scope.submitted = false;
            });
        };

        //  Calling routeParam method
        if ($route.current !== undefined && $route.current.method !== undefined) {
            $scope.method = $route.current.method;
            if (self.hasOwnProperty($route.current.method)) {
                self[$scope.method]();
            }
        }
    }]
);
// End anonymous function
})();
