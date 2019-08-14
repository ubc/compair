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
    'ubc.ctlt.compair.login',
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
        updateNotifcations: {method: 'POST', url: '/api/users/:id/notification'},
        password: {method: 'POST', url: '/api/users/:id/password'}
    });
    User.MODEL = "User";

    User.prototype.isLoggedIn = function() {
        return this.hasOwnProperty('id');
    };

    return User;
}]);

module.factory('UserLTIUsersResource', ['$resource', function($resource) {
    var UserLTIUsers = $resource('/api/users/:id/lti/users', {id: '@id'}, {
        deleteById: { method: 'DELETE',  url: '/api/users/:id/lti/users/:ltiUserId'},
    });
    UserLTIUsers.MODEL = "User";

    return UserLTIUsers;
}]);

module.factory('UserThirdPartyUsersResource', ['$resource', function($resource) {
    var UserThirdPartyUsers = $resource('/api/users/:id/third_party/users', {id: '@id'}, {
        deleteById: { method: 'DELETE',  url: '/api/users/:id/third_party/users/:thirdPartyUserId'},
    });
    UserThirdPartyUsers.MODEL = "User";

    return UserThirdPartyUsers;
}]);

module.constant('UserSettings', {
    notifications: false,
    expose_email_to_instructor: false,
    allow_student_change_name: true,
    allow_student_change_display_name: true,
    allow_student_change_student_number: true,
    allow_student_change_email: true
});

module.constant('SystemRole', {
    student: "Student",
    instructor: "Instructor",
    sys_admin: "System Administrator"
});

module.constant('EmailNotificationMethod', {
    enable: "enable",
    disable: "disable",
    //digest: "digest"
});

module.constant('CourseRole', {
    dropped: "Dropped",
    instructor: "Instructor",
    teaching_assistant: "Teaching Assistant",
    student: "Student"
});

/***** Controllers *****/
module.controller("UserWriteController",
    ['$scope', '$route', '$routeParams', '$location', 'breadcrumbs', 'Session',
     'AuthTypesEnabled', 'UserResource', 'SystemRole', 'Toaster', 'resolvedData',
     'UserSettings', 'EmailNotificationMethod', "$uibModal",
    function($scope, $route, $routeParams, $location, breadcrumbs, Session,
             AuthTypesEnabled, UserResource, SystemRole, Toaster, resolvedData,
             UserSettings, EmailNotificationMethod, $uibModal)
    {
        $scope.userId = $routeParams.userId;
        $scope.saveAttempted = false;
        $scope.duplicateUsername = false;
        $scope.duplicateStudentNumber = false;

        $scope.user = resolvedData.user || {};
        $scope.canManageUsers = resolvedData.canManageUsers;
        $scope.loggedInUser = resolvedData.loggedInUser;
        $scope.ownProfile = $scope.loggedInUser.id == $scope.userId;
        $scope.loggedInUserIsStudent = $scope.loggedInUser.system_role == SystemRole.student;

        $scope.method = $scope.user.id ? 'edit' : 'create';
        $scope.password = {};

        $scope.UserSettings = UserSettings;
        $scope.EmailNotificationMethod = EmailNotificationMethod;
        $scope.AuthTypesEnabled = AuthTypesEnabled;
        $scope.SystemRole = SystemRole;
        $scope.system_roles = [SystemRole.student, SystemRole.instructor, SystemRole.sys_admin]
        // remove system admin from system roles if current_user is not an admin
        if (!$scope.canManageUsers) {
            $scope.system_roles.pop()
        }

        if ($scope.method == 'edit') {
            breadcrumbs.options = {'View User': "{0}'s Profile".format($scope.user.displayname)};
        } else if ($scope.method == 'create') {
            $scope.user.uses_compair_login = true;
            $scope.user.email_notification_method = EmailNotificationMethod.enable;
            $scope.user.system_role = SystemRole.student;
        }

        $scope.showErrors = function($event, formValid) {

            // show error if invalid form or missing times or course start/end date/time mismatch
            if (!formValid) {
                
                // don't submit
                $event.preventDefault();
                
                // set helper text and Toast
                $scope.helperMsg = "Sorry, this user couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this user couldn't be saved yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";
                
                // display messages
                $scope.saveAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);
            
            }
            
        };
        
        $scope.save = function() {
            $scope.submitted = true;

            UserResource.save({'id': $scope.userId}, $scope.user, function(ret) {
                if ($scope.method == 'edit') {
                    Toaster.success('User Saved');
                } else if ($scope.method == 'create') {
                    Toaster.success('User Saved', 'This user now has access to ComPAIR.');
                }
                // refresh User's info on editing own profile and displayname changed
                if ($scope.ownProfile && $scope.user.displayname != $scope.loggedInUser.displayname) {
                    Session.refresh();
                }
                $location.path('/user/' + ret.id);
            }).$promise.then(function() {
                $scope.submitted = false;
            }, function(ret) {
                $scope.submitted = false;
                if (ret.status == "409") {
                    
                    // handle cases where username is a duplicate
                    if (ret.data.message.includes("username")) {
                        $scope.problemUsername = $scope.user.username;
                        $scope.duplicateUsername = true;
                    }
                    
                    // handle cases where student number is a duplicate
                    if (ret.data.message.includes("student number")) {
                        $scope.problemStudentNumber = $scope.user.student_number;
                        $scope.duplicateStudentNumber = true;
                    }
                    
                    $scope.saveAttempted = true;
                    $scope.helperMsg = "Sorry, this user couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";

                }
            });
            
        };

        $scope.showPasswordModal = function() {
            var modalScope = $scope.$new();
            modalScope.user = angular.copy($scope.user);

            $scope.modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "UserPasswordModalController",
                templateUrl: 'modules/user/user-password-modal-partial.html',
                scope: modalScope
            });
        };
    }]
);

