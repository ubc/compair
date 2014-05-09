// Module for the main navbar at the top of the application.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.navbar',
	[
		'ubc.ctlt.acj.authentication',
		'ubc.ctlt.acj.login' // for LogoutController
	]
);

/***** Providers *****/
// TODO declare providers here, e.g.:
// module.factory(...)

/***** Controllers *****/
module.controller(
	"NavbarController",
	function NavbarController($scope, $log, AuthenticationService) {

		// TODO determine if breadcrumbs can be improved
		$scope.breadcrumbs = [];

		// get information about the currently logged in user
		var updateAuthentication = function() {
			$scope.isLoggedIn = AuthenticationService.isAuthenticated();
			if ($scope.isLoggedIn)
			{
				var user = AuthenticationService.getUser();
				$scope.loggedInUser = user.displayname ? user.displayname : user.username;
				$log.info("Logged in as " + $scope.loggedInUser);
			}
			else
			{
				$log.info("No user login.");
			}
		};
		// listen for changes in authentication state
		$scope.$on(AuthenticationService.LOGIN_EVENT, updateAuthentication);
		$scope.$on(AuthenticationService.LOGOUT_EVENT, updateAuthentication);
		// initialize authentication information
		updateAuthentication();

		$scope.showLogin = function() {
			$scope.$emit(AuthenticationService.LOGIN_REQUIRED_EVENT);
		};

		// TODO Not sure what listening to judgement, steps do
		$scope.$on("JUDGEMENT", function(event) {
			route = $scope.breadcrumb[$scope.breadcrumb.length - 1].link ? $scope.breadcrumb[$scope.breadcrumb.length - 1].link : "";
			$location.path(route.replace("#/", ""));
		});
		var steps = '';
		$scope.$on("STEPS", function(event, val) {
			$scope.hastutorial = true;
			steps = val.steps;
			var intro = val.intro;
			steps.unshift({element: '#stepTutorial', intro: intro});
		});
	}
);

// End anonymous function
})();
