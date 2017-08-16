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
    ["$q", "Session",
    function($q, Session)
    {
        var _allow_operation = function(operation, resource, resource_scope, permissions) {
            if (resource in permissions)
            {
                if (resource_scope in permissions[resource]) {
                    return permissions[resource][resource_scope].indexOf(operation) != -1;
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
                        var resource_scope = courseId || 'global';
                        return $q.when(_allow_operation(operation, resource, resource_scope, permissions));
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