module.controller(
    "UserPasswordModalController",
    ['$scope', 'UserResource', 'Toaster', "$uibModalInstance",
    function ($scope, UserResource, Toaster, $uibModalInstance)
    {
        $scope.modalInstance = $uibModalInstance;
        $scope.submitted = false;
        $scope.password = {};
        $scope.saveModalAttempted = false;
        $scope.incorrectPassword = false;
        
        $scope.showErrors = function($event, formValid) {

            // show errors if invalid form
            if (!formValid) {
                
                // don't submit
                $event.preventDefault();
                
                // set helper text and Toast
                $scope.helperMsg = "Sorry, this password couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this password couldn't be saved yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";
                
                // display messages
                $scope.saveModalAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);
            
            }
            
        };

        $scope.changePassword = function() {
            $scope.submitted = true;
            UserResource.password({'id': $scope.user.id}, $scope.password, function (ret) {
                Toaster.success("Password Saved");
                $scope.modalInstance.close();
                $scope.password = {};
            }).$promise.then(function() {
                $scope.submitted = false;
            }, function(ret) {
                $scope.submitted = false;
                if (ret.status == "400") {
                    
                    // handle cases where old password is incorrect
                    if (ret.data.message.includes("not correct")) {
                        $scope.problemPassword = $scope.password.oldpassword;
                        $scope.incorrectPassword = true;
                    }
                    
                    $scope.saveModalAttempted = true;
                    $scope.helperMsg = "Sorry, this password couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                }
            });
        };
    }]
);

module.controller("UserViewController",
    ['$scope', '$routeParams', 'breadcrumbs', 'SystemRole', 'resolvedData',
     'UserResource', 'UserSettings', 'EmailNotificationMethod', 'Toaster', '$route',
    function($scope, $routeParams, breadcrumbs, SystemRole, resolvedData,
             UserResource, UserSettings, EmailNotificationMethod, Toaster, $route)
    {
        $scope.userId = $routeParams.userId;

        $scope.user = resolvedData.user;
        $scope.showEditButton = resolvedData.userEditButton;
        $scope.canManageUsers = resolvedData.canManageUsers;
        $scope.loggedInUser = resolvedData.loggedInUser;
        $scope.ownProfile = $scope.loggedInUser.id == $scope.userId;
        $scope.loggedInUserIsInstructor = $scope.loggedInUser.system_role == SystemRole.instructor;
        $scope.UserSettings = UserSettings;
        $scope.EmailNotificationMethod = EmailNotificationMethod;

        $scope.SystemRole = SystemRole;
        breadcrumbs.options = {'View User': "{0}'s Profile".format($scope.user.displayname)};

        $scope.updateNotificationSettings = function() {
            $scope.submitted = true;

            UserResource.updateNotifcations({'id': $scope.userId}, $scope.user, function(ret) {
                Toaster.success('Notifications Saved');
            }).$promise.catch(function() {
                // if update failed, refresh the page to show correct status
                $route.reload();
            }).finally(function() {
                $scope.submitted = false;
            });
        };
    }]
);

