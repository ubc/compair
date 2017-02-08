// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.user', [
    'ngResource',
    'ngRoute',
    'ng-breadcrumbs',
    'ubc.ctlt.compair.session',
    'ubc.ctlt.compair.authorization',
    'ubc.ctlt.compair.toaster'
]);

/***** Providers *****/
module.factory('UserResource', ['$resource', function($resource) {
    var User = $resource('/api/users/:id', {id: '@id'}, {
        getUserCourses: {url: '/api/users/courses'},
        getUserCoursesById: {url: '/api/users/:id/courses'},
        getUserCoursesStatus: {url: '/api/users/courses/status'},
        getTeachingUserCourses: {url: '/api/users/courses/teaching'},
        getEditButton: {url: '/api/users/:id/edit'},
        password: {method: 'POST', url: '/api/users/:id/password'}
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
        $scope.SystemRole = SystemRole;
        $scope.system_roles = [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]
        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;
        });
        Session.getUser().then(function(user) {
            $scope.ownProfile = userId == user.id;
            $scope.loggedInUserIsInstructor = user.system_role == SystemRole.instructor;

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
            $scope.user.uses_compair_login = true;
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

module.controller("UserListController",
    ['$scope', '$location', 'UserResource', 'Toaster', 'breadcrumbs', 'Session', 'SystemRole',
     'Authorize', 'xAPIStatementHelper',
    function($scope, $location, UserResource, Toaster, breadcrumbs, Session, SystemRole,
             Authorize, xAPIStatementHelper) {

        $scope.predicate = 'firstname';
        $scope.reverse = false;
        $scope.loggedInUserId = null;
        $scope.users = [];
        $scope.totalNumUsers = 0;
        $scope.userFilters = {
            page: 1,
            perPage: 20,
            search: null,
            orderBy: null,
            reverse: null
        };
        //$scope.SystemRole = SystemRole;
        //$scope.system_roles = [SystemRole.student, SystemRole.instructor]

        Session.getUser().then(function(user) {
            $scope.loggedInUserId = user.id;
        });

        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;

            if ($scope.canManageUsers) {
                $scope.updateUserList();
                // register watcher here so that we start watching when all filter values are set
                $scope.$watchCollection('userFilters', filterWatcher);
            } else {
                $location.path('/');
            }
        });

        $scope.updateUser = function(user) {
            UserResource.save({'id': user.id}, user,
                function (ret) {
                    Toaster.success("User Successfully Updated", 'Your changes were saved.');
                    $route.reload();
                },
                function (ret) {
                    Toaster.reqerror("User Update Failed", ret);
                }
            );
        };

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            $scope.userFilters.orderBy = $scope.predicate;
            $scope.userFilters.reverse = $scope.reverse ? true : null;
        };

        $scope.updateUserList = function() {
            UserResource.get($scope.userFilters).$promise.then(
                function(ret) {
                    $scope.users = ret.objects;
                    $scope.totalNumUsers = ret.total;
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve users.", ret);
                }
            );
        };
        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.search != newValue.search) {
                $scope.userFilters.page = 1;
            }
            if (oldValue.orderBy != newValue.orderBy) {
                $scope.userFilters.page = 1;
            }
            if(newValue.search === "") {
                $scope.userFilters.search = null;
            }
            xAPIStatementHelper.filtered_page($scope.userFilters);
            $scope.updateUserList();
        };
    }]
);

module.controller("UserCourseController",
    ['$scope', '$location', '$route', '$routeParams', 'UserResource', 'CourseResource', 'GroupResource', 'ClassListResource',
     'Toaster', 'breadcrumbs', 'Session', 'CourseRole', 'Authorize', 'xAPIStatementHelper', "moment",
    function($scope, $location, $route, $routeParams, UserResource, CourseResource, GroupResource, ClassListResource,
             Toaster, breadcrumbs, Session, CourseRole, Authorize, xAPIStatementHelper, moment) {

        var userId;
        $scope.user = {};
        $scope.totalNumCourses = 0;
        $scope.courseFilters = {
            page: 1,
            perPage: 20,
            search: null,
            orderBy: null,
            reverse: null
        };

        $scope.course_roles = [CourseRole.student, CourseRole.teaching_assistant, CourseRole.instructor];

        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;

            if ($scope.canManageUsers) {
                userId = $routeParams.userId;
                $scope.user = UserResource.get({'id': userId}, function (ret) {
                    breadcrumbs.options = {'Manage User Courses': "Manage {0}'s Courses".format(ret.fullname)};
                });

                $scope.updateCourseList();
                // register watcher here so that we start watching when all filter values are set
                $scope.$watchCollection('courseFilters', filterWatcher);
            } else {
                $location.path('/');
            }
        });

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            $scope.courseFilters.orderBy = $scope.predicate;
            $scope.courseFilters.reverse = $scope.reverse ? true : null;
        };

        $scope.updateCourseList = function() {
            var params = angular.merge({'id': userId}, $scope.courseFilters);
            UserResource.getUserCoursesById(params).$promise.then(
                function(ret) {
                    $scope.courses = ret.objects;
                    _.forEach($scope.courses, function(course) {
                        course.completed = course.end_date && moment().isAfter(course.end_date);
                        course.before_start = course.start_date && moment().isBefore(course.start_date);
                        course.in_progress = !(course.completed || course.before_start);

                        course.groups = [];
                        GroupResource.get({'courseId':course.id}).$promise.then(
                            function (ret) {
                                course.groups = ret.objects;
                            }
                        );
                    });
                    $scope.totalNumCourses = ret.total;
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve user's courses.", ret);
                }
            );
        };

        $scope.dropCourse = function(course) {
            ClassListResource.unenrol({'courseId': course.id, 'userId': userId},
                function (ret) {
                    Toaster.success("User Removed", "Successfully unenrolled " + ret.fullname + " from the course.");
                    $route.reload();
                },
                function (ret) {
                    Toaster.reqerror("User Not Removed", ret);
                }
            )
        };

        $scope.updateRole = function(course) {
            ClassListResource.enrol({'courseId': course.id, 'userId': userId}, course,
                function (ret) {
                    Toaster.success("User Added", 'Successfully changed '+ ret.fullname +'\'s course role to ' + ret.course_role);
                },
                function (ret) {
                    Toaster.reqerror("User Add Failed", "Problem encountered with " + course.name, ret);
                }
            );
        };

        $scope.updateGroup = function(course) {
            if (course.group_name && course.group_name != "") {
                GroupResource.enrol({'courseId': course.id, 'userId': userId, 'groupName': course.group_name}, {},
                    function (ret) {
                        Toaster.success("Update Complete", "Successfully added the user to group " + ret.group_name);
                    },
                    function (ret) {
                        Toaster.reqerror("Update Not Completed", ret);
                    }
                );
            } else {
                GroupResource.unenrol({'courseId': course.id, 'userId': userId},
                    function (ret) {
                        Toaster.success("User Removed", "Successfully removed the user from the group.");
                    },
                    function (ret) {
                        Toaster.reqerror("User Not Removed", ret);
                    }
                );
            }
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            if (oldValue.search != newValue.search) {
                $scope.courseFilters.page = 1;
            }
            if (oldValue.orderBy != newValue.orderBy) {
                $scope.courseFilters.page = 1;
            }
            if(newValue.search === "") {
                $scope.courseFilters.search = null;
            }
            xAPIStatementHelper.filtered_page($scope.courseFilters);
            $scope.updateCourseList();
        };
    }]
);

// End anonymous function
})();
