(function() {

var module = angular.module('ubc.ctlt.acj.attachment',
	[
		'ngPDFViewer',
		'ngResource',
		'ubc.ctlt.acj.authorization',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Controllers *****/
module.controller(
	"AttachmentPDFController",
	function($scope, $log, $routeParams, Authorize, CourseResource, QuestionResource, PDFViewerService, Toaster)
	{
		var courseId = $routeParams['courseId'];
		var questionId = $routeParams['questionId'];
		var postId = $routeParams['postId'];

		Authorize.can(Authorize.READ, CourseResource.MODEL).then(function(result) {
			$scope.canReadCourse = result;
		});
		Authorize.can(Authorize.READ, QuestionResource.MODEL).then(function(result) {
		    	$scope.canReadQuestion = result;
		});
		$scope.pdfURL = 'pdf/'+ courseId + '_' + questionId + '_' + postId + '.pdf';
		$scope.instance = PDFViewerService.Instance("viewer");
		$scope.nextPage = function() {
			$scope.instance.nextPage();
		};

		$scope.prevPage = function() {
			$scope.instance.prevPage();
		};

		$scope.gotoPage = function(page) {
			$scope.instance.gotoPage(page);
		};

		$scope.pageLoaded = function(curPage, totalPages) {
			$scope.currentPage = curPage;
			$scope.totalPages = totalPages;
		};
	}
);
})();