module.controller("UserListController",
    ['$scope', '$location', 'UserResource', 'Toaster', 'breadcrumbs', 'SystemRole',
     'LearningRecordStatementHelper', 'resolvedData',
    function($scope, $location, UserResource, Toaster, breadcrumbs, SystemRole,
             LearningRecordStatementHelper, resolvedData)
    {
        $scope.loggedInUserId = resolvedData.loggedInUser.id;
        $scope.canManageUsers = resolvedData.canManageUsers;

        $scope.predicate = 'lastname';
        $scope.reverse = false;
        $scope.users = [];
        $scope.totalNumUsers = 0;
        $scope.userFilters = {
            page: 1,
            perPage: 20,
            search: null,
            orderBy: null,
            reverse: null
        };

        // redirect user if doesn't have permission to view page
        if (!$scope.canManageUsers) {
            $location.path('/');
        }

        $scope.updateUser = function(user) {
            UserResource.save({'id': user.id}, user,
                function (ret) {
                    Toaster.success("User Saved");
                    $route.reload();
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
                }
            );
        };
        $scope.updateUserList();

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
            LearningRecordStatementHelper.filtered_page($scope.userFilters);
            $scope.updateUserList();
        };
        $scope.$watchCollection('userFilters', filterWatcher);
    }]
);

module.controller("UserManageController",
    ['$scope', '$location', '$route', '$routeParams', 'UserResource', 'CourseResource', 'GroupResource',
     'UserLTIUsersResource', 'UserThirdPartyUsersResource', 'ClassListResource', 'Toaster', 'breadcrumbs',
     'CourseRole', 'AuthTypesEnabled', 'LearningRecordStatementHelper', "moment", "resolvedData", 'GroupUserResource',
    function($scope, $location, $route, $routeParams, UserResource, CourseResource, GroupResource,
             UserLTIUsersResource, UserThirdPartyUsersResource, ClassListResource, Toaster, breadcrumbs,
             CourseRole, AuthTypesEnabled, LearningRecordStatementHelper, moment, resolvedData, GroupUserResource)
    {
        $scope.userId = $routeParams.userId;

        $scope.user = resolvedData.user;
        $scope.canManageUsers = resolvedData.canManageUsers;

        $scope.totalNumCourses = 0;
        $scope.courseFilters = {
            page: 1,
            perPage: 20,
            search: null,
            orderBy: null,
            reverse: null,
            includeSandbox: null
        };

        $scope.third_party_users = resolvedData.userThirdPartyUsers.objects;
        $scope.lti_users = resolvedData.userLTIs.objects;
        $scope.AuthTypesEnabled = AuthTypesEnabled;

        breadcrumbs.options = {'User Courses & Accounts': "{0}'s Courses & Accounts".format($scope.user.displayname)};
        $scope.course_roles = [CourseRole.student, CourseRole.teaching_assistant, CourseRole.instructor];

        if (!$scope.canManageUsers) {
            $location.path('/');
        }

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            $scope.courseFilters.orderBy = $scope.predicate;
            $scope.courseFilters.reverse = $scope.reverse ? true : null;
        };

        $scope.updateCourseList = function() {
            var params = angular.merge({'id': $scope.userId}, $scope.courseFilters);
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
                }
            );
        };
        $scope.updateCourseList();

        $scope.dropCourse = function(course) {
            ClassListResource.unenrol({'courseId': course.id, 'userId': $scope.userId},
                function (ret) {
                    Toaster.success("User Dropped");
                    $route.reload();
                }
            )
        };

        $scope.updateRole = function(course) {
            ClassListResource.enrol({'courseId': course.id, 'userId': $scope.userId}, course,
                function (ret) {
                    Toaster.success("User Saved", 'Successfully changed the user\'s course role to ' + ret.course_role + ".");
                }
            );
        };

        $scope.updateGroup = function(course) {
            if (course.group_id && course.group_id != "") {
                GroupUserResource.add({'courseId': course.id, 'userId': $scope.userId, 'groupId': course.group_id}, {},
                    function (ret) {
                        Toaster.success("User Saved", "Successfully added the user to group " + ret.name+".");
                    }
                );
            } else {
                GroupUserResource.remove({'courseId': course.id, 'userId': $scope.userId},
                    function (ret) {
                        Toaster.success("User Removed From Group");
                    }
                );
            }
        };

        $scope.unlinkLTI = function(lti_user) {
            var params = {
                id: $scope.userId,
                ltiUserId: lti_user.id,
            }
            UserLTIUsersResource.deleteById(params).$promise.then(
                function (ret) {
                    Toaster.success("LTI Unlink", "Successfully unlinked the LTI user as requested.");
                    $route.reload();
                }
            );
        }

        $scope.deleteThirdPartyUser = function(third_party_user) {
            var params = {
                id: $scope.userId,
                thirdPartyUserId: third_party_user.id,
            }
            UserThirdPartyUsersResource.deleteById(params).$promise.then(
                function (ret) {
                    Toaster.success("Third Party User Delete", "Successfully deleted the third party user as requested.");
                    $route.reload();
                }
            );
        }

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
            LearningRecordStatementHelper.filtered_page($scope.courseFilters);
            $scope.updateCourseList();
        };
        $scope.$watchCollection('courseFilters', filterWatcher);
    }]
);

// End anonymous function
})();
