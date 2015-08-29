// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.user', [
	'ngResource', 'ngRoute', 'ng-breadcrumbs', 'ubc.ctlt.acj.session',
	'ubc.ctlt.acj.authorization', 'ubc.ctlt.acj.toaster'
]);

/***** Providers *****/
module.factory('UserResource', ['$resource', function($resource) {
	var User = $resource('/api/users/:id', {id: '@id'}, {
		'getUserCourses': {url: '/api/users/:id/courses'},
		'getTeachingUserCourses': {url: '/api/users/courses/teaching'},
		'getEditButton': {url: '/api/users/:id/edit'},
		'password': {method: 'POST', url: '/api/users/:id/password'}
	});
	User.MODEL = "Users";

	User.prototype.isLoggedIn = function() {
		return this.hasOwnProperty('id');
	};

	return User;
}]);
module.factory('UserTypeResource', ['$resource', function($resource) {
	var ret = $resource('/api/usertypes/:id', {id: '@id'});
	ret.MODEL = "UserTypesForSystem";
	return ret;
}]);
module.factory('CourseRoleResource', ['$resource', function($resource){
	var ret = $resource('/api/courseroles');
	ret.MODEL = "UserTypesForCourse";
	return ret;
}]);

/***** Controllers *****/
module.controller("UserController", ['$scope', '$log', '$route', '$routeParams', '$location', 'breadcrumbs', 'Session', 'UserResource', 'Authorize', 'UserTypeResource', 'Toaster',
	function($scope, $log, $route, $routeParams, $location, breadcrumbs, Session, UserResource, Authorize, UserTypeResource, Toaster) {
		var userId;
		var messages = {
			new: {title: 'New User Created', msg: 'User should now have access.'},
			edit: {title: 'User Successfully Updated', msg: 'Your changes were saved.'}
		};
		$scope.user = {};
		$scope.method = 'new';
		$scope.password = {};
		Authorize.can(Authorize.MANAGE, UserResource.MODEL).then(function(result) {
			$scope.canManageUsers = result;
		});
		Session.getUser().then(function(user) {
			$scope.ownProfile = userId == user.id;
		});
		$scope.usertypes = UserTypeResource.query(function(ret) {
			if ($scope.method == 'new') {
				$scope.user.usertypesforsystem_id = ret[0].id;
			}
		});

		$scope.save = function() {
			$scope.submitted = true;
			UserResource.save({'id': userId}, $scope.user, function(ret) {
				Toaster.success(messages[$scope.method].title, messages[$scope.method].msg);
				$location.path('/user/' + ret.id);
			}).$promise.finally(function() {
				$scope.submitted = false;
			});
		};

		$scope.edit = function() {
			userId = $routeParams.userId;
			$scope.user = UserResource.get({'id':userId}, function (ret) {
				breadcrumbs.options = {'User Profile': "{0}'s Profile".format(ret.displayname)};
			});
		};

		$scope.view = function() {
			$scope.edit();
			Authorize.can(Authorize.CREATE, UserResource.MODEL).then(function(result) {
				$scope.canCreateUser = result;
			});
			$scope.showEditButton = UserResource.getEditButton({"id":userId});
		};

		$scope.changePassword = function() {
			$scope.submitted = true;
			UserResource.password({'id': $scope.user.id}, $scope.password, function (ret) {
				Toaster.success("Password Successfully Updated", "Your password has been changed.");
				$location.path('/user/' + ret.id);
			}).$promise.finally(function() {
				$scope.submitted = false;
			});
		};

		//  Calling routeParam method
		if ($route.current !== undefined &&
			$route.current.method !== undefined &&
			$scope.hasOwnProperty($route.current.method)) {

			$scope.method = $route.current.method;
			$scope[$scope.method]();
		}
	}]
);
// End anonymous function
})();
