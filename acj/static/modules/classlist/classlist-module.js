// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.classlist',
    [
        'ngResource',
        'ubc.ctlt.acj.attachment',
        'ubc.ctlt.acj.common.form',
        'ubc.ctlt.acj.common.interceptor',
        'ubc.ctlt.acj.course',
        'ubc.ctlt.acj.group',
        'ubc.ctlt.acj.toaster',
        'ubc.ctlt.acj.user',
        'ubc.ctlt.acj.lti',
        'ui.bootstrap',
        'fileSaver'
    ]
);

/***** Providers *****/
module.factory(
    "ClassListResource",
    ["$resource", "$cacheFactory", "Interceptors",
    function ($resource, $cacheFactory, Interceptors)
    {
        var url = '/api/courses/:courseId/users/:userId';
        var userRolesUrl = '/api/courses/:courseId/users/roles';
        var cache = $cacheFactory('classlist');
        var ret = $resource(
            url, {userId: '@userId'},
            {
                get: {cache: cache},
                enrol: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
                unenrol: {method: 'DELETE', url: url, interceptor: Interceptors.enrolCache},
                updateCourseRoles: {method: 'POST', url: userRolesUrl, interceptor: Interceptors.enrolCache},
                export: {
                    method: 'GET',
                    url: url,
                    headers: {Accept: 'text/csv'},
                    transformResponse: function (data, headers) {
                        // need to wrap response with object, otherwise $resource
                        // will try to decode response as json
                        return {content: data};
                    }
                }
            }
        );
        ret.MODEL = "UserCourse";
        return ret;
    }
]);

/***** Controllers *****/
module.controller(
    'ClassViewController',
    ["$scope", "$log", "$routeParams", "$route", "ClassListResource", "CourseResource",
             "CourseRole", "GroupResource", "Toaster", "Session", "SaveAs", "LTIResource", "$modal",
    function($scope, $log, $routeParams, $route, ClassListResource, CourseResource,
             CourseRole, GroupResource, Toaster, Session, SaveAs, LTIResource, $modal)
    {
        $scope.course = {};
        $scope.classlist = [];
        var courseId = $routeParams['courseId'];
        $scope.courseId = courseId;
        $scope.submitted = false;
        $scope.lti_membership_enabled = false;
        $scope.lti_membership_pending = 0;
        Session.getUser().then(function(user) {
            $scope.loggedInUserId = user.id;
        });
        CourseResource.get({'id':courseId},
            function (ret) {
                $scope.course_name = ret.name;
                if (ret.lti_linked) {
                    LTIResource.getMembershipStatus({id: courseId},
                        function(ret) {
                            $scope.lti_membership_enabled = ret.status.enabled;
                            $scope.lti_membership_pending = ret.status.pending;
                        },
                        function(ret) {
                            Toaster.reqerror("LTI Course Status Error", ret);
                        }
                    );
                }
            },
            function (ret) {
                Toaster.reqerror("No Course Found For ID "+courseId, ret);
            }
        );
        ClassListResource.get({'courseId':courseId},
            function (ret) {
                $scope.classlist = ret.objects;
                $scope.resetSelected();
            },
            function (ret) {
                Toaster.reqerror("No Users Found For Course ID "+courseId, ret);
            }
        );
        GroupResource.get({'courseId':courseId},
            function (ret) {
                $scope.groups = ret.objects;
            },
            function (ret) {
                Toaster.reqerror("Groups Retrieval Failed", ret);
            }
        );

        $scope.resetSelected = function() {
            angular.forEach($scope.classlist, function(user) {
                user.selected = false;
            });
        };

        $scope.course_roles = [CourseRole.student, CourseRole.teaching_assistant, CourseRole.instructor];

        $scope.addUsersToNewGroup = function() {
            modalInstance = $modal.open({
                animation: true,
                controller: "AddGroupModalController",
                templateUrl: 'modules/group/group-form-partial.html',
            }).result.then(function (groupName) {
                $scope.addUsersToGroup(groupName);
            }, function () {
                //cancelled, do nothing
            });
        };

        $scope.addUsersToGroup = function(groupName) {
            var selectedUserIds = $scope.classlist.filter(function(user) {
                return user.selected;
            }).map(function(user) {
                return user.id;
            });

            if (groupName == undefined) {
                groupName = null;
            }

            if (groupName) {
                GroupResource.updateUsersGroup({'courseId': courseId, 'groupName': groupName}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("Successfully enroled the users into " + ret.group_name);
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("Failed to enrol the users into the group.", ret);
                    }
                );
            } else {
                GroupResource.removeUsersGroup({'courseId': courseId}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("Successfully removed the users from groups");
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("Failed to enrol the users into the group.", ret);
                    }
                );
            }
        };

        $scope.updateUsers = function(courseRole) {
            var selectedUserIds = $scope.classlist.filter(function(user) {
                return user.selected;
            }).map(function(user) {
                return user.id;
            });

            if (courseRole) {
                ClassListResource.updateCourseRoles({'courseId': courseId}, {ids: selectedUserIds, course_role: courseRole},
                    function (ret) {
                        Toaster.success("Users Updated", 'Successfully changed users course role to ' + courseRole);
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("Failed to update users course roles", ret);
                    }
                );
            } else {
                ClassListResource.updateCourseRoles({'courseId': courseId}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("User Removed", 'Successfully removed users from course');
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("Failed to remove users from course", ret);
                    }
                );
            }
        };

        $scope.update = function(userId, groupName) {
            if (groupName) {
                GroupResource.enrol({'courseId': courseId, 'userId': userId, 'groupName': groupName}, {},
                    function (ret) {
                        Toaster.success("Successfully enroled the user into " + ret.group_name);
                    },
                    function (ret) {
                        Toaster.reqerror("Failed to enrol the user into the group.", ret);
                    }
                );
            } else {
                GroupResource.unenrol({'courseId': courseId, 'userId': userId},
                    function (ret) {
                        Toaster.success("Successfully removed the user from the group.");
                    },
                    function (ret) {
                        Toaster.reqerror("Failed to remove the user from the group.", ret);
                    }
                );
            }
        };

        $scope.enrol = function(user) {
            ClassListResource.enrol({'courseId': courseId, 'userId': user.id}, user,
                function (ret) {
                    Toaster.success("User Added", 'Successfully changed '+ ret.fullname +'\'s course role to ' + ret.course_role);
                },
                function (ret) {
                    Toaster.reqerror("User Add Failed For ID " + user.id, ret);
                }
            );
        };

        $scope.unenrol = function(userId) {
            ClassListResource.unenrol({'courseId': courseId, 'userId': userId},
                function (ret) {
                    Toaster.success("Successfully unenroled " + ret.fullname + " from the course.");
                    $route.reload();
                },
                function (ret) {
                    Toaster.reqerror("Failed to unerol the user from the course.", ret);
                }
            )
        };

        $scope.updateLTIMembership = function() {
            $scope.submitted = true;
            LTIResource.updateMembership({id: courseId}, {},
                function(ret) {
                    $scope.submitted = false;
                    ClassListResource.get({'courseId':courseId},
                        function (ret) {
                            Toaster.success("Successfully updated enrolment from the course.");
                            $scope.classlist = ret.objects;
                        },
                        function (ret) {
                            Toaster.reqerror("No Users Found For Course ID "+courseId, ret);
                        }
                    );
                },
                function(ret) {
                    $scope.submitted = false;
                    Toaster.reqerror("LTI Update Course Membership Error", ret);
                }
            );
        };

        $scope.export = function() {
            ClassListResource.export({'courseId': courseId}, function(ret) {
                SaveAs.download(ret.content, 'classlist_'+$scope.course_name+'.csv', {type: "text/csv;charset=utf-8"});
            });
        };
    }
]);

