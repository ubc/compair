// Login/logout controllers

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.login', ['ngResource']);

/***** Providers *****/
// TODO declare providers here, e.g.:
// module.factory(...)

/***** Controllers *****/
module.controller(
	"LoginController",
	function LoginController($rootScope, $cookieStore, $scope, $location, flashService, loginService, authService, isInstalled) {
		$rootScope.breadcrumb = [{'name':'Login'}];
		$rootScope.$broadcast("NO_TUTORIAL", false);

		var installed = isInstalled.get( function() {
			if (!installed.installed) {
				$location.path('/install');
			}
		});
		if ($cookieStore.get('loggedIn')) {
			$location.path('/');
		}
		$scope.submit = function() {
			if ( !($scope.username && $scope.password) ) {
				flashService.flash('danger', 'Please provide a username and a password');
				return '';
			}
			input = {"username": $scope.username, "password": $scope.password};
			var user = loginService.save( input, function() {
				if (user.display) {
					authService.loginConfirmed();
					$rootScope.$broadcast("LOGGED_IN", user);
					$location.path('/');
				} else {
					flashService.flash('danger', 'Incorrect username or password');
				}
			});
		};
	}
);

// End anonymous function
})();
