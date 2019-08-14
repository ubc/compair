// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.classlist',
    [
        'ngResource',
        'ubc.ctlt.compair.attachment',
        'ubc.ctlt.compair.learning_records.learning_record',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.group',
        'ubc.ctlt.compair.toaster',
        'ubc.ctlt.compair.user',
        'ubc.ctlt.compair.login',
        'ubc.ctlt.compair.lti',
        'ubc.ctlt.compair.authorization',
        'ui.bootstrap',
        'ngFileSaver'
    ]
);

module.constant('ThirdPartyAuthType', {
    cas: "CAS",
    saml: 'SAML'
});

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
    ["$scope", "$routeParams", "$route", "ClassListResource", "CourseResource", "GroupUserResource",
             "CourseRole", "GroupResource", "Toaster", "FileSaver", "Blob", "LTIResource",
             "UserResource", "$uibModal", "LearningRecordStatementHelper", "resolvedData",
    function($scope, $routeParams, $route, ClassListResource, CourseResource, GroupUserResource,
             CourseRole, GroupResource, Toaster, FileSaver, Blob, LTIResource,
             UserResource, $uibModal, LearningRecordStatementHelper, resolvedData)
    {

        $scope.courseId = $routeParams.courseId;

        $scope.course = resolvedData.course;
        $scope.classlist = resolvedData.classlist.objects;
        $scope.groups = resolvedData.groups.objects;
        $scope.loggedInUserId = resolvedData.loggedInUser.id;
        $scope.canManageUsers = resolvedData.canManageUsers;
        $scope.canCreateUsers = resolvedData.canCreateUsers;

        $scope.submitted = false;
        $scope.lti_membership_enabled = false;
        $scope.lti_membership_pending = 0;
        $scope.course_roles = [CourseRole.student, CourseRole.teaching_assistant, CourseRole.instructor];

        $scope.groupAddOptions = Array( {'id':'-1',  'name':'--------------------', 'disabled':true},
                                        {'id':'add', 'name':'Add new group'},
                                        {'id':'manage', 'name':'Manage group names'});
        $scope.bulkGroupAddOptions = Array( {'id':'-1',  'name':'--------------------', 'disabled':true},
                                            {'id':'manage', 'name':'Manage group names'});

        if ($scope.course.lti_linked) {
            LTIResource.getMembershipStatus({id: $scope.courseId},
                function(ret) {
                    $scope.lti_membership_enabled = ret.status.enabled;
                    $scope.lti_membership_pending = ret.status.pending;
                }
            );
        }

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

        $scope.addUsersToNewGroup = function() {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.createNewGroup = true;

            var modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "AddGroupModalController",
                templateUrl: 'modules/group/group-modal-partial.html',
                scope: modalScope
            });

            modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal("Edit Group");
            });
            modalInstance.result.then(function (groupName) {
                $scope.addUsersToGroup(groupName);
                LearningRecordStatementHelper.closed_modal("Edit Group");
            }, function () {
                LearningRecordStatementHelper.closed_modal("Edit Group");
            });
        };

         $scope.manageGroups = function() {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;

            var modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "ManageGroupsModalController",
                templateUrl: 'modules/group/groups-manage-modal-partial.html',
                scope: modalScope
            });

            modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal("Edit Group");
            });
            modalInstance.result.finally(function () {
                // refresh groups
                GroupResource.get({'courseId': modalScope.courseId}).$promise
                    .then(function(ret) {
                        $scope.groups = ret.objects;
                    });
                LearningRecordStatementHelper.closed_modal("Edit Group");
            });
        };

        $scope.addUsersToGroup = function(group_id) {
            var selectedUserIds = $scope.classlist.filter(function(user) {
                return user.selected;
            }).map(function(user) {
                return user.id;
            });

            if (group_id == undefined) {
                group_id = null;
            }

            if (group_id) {
                GroupUserResource.addUsersToGroup({'courseId': $scope.courseId, 'groupId': group_id}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("User(s) Saved", "Successfully added the user(s) into " + ret.name + ".");
                        $route.reload();
                    }
                );
            } else {
                GroupUserResource.removeUsersFromGroup({'courseId': $scope.courseId}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("User(s) Removed From Group");
                        $route.reload();
                    }
                );
            }
        };

        $scope.bulkGroupSelected = function(group_id) {
            if (group_id == 'manage') {
                $scope.selectedGroup = "";
                $scope.manageGroups();
            }
        };

        $scope.updateUsers = function(courseRole) {
            var selectedUserIds = $scope.classlist.filter(function(user) {
                return user.selected;
            }).map(function(user) {
                return user.id;
            });

            if (courseRole) {
                ClassListResource.updateCourseRoles({'courseId': $scope.courseId}, {ids: selectedUserIds, course_role: courseRole},
                    function (ret) {
                        Toaster.success("User(s) Saved", "Successfully changed course role to " + courseRole + ".");
                        $route.reload();
                    }
                );
            } else {
                ClassListResource.updateCourseRoles({'courseId': $scope.courseId}, {ids: selectedUserIds},
                    function (ret) {
                        Toaster.success("User(s) Dropped");
                        $route.reload();
                    }
                );
            }
        };

        $scope.addUserToNewGroup = function(user) {
            var modalScope = $scope.$new();
            modalScope.courseId = $scope.courseId;
            modalScope.groups = $scope.groups;
            modalScope.createNewGroup = true;

            var modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "AddGroupModalController",
                templateUrl: 'modules/group/group-modal-partial.html',
                scope: modalScope
            });

            modalInstance.opened.then(function() {
                LearningRecordStatementHelper.opened_modal("Edit Group");
            });
            modalInstance.result.then(function (group_id) {
                user.group_id = group_id;
                $scope.updateGroup(user, true);
                LearningRecordStatementHelper.closed_modal("Edit Group");
            }, function () {
                LearningRecordStatementHelper.closed_modal("Edit Group");
            });
        };

        $scope.updateGroup = function(user, reload, original_group_id) {
            if (user.group_id == 'add') {
                $scope.createNewGroup = true;
                $scope.addUserToNewGroup(user);
                user.group_id = original_group_id;
            } else if (user.group_id == 'manage') {
                $scope.manageGroups();
                user.group_id = original_group_id;
            } else if (user.group_id) {
                GroupUserResource.add({'courseId': $scope.courseId, 'userId': user.id, 'groupId': user.group_id}, {},
                    function (ret) {
                        Toaster.success("User Saved", "Successfully added the user to group " + ret.name + ".");
                        if (reload) {
                            $route.reload();
                        }
                    },
                    function (ret) {
                        // will reset the changed group_id in the select
                        $route.reload();
                    }
                );
            } else {
                GroupUserResource.remove({'courseId': $scope.courseId, 'userId': user.id},
                    function (ret) {
                        Toaster.success("User Removed From Group");
                    },
                    function (ret) {
                        // will reset the changed group_id in the select
                        $route.reload();
                    }
                );
            }
        };

        $scope.enrol = function(user) {
            ClassListResource.enrol({'courseId': $scope.courseId, 'userId': user.id}, user,
                function (ret) {
                    Toaster.success("User Saved", 'Successfully changed '+ ret.fullname +'\'s course role to ' + ret.course_role + ".");
                }
            );
        };

        $scope.unenrol = function(userId) {
            ClassListResource.unenrol({'courseId': $scope.courseId, 'userId': userId},
                function (ret) {
                    Toaster.success("User Dropped");
                    $route.reload();
                }
            )
        };

        $scope.updateLTIMembership = function() {
            $scope.submitted = true;
            LTIResource.updateMembership({id: $scope.courseId}, {},
                function(ret) {
                    $scope.submitted = false;
                    ClassListResource.get({'courseId':$scope.courseId},
                        function (ret) {
                            Toaster.success("Enrollment List Refreshed", "This page now shows the most up-to-date enrollment for your course.");
                            $route.reload();
                        }
                    );
                },
                function(ret) {
                    $scope.submitted = false;
                }
            );
        };

        $scope.export = function() {
            ClassListResource.export({'courseId': $scope.courseId}, function(ret) {
                var data = new Blob([ret.content], { type: "text/csv;charset=utf-8" });
                FileSaver.saveAs(data, 'classlist_'+$scope.course.name+'.csv');
            });
        };

        $scope.updateTableOrderBy = function(predicate) {
            $scope.reverse = $scope.predicate == predicate && !$scope.reverse;
            $scope.predicate = predicate;
            var orderBy = $scope.predicate + " " + ($scope.reverse ? "desc" : "asc");
            LearningRecordStatementHelper.sorted_page_section("classlist table", orderBy);
        };
        $scope.resetSelected();
    }
]);

