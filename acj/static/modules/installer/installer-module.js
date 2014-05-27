// Module for the installation wizard.

// isolate this module's creation by putting it in an anonymous function
(function() {

// the module needs a unique name that prevents conflicts with 3rd party modules
var module = angular.module(
	'ubc.ctlt.acj.installer', 
	[
		'ngResource', 
		'ngCookies',
		'ubc.ctlt.acj.common.flash',
		'ubc.ctlt.acj.common.installed'
	]
);

/***** Providers *****/
module.factory('installService', function($resource) {
	return $resource('/install');
});

module.factory('createAdmin', function($resource) {
	return $resource( '/admin' );
});

/***** Controllers *****/
module.controller(
	"InstallController",
	function InstallController($rootScope, $scope, $location, $cookieStore, flashService, installService, createAdmin, isInstalled) {
		$scope.failMsg = "";
		var criteria = installService.get( function() {
			//$scope.username = criteria.username;
			$scope.requirements = criteria.requirements;
		});

		$scope.submit = function() 
		{
			if ($scope.password != $scope.retypepw) {
				return '';
			}
			var re = /[^@]+@[^@]+/;
			if ($scope.email == undefined || $scope.email == '') {
				$scope.email = undefined;
			} else if (!re.exec($scope.email)) {
				$scope.formaterr = true;
				return;
			}
			input = {"username": $scope.username, "password": $scope.password, "usertype": 'Admin', "email": $scope.email, "firstname": $scope.firstname, "lastname": $scope.lastname, "display": $scope.display};
			// try to save the admin user
			createAdmin.save(input).$promise.then( 
				// request successful
				function(ret) {
					console.log(ret);
					if (ret['error'].length > 0) {
						$scope.failMsg = ret['error'][0]['msg'];
					}
					else {
						$scope.done = true;
						flashService.flash('success', 'Administrator created. Click Login to try logging in with your administrator account');
					}
				},
				// request error
				function(error) {
					$scope.failMsg = "Server error while saving."
				}
			);
		};
	}
);


// end anonymous function
})();
