// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.course', ['ngResource', 'ckeditor']);

/***** Providers *****/
module.factory('CourseResource', function($resource) {
	var ret = $resource('/api/courses/:id', {id: '@id'})
	ret.MODEL = "Courses"; // add constant to identify the model
						// being used, this is for permissions checking
						// and should match the server side model name
	return ret;
});

/***** Controllers *****/
module.controller(
	'CourseController',
	function($scope, $log, CourseResource)
	{
		$scope.editorOptions = 
		{
			language: 'en',
			disableInline: true,
			removeButtons: 'Anchor,Strike,Subscript,Superscript',
			toolbarGroups: [
				{ name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
				{ name: 'links' }
			]
		};
		$scope.newCourseSubmit = function() {
			$scope.submitted = true;
			CourseResource.save($scope.course).$promise.then(
				function (ret)
				{
					$scope.submitted = false;
					// TODO REDIRECT TO NEWLY CREATED COURSE
				},
				function (ret)
				{
					$scope.submitted = false;
					$scope.courseErr = ret.data.error
				}
			);
		};
	}
);

// End anonymous function
})();
