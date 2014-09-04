// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.classlist',
	[
		'angularFileUpload',
		'ngResource',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"ClassListResource",
	function ($resource)
	{
		var ret = $resource(
			'/api/courses/:courseId/users'
		);
		ret.MODEL = "CoursesAndUsers";
		return ret;
	}
);

/***** Services *****/
module.service('importService', function(FileUploader, $location, CourseResource, Toaster) {
	var results = {};
	var uploader = null; 
	
	var getUploader = function(courseId) {
		var uploader = new FileUploader({
			url: '/api/courses/'+courseId+'/users',
			queueLimit: 1,
			removeAfterUpload: true
		});

		uploader.filters.push({
			name: 'pdfFilter',
			fn: function(item, options) {
				var type = '|' + item.type.slice(item.type.lastIndexOf('/') + 1) + '|';
				return '|csv|'.indexOf(type) !== -1;
			}
		});

		return uploader;
	}

	var onComplete = function(courseId) {
		return function(fileItem, response, status, headers) {
			results = response;
			if (!('error' in results)) {
				count = results.success.length;
				Toaster.success("Successfully enroled "+ count +" students.");
				$location.path('/course/' + courseId + '/user/import/results');		
			}	
		};
	}

	var onError = function() {
		return function(fileItem, response, status, headers) {
			Toaster.reqerror("Unable to upload the class list. Please try again.", status);
			if ('error' in response) {
				Toaster.error("Only csv files can be uploaded.");
			}
		};
	}	

	var getResults = function() {
		return results;
	}

	return {
		getUploader: getUploader,
		onComplete: onComplete,
		getResults: getResults,
		onError: onError
	};
});

/***** Controllers *****/
module.controller(
	'ClassViewController',
	function($scope, $log, $routeParams, ClassListResource, CourseResource, Toaster)
	{
		$scope.course = {};
		$scope.classlist = {};
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve course: "+courseId, ret);
			}
		);
		ClassListResource.get({'courseId':courseId}).$promise.then(
			function (ret) {
				$scope.classlist = ret.objects;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve class list for course: "+courseId, ret);
			}
		);
	}
);

module.controller(
	'ClassImportController',
	function($scope, $log, $location, $routeParams, ClassListResource, CourseResource, Toaster, importService)
	{
		$scope.course = {};
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve course: "+courseId, ret);
			}
		);
		$scope.uploader = importService.getUploader(courseId);
		$scope.uploader.onCompleteItem = importService.onComplete(courseId);
		$scope.uploader.onErrorItem = importService.onError();
	}
);

module.controller(
	'ClassImportResultsController',
	function($scope, $log, $routeParams, ClassListResource, Toaster, importService, CourseResource)
	{
		$scope.results = importService.getResults();

		$scope.course = {};
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("Unable to retrieve course: "+courseId, ret);
			}
		);
		
		$scope.headers = ['Username', 'First Name', 'Last Name', 'Email'];
	}
);

// End anonymous function
})();
