// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

// TODO 
// Create the module with a unique name.
// The module needs a unique name that prevents conflicts with 3rd party modules
// We're using "ubc.ctlt.acj" as the project's prefix, followed by the module 
// name.
var module = angular.module('ubc.ctlt.acj.home',
	[
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.user'
	]
);

/***** Providers *****/
// TODO declare providers here, e.g.:
// module.factory(...)

/***** Controllers *****/
module.controller(
	'HomeController',
	function HomeController($rootScope, $scope, $location, CourseResource,
							UserResource,
							loginService, flashService) {
		// the property by which the list of courses will be sorted
		$scope.orderProp = 'name';
		$rootScope.breadcrumb = [{'name':'Home'}];

		var login = loginService.get( function() {
			type = login.usertype;
			if (type && (type=='Teacher' || type=='Admin')) {
				$scope.instructor = true;
				$scope.admin = type=='Admin';
			} else {
				$scope.instructor = false;
			}

			var courses = CourseResource.get( function() {
				var steps = [];
				var intro = '';
				$scope.courses = courses.courses;
				if ( $scope.instructor ) {
					steps = [
						{
							element: '#step1',
							intro: 'Create a new course',
						},
						{
							element: '#step2',
							intro: "Go to Question Page to view questions and create questions",
						},
						{
							element: '#step3',
							intro: "Go to Enrol Page to enrol students or drop students",
						},
						{
							element: "#step4",
							intro: "Go to Import Page to import students from a file",
						},
					];
					intro = "Lists all the courses you are enrolled in. As an instructor, creating a new course is also an option. From here you can go to Question Page, Enrolment Page, or Import Page.";
				} else {
					steps = [
						{
							element: '#step2',
							intro: "Go to Question Page to view questions and create question",
						},
					];
					intro = "Lists all the courses you are enrolled in. From here, you can go to Question Page.";
				}
				if ( courses.courses.length < 1 ) {
					steps = [];
				}
				$rootScope.$broadcast("STEPS", {"steps": steps, "intro": intro});
			});
		});
		$scope.submit = function() {
			input = {"name": $scope.course};
			var retval = courseService.save( input, function() {
				$scope.check = false;
				$scope.flash = retval.flash;
				if (!$scope.flash) {
					$scope.courses.push(retval);
				}
				else {
					flashService.flash('danger', retval.flash);
				}
			});
		};
		$scope.redirect = function(url) {
			$location.path(unescape(url));
		};
	}
);
// End anonymous function
})();
