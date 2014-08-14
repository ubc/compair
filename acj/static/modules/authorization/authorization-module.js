// Use this module to check if a user has permission for certain functions

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.authorization', 
	[
		'ngCookies',
        'ubc.ctlt.acj.session'
	]
);

/***** Providers *****/
// normally, there would be a "Service" at the end of the name, but it seems
// too much to type if it's going to be used a lot
module.factory('Authorize',
	function($log, $q, $cookieStore, Session)
	{
		var _allow_operation = function(operation, resource, permissions) {
			$log.debug(permissions);
			if (resource in permissions)
			{
				if (operation in permissions[resource])
				{
					return permissions[resource][operation];
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
			can: function(operation, resource) {
				return Session.getUser().then(function(user) {
                    if (user == null) {
                        return $q.when(false);
                    }

                    if (user.usertypeforsystem.name == "System Administrator")
                    {
                        return $q.when(true);
                    }

                    return Session.getPermissions().then(function(permissions) {
                        return $q.when(_allow_operation(operation, resource, permissions));
                    });
                });
			}
		};
	}
);

/***** Controllers *****/
// module.controller(...)

// End anonymous function
})();
