// Just holds the course resouce object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.group',
	[
		'ngResource',
		'ubc.ctlt.acj.attachment',
		'ubc.ctlt.acj.common.form',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Providers *****/
module.factory(
	"GroupResource",
	function ($resource)
	{
		var url = '/api/courses/:courseId/groups/:groupId';
		var unenrolUrl = '/api/courses/:courseId/users/:userId/groups'
		var ret = $resource(url, {groupId: '@groupId'},
			{
				enrol: {method: 'POST', url: unenrolUrl+'/:groupId'},
				unenrol: {method: 'DELETE', url: unenrolUrl}
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
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);
		$scope.uploader = importService.getUploader(courseId, 'groups');
		$scope.uploader.onCompleteItem = importService.onComplete(courseId);
		$scope.uploader.onErrorItem = importService.onError();
	}
);

module.controller(
	'GroupImportResultsController',
	function($scope, $log, $location, $routeParams, CourseResource, Toaster, importService)
	{
		$scope.invalids = importService.getResults().invalids;

		$scope.course = {}
		var courseId = $routeParams['courseId'];
		CourseResource.get({'id':courseId}).$promise.then(
			function (ret) {
				$scope.course = ret;
			},
			function (ret) {
				Toaster.reqerror("No Course Found For ID "+courseId, ret);
			}
		);

		// TODO: change "Row" to something more meaningful
		$scope.headers = ['Row', 'Message'];
	}
);

})();