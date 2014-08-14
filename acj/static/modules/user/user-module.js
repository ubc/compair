// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.user', ['ngResource']);

/***** Providers *****/
module.factory('UserResource', function($resource) {
	var User = $resource('/api/users/:id', {id: '@id'},
		{
			'getUserCourses':
			{
				method: 'GET',
				url: '/api/users/:id/courses'
			}
		}
	);
	User.MODEL = "Users";

    User.prototype.isLoggedIn = function() {
        return this.hasOwnProperty('id');
    };

	return User;
});
module.factory('UserTypeResource', function($resource) {
	var ret = $resource('/api/usertypes/:id', {id: '@id'});
	ret.MODEL = "UserTypesForSystem";
	return ret;
});
module.factory('UserPasswordResource', function($resource) {
	var ret = $resource('/api/users/password/:id', {id: '@id'});
	ret.MODEL = "Users";
	return ret;
});


/***** Controllers *****/
// TODO declare controllers here, e.g.:
module.controller("UserCreateController",
	function($scope, $log, $routeParams, UserResource, UserTypeResource, Toaster)
	{
		$scope.usertypes = {};
		$scope.user = {};
		$scope.create = true;
		UserTypeResource.query(
			function (ret)
			{
				$scope.usertypes = ret;
				$scope.user.usertypesforsystem_id = $scope.usertypes[0].id;
			},
			function (ret)
			{
				Toaster.reqerror("Unable to retrieve the user types", ret);
			}
		);
		$scope.userSubmit = function () {
			$scope.submitted = true;
			UserResource.save({},$scope.user).$promise.then(
				function (ret)
				{
					$scope.submitted = false;
					Toaster.success("New User Created!",
						'"' + ret.displayname + '"' +'should now have access.');
				},
				function (ret)
				{
					$scope.submitted = false;
					if (ret.status == '409') {
						Toaster.error(ret.data.error);
					} else {
						Toaster.reqerror("Unable to create new user.", ret);
					}
				}
			);
		};
	}
);

module.controller("UserEditController",
	function($scope, $log, $routeParams, breadcrumbs, Session, UserResource, Authorize, UserTypeResource, Toaster)
	{
		var userId = $routeParams['userId'];
		Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
            $scope.canManageUsers = result;
        });
        Session.getUser().then(function(user) {
            $scope.ownProfile = userId == user.id;
        });
		$scope.user = {}
		$scope.usertypes = {};
		$scope.create = false;
		UserTypeResource.query(
			function (ret) {
				$scope.usertypes = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the user types", ret);
			}
		);
		UserResource.get({'id':userId}).$promise.then(
			function (ret) {
				$scope.user = ret;
				breadcrumbs.options = {'View User': ret.username+"'s Profile"};
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve user "+ userId, ret);
			}
		);
		$scope.userSubmit = function() {
			$scope.submitted = true;
			UserResource.save({'id': userId}, $scope.user).$promise.then(
				function(ret) {
					$scope.submitted = false;
					Toaster.success("User Updated!");
				},
				function(ret) {
					$scope.submitted = false;
					Toaster.reqerror("User Update Failed.", ret);
				}
			);
		}
	}
);

module.controller("UserUpdatePasswordController",
	function($scope, $log, $routeParams, Session, UserPasswordResource, Toaster)
	{
        $scope.password = {};
        $scope.create = true;
		Session.getUser().then(function(user) {
            $scope.changePassword = function() {
                $scope.submitted = true;
                UserPasswordResource.save({'id': user.id}, $scope.password).$promise.then(
                    function (ret) {
                        $scope.submitted = false;
                        Toaster.success("Password Updated!");
                    },
                    function (ret) {
                        $scope.submitted = false;
                        if (ret.status == '401') {
                            Toaster.error(ret.data.error);
                        } else {
                            Toaster.reqerror("Unable to update your password.", ret);
                        }
                    }
                );
            }
        });
	}
);

module.controller("UserViewController",
	function($scope, $log, $routeParams, breadcrumbs, Session, UserResource, Authorize, Toaster)
	{
		var userId = $routeParams['userId'];
		Authorize.can(Authorize.CREATE, UserResource.MODEL).then(function(result) {
            $scope.canCreateUser = result;
        });
        Session.getUser().then(function(user) {
            $scope.ownProfile = userId == user.id;
        });
		$scope.user = {}
		UserResource.get({"id":userId}).$promise.then(
			function (ret) {
				$scope.user = ret;
				breadcrumbs.options = {'View User': ret.username+"'s Profile"};
				$scope.readDate = Date.parse(ret.lastonline);
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve the user's data", ret);
			}
		);

	}
);

// End anonymous function
})();
