// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.classlist',
    [
        'ngResource',
        'ubc.ctlt.compair.attachment',
        'ubc.ctlt.compair.common.xapi',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.group',
        'ubc.ctlt.compair.toaster',
        'ubc.ctlt.compair.user',
        'ubc.ctlt.compair.login',
        'ubc.ctlt.compair.lti',
        'ubc.ctlt.compair.authorization',
        'ubc.ctlt.compair.oauth',
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
             "CourseRole", "GroupResource", "Toaster", "Session", "SaveAs", "LTIResource",
             "UserResource", "Authorize", "$modal", "xAPIStatementHelper",
    function($scope, $log, $routeParams, $route, ClassListResource, CourseResource,
             CourseRole, GroupResource, Toaster, Session, SaveAs, LTIResource,
             UserResource, Authorize, $modal, xAPIStatementHelper)
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
        Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;
        });
        Authorize.can(Authorize.CREATE, UserResource.MODEL).then(function (result) {
            $scope.canCreateUsers = result;
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
                Toaster.reqerror("No Course Found For Course ID "+courseId, ret);
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
        GroupResource.getAllFromSession({'courseId':courseId},
            function (ret) {
                $scope.groups = ret.objects;
            },
            function (ret) {
                Toaster.reqerror("Groups Retrieval Failed", ret);
            }
        );

		// enable checkbox to select/deselect all users
		$scope.selectAll = function() {
			angular.forEach($scope.classlist, function(user) {
				user.selected = $scope.selectedAll;
			});
		};
		$scope.checkIfAllSelected = function() {
			$scope.selectedAll = $scope.classlist.every(function(user) {
				return user.selected == true
			})
		};

        $scope.resetSelected = function() {
            angular.forEach($scope.classlist, function(user) {
                user.selected = false;
            });
        };

        $scope.course_roles = [CourseRole.student, CourseRole.teaching_assistant, CourseRole.instructor];

        $scope.addUsersToNewGroup = function() {
            var modalInstance = $modal.open({
                animation: true,
                backdrop: 'static',
                controller: "AddGroupModalController",
                templateUrl: 'modules/group/group-form-partial.html'
            })
            modalInstance.opened.then(function() {
                xAPIStatementHelper.opened_modal("Edit Group");
            });
            modalInstance.result.then(function (groupName) {
                $scope.addUsersToGroup(groupName);
                xAPIStatementHelper.closed_modal("Edit Group");
            }, function () {
                xAPIStatementHelper.closed_modal("Edit Group");
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
                        Toaster.success("Update Complete", "Successfully enrolled the user(s) into " + ret.group_name);
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("User(s) Not Enrolled", ret);
                    }
                );
            } else {
                GroupResource.removeUsersGroup({'courseId': courseId}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("User(s) Removed", "Successfully removed the user(s) from groups");
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("No User(s) Removed", ret);
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
                        Toaster.success("User(s) Updated", "Successfully changed course role to " + courseRole);
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("User(s) Not Updated", ret);
                    }
                );
            } else {
                ClassListResource.updateCourseRoles({'courseId': courseId}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("User(s) Removed", "Successfully removed user(s) from course.");
                        $route.reload();
                    },
                    function (ret) {
                        Toaster.reqerror("No User(s) Removed", ret);
                    }
                );
            }
        };

        $scope.update = function(userId, groupName) {
            if (groupName) {
                GroupResource.enrol({'courseId': courseId, 'userId': userId, 'groupName': groupName}, {},
                    function (ret) {
                        Toaster.success("Update Complete", "Successfully enrolled the user into " + ret.group_name);
                    },
                    function (ret) {
                        Toaster.reqerror("Update Not Completed", ret);
                    }
                );
            } else {
                GroupResource.unenrol({'courseId': courseId, 'userId': userId},
                    function (ret) {
                        Toaster.success("User Removed", "Successfully removed the user from the group.");
                    },
                    function (ret) {
                        Toaster.reqerror("User Not Removed", ret);
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
                    Toaster.reqerror("User Add Failed", ret);
                }
            );
        };

        $scope.unenrol = function(userId) {
            ClassListResource.unenrol({'courseId': courseId, 'userId': userId},
                function (ret) {
                    Toaster.success("User Removed", "Successfully unenrolled " + ret.fullname + " from the course.");
                    $route.reload();
                },
                function (ret) {
                    Toaster.reqerror("User Not Removed", ret);
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
                            Toaster.success("Enrolment Refreshed", "Successfully updated enrolment for the course.");
                            $route.reload();
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

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            var orderBy = $scope.predicate + " " + ($scope.reverse ? "desc" : "asc");
            xAPIStatementHelper.sorted_page_section("classlist table", orderBy);
        }
    }
]);

module.controller(
    'ClassImportController',
    ["$scope", "$log", "$location", "$routeParams", "ClassListResource", "CourseResource",
        "Toaster", "importService", "ThirdPartyAuthType", "AuthTypesEnabled",
    function($scope, $log, $location, $routeParams, ClassListResource, CourseResource,
             Toaster, importService, ThirdPartyAuthType, AuthTypesEnabled)
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
        $scope.ThirdPartyAuthType = ThirdPartyAuthType;
        $scope.importTypes = [];
        if (AuthTypesEnabled.cas) {
            $scope.importTypes.push({'value': ThirdPartyAuthType.cas, 'name': 'CWL username'})
        }
        if (AuthTypesEnabled.app) {
            $scope.importTypes.push({'value': null, 'name': 'ComPAIR username'})
        }

        // default value
        $scope.importType = $scope.importTypes[0].value;

        $scope.uploader = importService.getUploader(courseId, 'users');
        $scope.uploader.onCompleteItem = function(fileItem, response, status, headers) {
            $scope.submitted = false;
            importService.onComplete(courseId, response);
        };
        $scope.uploader.onBeforeUploadItem = function(fileItem) {
            if ($scope.importType == ThirdPartyAuthType.cas) {
                fileItem.formData.push({ 'import_type': $scope.importType });
            }
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
            $scope.user.course_role = $scope.course_role;
            ClassListResource.enrol({'courseId': courseId, 'userId': $scope.user.id}, $scope.user,
                function (ret) {
                    $scope.submitted = false;
                    Toaster.success("User Added", 'Successfully added '+ ret.fullname +' as ' + ret.course_role + ' to the course.');
                    $route.reload();
                },
                function (ret) {
                    $scope.submitted = false;
                    Toaster.reqerror("User Add Failed", "Problem encountered for ID " + $scope.user.id, ret);
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
