// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.group',
	[
		'ngResource',
		'ubc.ctlt.acj.attachment',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.common.interceptor',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"GroupResource",
	function ($resource, Interceptors)
	{
		var url = '/api/courses/:courseId/groups/:groupId';
		var unenrolUrl = '/api/courses/:courseId/users/:userId/groups';
		var ret = $resource(url, {groupId: '@groupId'},
			{
				enrol: {method: 'POST', url: unenrolUrl+'/:groupId', interceptor: Interceptors.enrolCache},
				unenrol: {method: 'DELETE', url: unenrolUrl, interceptor: Interceptors.enrolCache}
			}
		);

		ret.MODEL = 'Groups';
		return ret;
	}
);

/***** Controllers *****/
module.controller(
	'GroupImportController',
	function($scope, $log, $location,$routeParams, CourseResource, Toaster, importService)
	{
		$scope.course = {};
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id': courseId}).$promise.then(
			function (ret) {
				$scope.course_name = ret['name'];
			},
			function (ret) {
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);

		$scope.userIdentifiers = [
			{'key': 'username', 'label': 'Username'},
			{'key': 'student_no', 'label': 'Student Number'}
		];
		$scope.userIdentifier = $scope.userIdentifiers[0].key;

		$scope.uploader = importService.getUploader(courseId, 'groups');

		$scope.uploader.onBeforeUploadItem = function(item) {
			item.formData.push({'userIdentifier': $scope.userIdentifier});
		};

		$scope.uploader.onCompleteItem = function(fileItem, response, status, headers) {
			$scope.submitted = false;
			importService.onComplete(courseId, response);
		};
		$scope.uploader.onErrorItem = importService.onError();
		$scope.upload = function() {
			$scope.submitted = true;
			$scope.uploader.uploadAll();
		};
	}
);

module.controller(
	'GroupImportResultsController',
	function($scope, $log, $location, $routeParams, CourseResource, Toaster, importService)
	{
		$scope.invalids = importService.getResults().invalids;

		$scope.courseId = $routeParams['courseId'];

		// TODO: change "Row" to something more meaningful
		$scope.headers = ['Row', 'Message'];
	}
);

})();