module.controller(
    'ClassImportController',
    ["$scope", "$routeParams", "ClassListResource", "CourseResource",
        "Toaster", "importService", "ThirdPartyAuthType", "AuthTypesEnabled", "resolvedData",
    function($scope, $routeParams, ClassListResource, CourseResource,
             Toaster, importService, ThirdPartyAuthType, AuthTypesEnabled, resolvedData)
    {
        $scope.courseId = $routeParams['courseId'];
        $scope.course = resolvedData.course;

        $scope.ThirdPartyAuthType = ThirdPartyAuthType;
        $scope.importTypes = [];
        //only allow one import type between CAS and SAML (priority given to SAML)
        if (AuthTypesEnabled.saml) {
            $scope.importTypes.push({'value': ThirdPartyAuthType.saml, 'name': 'CWL username'})
        } else if (AuthTypesEnabled.cas) {
            $scope.importTypes.push({'value': ThirdPartyAuthType.cas, 'name': 'CWL username'})
        }
        if (AuthTypesEnabled.app) {
            $scope.importTypes.push({'value': null, 'name': 'ComPAIR username'})
        }

        // default value
        $scope.importType = $scope.importTypes[0].value;

        $scope.uploader = importService.getUploader($scope.courseId, 'users');
        $scope.uploader.onCompleteItem = function(fileItem, response, status, headers) {
            $scope.submitted = false;
            importService.onComplete($scope.courseId, response);
        };
        $scope.uploader.onBeforeUploadItem = function(fileItem) {
            if ($scope.importType == ThirdPartyAuthType.cas || $scope.importType == ThirdPartyAuthType.saml) {
                fileItem.formData.push({ 'import_type': $scope.importType });
            }
        };

        $scope.upload = function() {
            $scope.submitted = true;
            $scope.uploader.uploadAll();
        };
    }
]);

