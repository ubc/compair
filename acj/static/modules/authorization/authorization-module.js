// Use this module to check if a user has permission for certain functions

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.authorization', 
	[
		'ngResource',
		'ubc.ctlt.acj.authentication'
	]
);

/***** Providers *****/
module.factory('AuthorizationResource',
	function($resource)
	{
		return $resource('/api/authorization');
	}
);

// normally, there would be a "Service" at the end of the name, but it seems
// too much to type if it's going to be used a lot
module.factory('Authorize',
	function($log, $q, AuthenticationService, AuthorizationResource)
	{
		var _permissions = null;

		var _allow_operation = function(operation, resource) {
			if (resource in _permissions)
			{
				if (operation in _permissions[resource])
				{
					return _permissions[resource][operation];
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
				if (!AuthenticationService.isAuthenticated)
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
				// Need to get permissions from the server side.
				// This is complicated by the async nature of angularjs,
				// since we have to wait for the request to the server to
				// complete, we have to return a promise.
				if (_permissions == null)
				{
					$log.debug("Authorize: Get permissions info from server.");
					var deferred = $q.defer()
					AuthorizationResource.get().$promise.then(
						function (ret)
						{
							_permissions = ret;
							deferred.resolve(
								_allow_operation(operation, resource));
						},
						function (ret)
						{
							// Assume that there's nothing we can do
							// on the client side if we can't 
							$log.error("Failed to get permissions info!");
							deferred.resolve(false);
						}
					);
					return deferred.promise;
				}
				// already have permissions from the server
				return _allow_operation(operation, resource);
			}
		};
	}
);

/***** Controllers *****/
// module.controller(...)

// End anonymous function
})();
