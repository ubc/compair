(function() {

var module = angular.module('ubc.ctlt.acj.attachment',
	[
		'angularFileUpload',
		'ngResource',
		'ubc.ctlt.acj.course',
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
				var count = results.success;
				Toaster.success("Students Added", "Successfully added "+count+" students.");
				if (results.invalids.length > 0) {
					$location.path('/course/' + courseId + '/user/import/results');
				} else {
					$location.path('/course/' + courseId + '/user');
				}
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
	};

	var onComplete = function(courseId, response) {
		results = response;
		if (!('error' in results)) {
			onSuccess(courseId);
		}
	};

	var onError = function() {
		return function(fileItem, response, status, headers) {
			Toaster.reqerror("Unable To Upload", status);
			if ('error' in response) {
				Toaster.error("File Type Error", "Only CSV files can be uploaded.");
			}
		};
	};

	var getResults = function() {
		return results;
	};

	return {
		getUploader: getUploader,
		onComplete: onComplete,
		getResults: getResults,
		onError: onError
	};
});

/***** Controllers *****/

})();