module.controller(
    'ClassImportResultsController',
    ["$scope", "$routeParams", "ClassListResource", "Toaster", "importService", "resolvedData",
    function($scope, $routeParams, ClassListResource, Toaster, importService, resolvedData)
    {
        $scope.results = importService.getResults();

        $scope.courseId = $routeParams['courseId'];
        $scope.headers = ['Username', 'Student Number', 'First Name', 'Last Name', 'Email', 'Reason'];
    }
]);

module.component('enrolComponent', {
    controller: 'EnrolController',
    templateUrl: 'modules/classlist/classlist-enrol-partial.html',
    bindings: {
        courseId: '<'
    }
});

module.controller(
    'EnrolController',
    ["$route", "ClassListResource", "Toaster", "UserResource", "CourseRole",
    function($route, ClassListResource, Toaster, UserResource, CourseRole)
    {
        var ctrl = this;
        //ctrl.courseId

        ctrl.course_roles = [CourseRole.student, CourseRole.teaching_assistant, CourseRole.instructor];

        ctrl.enrolSubmit = function() {
            ctrl.submitted = true;
            ctrl.user.course_role = ctrl.course_role;
            ClassListResource.enrol({'courseId': ctrl.courseId, 'userId': ctrl.user.id}, ctrl.user).$promise.then(
                function (ret) {
                    Toaster.success("User Enrolled", 'Successfully enrolled '+ ret.fullname +' as ' + ret.course_role + ' in the course.');
                    $route.reload();
                }
            ).finally(function() {
                ctrl.submitted = false;
            });
        };

        ctrl.getUsersAhead = function(search) {
            // need return a real promise so can't use short form (without $promise.then)
            return UserResource.get({search: search}).$promise.then(function(response) {
                return response.objects;
            });
        }
    }
]);

// End anonymous function
})();
