(function() {

var module = angular.module('ubc.ctlt.acj.attachment',
	[
		'angularFileUpload',
		'ngPDFViewer',
		'ngResource',
		'ubc.ctlt.acj.authorization',
		'ubc.ctlt.acj.course',
		'ubc.ctlt.acj.question',
		'ubc.ctlt.acj.toaster'
	]
);

/***** Services *****/
module.service('importService', function(FileUploader, $location, CourseResource, Toaster) {
	var results = {};
	var uploader = null;
	var model = '';

	var onSuccess = function(courseId) {
		switch(model) {
			case 'users':
				var count = results.success.length;
				Toaster.success("Students Added", "Successfully added "+count+" students.");
				$location.path('/course/'+courseId+'/user/import/results');
				break;
			case 'groups':
				Toaster.success("Groups Added", "Successfully added "+ results.success +" groups.");
				if (results.invalids.length > 0) {
					$location.path('/course/'+courseId+'/group/import/results');
				} else {
					$location.path('/course/'+courseId+'/user');
				}
				break;
			default:
				Toaster.success("Success");
				break;
		}
	};

	var getUploader = function(courseId, type) {
		uploader = new FileUploader({
			url: '/api/courses/'+courseId+'/'+type,
			queueLimit: 1,
			removeAfterUpload: true
		});
		model = type;

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
				onSuccess(courseId);
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
