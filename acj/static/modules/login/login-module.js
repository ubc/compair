// Login/logout controllers

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.login',
	[
		'ngResource',
		'ubc.ctlt.acj.authentication',
		'ubc.ctlt.acj.user'
	]
);

/***** Providers *****/
module.factory('LoginResource', function($resource) {
	return $resource(
		'/login/:operation',
		{},
		{
			login: { method:'POST', params: {operation: "login"} },
			logout: { method:'DELETE', params: {operation: "logout"} }
		}
	);
});

/***** Controllers *****/
module.controller(
	"LoginController",
	function LoginController($rootScope, $scope, $location, $log,
							 LoginResource, UserResource, AuthenticationService) {
		// TODO REFACTOR BREADCRUMB AND NO_TUTORIAL BROADCAST
		$rootScope.breadcrumb = [{'name':'Login'}];
		$rootScope.$broadcast("NO_TUTORIAL", false);

		$scope.submitted = false;

		$scope.submit = function() {
			$scope.submitted = true;
			var params = {"username": $scope.username, "password": $scope.password};
			LoginResource.login(params).$promise.then(
				function(ret) {
					// login successful
					$log.debug("Login authentication successful!");
					userid = ret.userid
					$log.debug("Login User ID: " + userid);
					// retrieve logged in user's information
					user = UserResource.get({id: userid}).$promise.then(
						function(ret) {
							$log.debug("Retrived logged in user's data: " + JSON.stringify(ret));
							AuthenticationService.login(ret);
							$location.path("/");
						},
						function(ret) {
							$log.debug("Failed to retrieve logged in user's data: " +
								JSON.stringify(ret));
							$scope.login_err = "Unable to retrieve user information, server problem?";
							$scope.submitted = false;
						}
					);
				},
				function(ret) {
					// login failed
					$log.debug("Login authentication failed.");
					$scope.login_err = ret.data.error;
					$scope.submitted = false;
				}
			);

		};
	}
);

module.controller(
	"LogoutController",
	function LogoutController($scope, $location, $log, LoginResource, AuthenticationService) {
		$scope.logout = function() {
			LoginResource.logout().$promise.then(
				function() {
					$log.debug("Logging out user successful.");
					AuthenticationService.logout();
					$location.path("/login");
				}
				// TODO do we care about logout failure? if so, handle it here
			);
		};
	}
);
// End anonymous function
})();