module.controller(
    'ClassImportController',
    ["$scope", "$log", "$location", "$routeParams", "ClassListResource", "CourseResource", "Toaster", "importService",
    function($scope, $log, $location, $routeParams, ClassListResource, CourseResource, Toaster, importService)
    {
        $scope.course = {};
        var courseId = $routeParams['courseId'];
        CourseResource.get({'id':courseId},
            function (ret) {
                $scope.course_name = ret['name'];
            },
            function (ret) {
                Toaster.reqerror("No Course Found For ID "+courseId, ret);
            }
        );
        $scope.uploader = importService.getUploader(courseId, 'users');
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
    'ClassImportResultsController',
    ["$scope", "$log", "$routeParams", "ClassListResource", "Toaster", "importService",
    function($scope, $log, $routeParams, ClassListResource, Toaster, importService)
    {
        $scope.results = importService.getResults();

        $scope.course = {};
        $scope.courseId = $routeParams['courseId'];
        $scope.headers = ['Username', 'Student Number', 'First Name', 'Last Name', 'Email', 'Message'];
    }
]);

module.controller(
    'EnrolController',
    ["$scope", "$log", "$routeParams", "$route", "$location", "ClassListResource", "Toaster", "UserResource",
    function($scope, $log, $routeParams, $route, $location, ClassListResource, Toaster, UserResource)
    {
        var courseId = $routeParams['courseId'];

        $scope.enrolSubmit = function() {
            $scope.submitted = true;
            ClassListResource.enrol({'courseId': courseId, 'userId': $scope.user.id}, $scope.user,
                function (ret) {
                    $scope.submitted = false;
                    Toaster.success("User Added", 'Successfully added '+ ret.fullname +' as ' + ret.course_role + ' to the course.');
                    $route.reload();
                },
                function (ret) {
                    $scope.submitted = false;
                    Toaster.reqerror("User Add Failed For ID " + $scope.user.id, ret);
                }
            );
        };

        $scope.getUsersAhead = function(search) {
            // need return a real promise so can't use short form (without $promise.then)
            return UserResource.get({search: search}).$promise.then(function(response) {
                return response.objects;
            });
        }
    }
]);

// End anonymous function
})();
