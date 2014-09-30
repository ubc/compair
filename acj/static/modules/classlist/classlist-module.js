// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.classlist',
	[
		'angularFileUpload',
		'ngResource',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.toaster',
		'ubc.ctlt.acj.user',
		'ui.bootstrap'
	]
);

/***** Providers *****/
module.factory(
	"ClassListResource",
	function ($resource)
	{
		var enrolUrl = '/api/courses/:courseId/users/:userId/enrol';
		var ret = $resource(
			'/api/courses/:courseId/users',
			{},
			{
				enrol: {method: 'POST', url: enrolUrl},
				unenrol: {method: 'DELETE', url: enrolUrl}
			}
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
				Toaster.success("Students Added", "Successfully added "+ count +" students.");
				$location.path('/course/' + courseId + '/user/import/results');		
			}	
		};
	}

	var onError = function() {
		return function(fileItem, response, status, headers) {
			Toaster.reqerror("Unable To Upload", status);
			if ('error' in response) {
				Toaster.error("File Type Error", "Only CSV files can be uploaded.");
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
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);
		ClassListResource.get({'courseId':courseId}).$promise.then(
			function (ret) {
				$scope.classlist = ret.objects;
			},
			function (ret) {
				Toaster.reqerror("No Users Found For Course ID "+courseId, ret);
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
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
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
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);

		$scope.headers = ['Username', 'First Name', 'Last Name', 'Email'];
	}
);

module.controller(
	'EnrolInstructorController',
	function($scope, $log, $routeParams, $route, $location, ClassListResource, Toaster, Session, CourseResource, UserTypeResource)
	{

		$scope.course = {};
		$scope.user = {};
		Session.getUser().then(function(user) {
		    $scope.loggedInUserId = user.id;
		});
		var courseId = $routeParams['courseId'];
		// TODO: generate drop down menu to select role
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);
		CourseResource.getInstructors({'id': courseId}).$promise.then(
			function (ret) {
				$scope.enroled = ret.instructors;
			},
			function (ret) {
				Toaster.reqerror("No Instructors Found", ret);
			}
		);
		UserTypeResource.getInstructors().$promise.then(
			function (ret) {
				$scope.instructors = ret.instructors;
			},
			function (ret) {
				Toaster.reqerror("No Instructors Found", ret);
			}
		);
		$scope.enrolSubmit = function() {
			$scope.submitted = true;
			if (!$scope.user.id) {
				Toaster.error("Invalid user selected. Please try again.");
				$scope.user = {};
				$scope.submitted = false;
				return;
			} else if ($scope.enroled[$scope.user.id]) {
				Toaster.success("User is already enroled.");
				$scope.user = {};
				$scope.submitted = false;
				return;
			}
			ClassListResource.enrol({'courseId': courseId, 'userId': $scope.user.id}, $scope.user).$promise.then(
				function (ret) {
					$scope.submitted = false;
					$scope.enroled[ret.user.id] = ret.user.fullname;
					$scope.user = {}; // reset form
					Toaster.success("User Added", 'Successfully added '+ ret.user.fullname +' as ' + ret.usertypesforcourse.name + ' to the course.');
				},
				function (ret) {
					$scope.submitted = false;
					Toaster.reqerror("User Add Failed For ID " + $scope.user_id, ret);
				}
			);
		};

		$scope.remove = function (user_id) {
			Session.getUser().then(function(user) {
				$scope.loggedInUserId = user.id;
			});
			ClassListResource.unenrol({'courseId': courseId, 'userId': user_id}).$promise.then(
				function (ret) {
					Toaster.success("User Dropped", 'Successfully dropped '+ ret.user.fullname +' from the course.');
					// refresh permissions and redirect them to home if they unenroll themselves
					if ($scope.loggedInUserId == ret.user.id) {
						Session.refresh().then(function () {
							$location.path("#/");
						});
					} else {
						delete $scope.enroled[ret.user.id];
					}
				},
				function (ret) {
					Toaster.reqerror('User Drop Failed', ret);
				}
			);
		}
	}
);

// End anonymous function
})();
