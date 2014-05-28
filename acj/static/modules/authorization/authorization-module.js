// Use this module to check if a user has permission for certain functions

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.authorization', 
	[
		'ngCookies',
		'ubc.ctlt.acj.authentication'
	]
);

/***** Providers *****/
// normally, there would be a "Service" at the end of the name, but it seems
// too much to type if it's going to be used a lot
module.factory('Authorize',
	function($log, $q, $cookieStore, AuthenticationService)
	{
		var _permissions = null;

		var _allow_operation = function(operation, resource, permissions) {
			if (resource in permissions)
			{
				if (operation in permissions[resource])
				{
					$log.debug("Here");
					$log.debug(resource);
					$log.debug(operation);
					$log.debug(permissions[resource]);
					$log.debug(permissions[resource][operation]);
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
			storePermissions: function(permissions) {
				_permissions = permissions;
				$cookieStore.put('current.permissions', permissions);
				$log.debug("Stored Permissions");
				$log.debug(_permissions);
			},
			getPermissions: function() {
				if (_permissions)
				{
					return _permissions;
				}
				var cookie_permissions = $cookieStore.get('current.permissions');
				if (cookie_permissions)
				{
					_permissions = cookie_permissions;
					return _permissions;
				}
				$log.error("Stored permissions not found!");
				return null;
			},
			can: function(operation, resource) {
				if (!AuthenticationService.isAuthenticated())
				{
					// in case of logout, we should clear permissions
					_permissions = null;
					return false;
				}
				user = AuthenticationService.getUser()
				if (user.usertypeforsystem.name == "System Admin")
				{
					return true;
				}
				var permissions = this.getPermissions();
				return _allow_operation(operation, resource, permissions);
			}
		};
	}
);

/***** Controllers *****/
// module.controller(...)

// End anonymous function
})();
