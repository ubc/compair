// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.group',
    [
        'ngResource',
        'ubc.ctlt.compair.attachment',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.login',
        'ubc.ctlt.compair.toaster',
        'ui.bootstrap'
    ]
);

/***** Providers *****/
module.factory(
    "GroupResource",
    ["$resource", "Interceptors",
    function ($resource, Interceptors)
    {
        var url = '/api/courses/:courseId/groups/:groupId';
        var ret = $resource(url, {groupId: '@id'},
            {
                get: {url: url, cache: true, interceptor: Interceptors.enrolCache},
                save: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
                delete: {method: 'DELETE', url: url, interceptor: Interceptors.enrolCache},
            }
        );

        ret.MODEL = 'Group';
        return ret;
    }
]);

module.factory(
    "GroupUserResource",
    ["$resource", "Interceptors",
    function ($resource, Interceptors)
    {
        var url = '/api/courses/:courseId/groups/:groupId/users/:userId';
        var removeUrl = '/api/courses/:courseId/groups/users/:userId';
        var getUrl = '/api/courses/:courseId/groups/user';
        var ret = $resource(url, {groupId: '@groupId'},
            {
                getCurrentUserGroup: {url: getUrl, cache: true, interceptor: Interceptors.enrolCache},
                add: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
                remove: {method: 'DELETE', url: removeUrl, interceptor: Interceptors.enrolCache},
                addUsersToGroup: {method: 'POST', url: url, interceptor: Interceptors.enrolCache},
                removeUsersFromGroup: {method: 'POST', url: removeUrl, interceptor: Interceptors.enrolCache},
            }
        );

        ret.MODEL = 'Group';
        return ret;
    }
]);

/***** Controllers *****/
module.controller(
    'AddGroupModalController',
    ["$rootScope", "$scope", "$uibModalInstance", "$filter", "Toaster", "GroupResource",
    function ($rootScope, $scope, $uibModalInstance, $filter, Toaster, GroupResource) {
        if ($scope.createNewGroup) {
            $scope.group = {};
        }
        $scope.modalInstance = $uibModalInstance;
        $scope.submitted = false;

        $scope.groupSubmit = function () {
            $scope.submitted = true;

            var groupNameExists = $filter('filter')($scope.groups, {'name':$scope.group.name, 'id': "!"+$scope.group.id}, true).length > 0;
            groupNameExists = false;

            if (groupNameExists) {
                Toaster.warning("Group Not Added", "The group name you have entered already exists. Please enter another group name and press Save.");
                $scope.submitted = false;
            }
            else {
                GroupResource.save({'courseId': $scope.courseId}, $scope.group).$promise.then(
                    function (ret) {
                        $scope.group = ret;
                        $uibModalInstance.close($scope.group.id);
                    }
                ).finally(function() {
                    $scope.submitted = false;
                });
            }
        };

        $scope.groupCancelEdit = function() {
            $scope.modalInstance.dismiss();
        }
    }
]);

module.controller(
    'ManageGroupsModalController',
    ["$rootScope", "$scope", "$uibModalInstance", "Toaster", "$uibModal", "GroupResource", "xAPIStatementHelper",
    function ($rootScope, $scope, $uibModalInstance, Toaster, $uibModal, GroupResource, xAPIStatementHelper) {
        $scope.group = {};
        $scope.modalInstance = $uibModalInstance;
        $scope.modalDone = function() {
            $scope.modalInstance.dismiss();
        };

        $scope.groupDelete = function(group_id) {
            $scope.submitted = true;
            GroupResource.delete({'courseId': $scope.courseId, 'groupId': group_id}).$promise
                .then(function(ret) {
                    return GroupResource.get({'courseId': $scope.courseId}).$promise;
                }, function(ret) {
                    return GroupResource.get({'courseId': $scope.courseId}).$promise;
                })
                .then(function(ret) {
                    $scope.groups = ret.objects;
                })
                .finally(function() {
                   $scope.submitted = false;
                });
        };

        $scope.groupEdit = function(group_id) {
            var modalScope = $scope.$new();
            var targetGroup = modalScope.groups.filter(function(group) {
                return group.id === group_id;
            });
            if (targetGroup.length == 0) {
                Toaster.warning("Group Not Found", "Problem editing the group.  Please reload the page and try again later.");
                return;
            }

            modalScope.courseId = $scope.courseId;
            modalScope.createNewGroup = false;
            // deep clone instead of using the same copy.
            // otherwise the group name will change behind the modal dialog as the user types the new name
            modalScope.group = $.extend(true, {}, targetGroup[0]);

            var modalInstance = $uibModal.open({
                animation: true,
                backdrop: 'static',
                controller: "AddGroupModalController",
                templateUrl: 'modules/group/group-modal-partial.html',
                scope: modalScope
            });
            var parentModal = $('.modal-content');

            modalInstance.opened.then(function() {
                parentModal.addClass('hidden');
                xAPIStatementHelper.opened_modal("Edit Group");
            });
            modalInstance.result.then(function (group_id) {
                // refresh groups
                GroupResource.get({'courseId': $scope.courseId}).$promise
                    .then(function(ret) {
                        $scope.groups = ret.objects;
                    });
                parentModal.removeClass('hidden');
                xAPIStatementHelper.closed_modal("Edit Group");
            }, function () {
                parentModal.removeClass('hidden');
                xAPIStatementHelper.closed_modal("Edit Group");
            });
        };
    }
]);

})();