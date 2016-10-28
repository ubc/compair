// Use this module to check if a user has permission for certain functions

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.authorization',
    [
        'ubc.ctlt.compair.session'
    ]
);

/***** Providers *****/
// normally, there would be a "Service" at the end of the name, but it seems
// too much to type if it's going to be used a lot
module.factory('Authorize',
    ["$log", "$q", "Session",
    function($log, $q, Session)
    {
        var _allow_operation = function(operation, resource, courseId, permissions) {
            if (resource in permissions)
            {
                if (operation in permissions[resource])
                {
                    if (courseId in permissions[resource][operation]) {
                        return permissions[resource][operation][courseId];
                    }
                }
            }
            return false;
        };

        return {
            MANAGE: "manage",
            CREATE: "create",
            READ: "read",
            EDIT: "edit",
            DELETE: "delete",
            can: function(operation, resource, courseId) {
                return Session.getUser().then(function(user) {
                    if (user == null) {
                        return $q.when(false);
                    }

                    if (user.system_role == "System Administrator")
                    {
                        return $q.when(true);
                    }

                    return Session.getPermissions().then(function(permissions) {
                        var course_id = courseId || 'global';
                        return $q.when(_allow_operation(operation, resource, course_id, permissions));
                    });
                });
            }
        };
    }
]);

/***** Controllers *****/
// module.controller(...)

// End anonymous function
})();