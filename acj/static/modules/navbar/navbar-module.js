// Module for the main navbar at the top of the application.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.navbar',
	[
		'ng-breadcrumbs',
		'ngRoute',
		'ubc.ctlt.acj.authentication',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.login', // for LogoutController
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.user'
	]
);

/***** Providers *****/
// TODO declare providers here, e.g.:
// module.factory(...)

/***** Controllers *****/
module.controller(
	"NavbarController",
	function NavbarController($scope, $log, $route, breadcrumbs,
		Session, AuthenticationService, Authorize, CourseResource, UserResource, QuestionResource)
	{
		$scope.breadcrumbs = breadcrumbs;
		$scope.isLoggedIn = false;

		// determine if we're in a course so we know whether to show
		// the course settings
		//$scope.inCourse = false;
		$scope.getPermissions = function() {
			Authorize.can(Authorize.CREATE, UserResource.MODEL).then(function (result) {
				$scope.canCreateUsers = result;
			});
			Authorize.can(Authorize.CREATE, CourseResource.MODEL).then(function (result) {
				$scope.canCreateCourses = result;
			});
			Authorize.can(Authorize.MANAGE, QuestionResource.MODEL).then(function (result) {
				$scope.canManageQuestions = result;
			});
		};
		$scope.setInCourse = function() {
			var courseId = $route.current.params['courseId'];
			$scope.inCourse = false;
			if (courseId) {
				$scope.inCourse = true;
				// update breadcrumb to show the course name
				CourseResource.getName({'id': courseId}).$promise.then(
					function(ret)
					{
						breadcrumbs.options = {'Course Questions': ret['course_name']};
					}
				);
			}
			$scope.courseId = courseId;
		};
		$scope.setInCourse(); // init for first page load
		$scope.$on('$locationChangeSuccess', function(event, next) {
			// update for further navigation after the page has loaded
			$scope.setInCourse();
		});
		// show course configure options if user can edit courses
		/*Authorize.can(Authorize.EDIT, CourseResource.MODEL).then(function(result) {
			$scope.canEditCourse = result;
		})*/

		Session.getUser().then(function(user) {
			$scope.loggedInUser = user;
			$log.debug("Logged in as " + $scope.loggedInUser.username);
		});

		$scope.getPermissions();
		$scope.$on(AuthenticationService.LOGIN_EVENT, function() {
		   $scope.getPermissions();
		});

		// listen for changes in authentication state
//		$scope.$on(AuthenticationService.LOGIN_EVENT, updateAuthentication);
//		$scope.$on(AuthenticationService.LOGOUT_EVENT, updateAuthentication);

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
