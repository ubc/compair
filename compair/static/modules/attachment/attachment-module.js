(function() {

var module = angular.module('ubc.ctlt.compair.attachment',
    [
        'angularFileUpload',
        'ngResource',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.toaster'
    ]
);

module.constant('FileExtensions', {
    import: ['csv'],
    attachment: []
});

module.constant('FileMimeTypes', {
    pdf: ['application/pdf'],
    mp3: ['audio/mpeg3', 'audio/x-mpeg-3', 'audio/mp3', 'audio/mpeg', 'video/x-mpeg'],
    mp4: ['audio/mp4', 'video/mp4', 'application/mp4'],
    jpg: ['image/jpeg', 'image/pjpeg'],
    jpeg: ['image/jpeg', 'image/pjpeg'],
    png: ['image/png'],
    csv: ['text/csv', 'application/csv', 'text/plain', 'text/comma-separated-values']
});

/***** Services *****/
module.service('importService',
        ['FileUploader', '$location', "$cacheFactory", "CourseResource", "Toaster", "FileExtensions", "FileMimeTypes",
        function(FileUploader, $location, $cacheFactory, CourseResource, Toaster, FileExtensions, FileMimeTypes) {
    var results = {};
    var uploader = null;
    var model = '';

    var onSuccess = function(courseId) {
        var cache = $cacheFactory.get('classlist');
        if (cache) {
            cache.remove('/api/courses/' + courseId + '/users');
        }
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
                    $location.path('/course/'+courseId+'/user/group/import/results');
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
            removeAfterUpload: true,
            headers: {
                Accept: 'application/json'
            }
        });
        model = type;

        uploader.filters.push({
            name: 'importExtensionFilter',
            fn: function(item, options) {
                var type = item.type.slice(item.type.lastIndexOf('/') + 1);
                valid = false;
                _.forEach(FileExtensions.import, function(importExtension) {
                    if (_.includes(FileMimeTypes[importExtension], item.type) || importExtension == type) {
                        valid = true;
                    }
                });
                if (!valid) {
                    var allowedExtensions = FileExtensions.import.join(', ').toUpperCase();
                    Toaster.error("File Type Error", "Only "+allowedExtensions+" files are accepted.")
                }
                return valid;
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
}]);

module.service('attachService',
        ["FileUploader", "$location", "Toaster", "FileExtensions", "FileMimeTypes",
        function(FileUploader, $location, Toaster, FileExtensions, FileMimeTypes) {
    var file = null;

    var getUploader = function() {
        var uploader = new FileUploader({
            url: '/api/attachment',
            queueLimit: 1,
            autoUpload: true,
            headers: {
                Accept: 'application/json'
            }
        });

        file = null;

        uploader.onCompleteItem = onComplete();
        uploader.onErrorItem = onError();

        uploader.filters.push({
            name: 'attachmentExtensionFilter',
            fn: function(item) {
                var type = item.type.slice(item.type.lastIndexOf('/') + 1);
                valid = false;
                _.forEach(FileExtensions.attachment, function(attachmentExtension) {
                    if (_.includes(FileMimeTypes[attachmentExtension], item.type) || attachmentExtension == type) {
                        valid = true;
                    }
                });
                if (!valid) {
                    var allowedExtensions = FileExtensions.attachment.join(', ').toUpperCase();
                    Toaster.error("File Type Error", "Only "+allowedExtensions+" files are accepted.")
                }
                return valid;
            }
        });

        uploader.filters.push({
            name: 'sizeFilter',
            fn: function(item) {
                var valid = item.size <= 26214400; // 1024 * 1024 * 25 -> max 25MB
                if (!valid) {
                    var size = item.size / 1048576; // convert to MB
                    Toaster.error("File Size Error", "The file size is "+size.toFixed(2)+"MB. The maximum allowed is 25MB.")
                }
                return valid;
            }
        });

        return uploader;
    };

    var onComplete = function() {
        return function(fileItem, response) {
            if (response) {
                file = response['file'];
            }
        };
    };

    var onError = function() {
        return function(fileItem, response, status) {
            if (response == '413') {
                Toaster.error("File Size Error", "The file is larger than 25MB. Please upload a smaller file.");
            } else {
                Toaster.reqerror("Attachment Fail", status);
            }
        };
    };

    var reset = function() {
        return function() {
            file = null;
        }
    };

    var getFile = function() {
        return file;
    };

    return {
        getUploader: getUploader,
        getFile: getFile,
        reset: reset
    };
}]);

module.service('answerAttachService',
        ["FileUploader", "$location", "Toaster", "FileExtensions", "FileMimeTypes",
        function(FileUploader, $location, Toaster, FileExtensions, FileMimeTypes) {
    var file = null;

    var getUploader = function(initParams) {
        var uploader = new FileUploader({
            url: '/api/attachment',
            queueLimit: 1,
            autoUpload: true,
            headers: {
                Accept: 'application/json'
            }
        });

        file = null;

        uploader.onCompleteItem = onComplete();
        uploader.onErrorItem = onError();

        uploader.filters.push({
            name: 'attachmentExtensionFilter',
            fn: function(item) {
                var type = item.type.slice(item.type.lastIndexOf('/') + 1);
                valid = false;
                _.forEach(FileExtensions.attachment, function(attachmentExtension) {
                    if (_.includes(FileMimeTypes[attachmentExtension], item.type) || attachmentExtension == type) {
                        valid = true;
                    }
                });
                if (!valid) {
                    var allowedExtensions = FileExtensions.attachment.join(', ').toUpperCase();
                    Toaster.error("File Type Error", "Only "+allowedExtensions+" files are accepted.")
                }
                return valid;
            }
        });

        uploader.filters.push({
            name: 'sizeFilter',
            fn: function(item) {
                var valid = item.size <= 26214400; // 1024 * 1024 * 25 -> max 25MB
                if (!valid) {
                    var size = item.size / 1048576; // convert to MB
                    Toaster.error("File Size Error", "The file size is "+size.toFixed(2)+"MB. The maximum allowed is 25MB.")
                }
                return valid;
            }
        });

        return uploader;
    };

    var uploadedCallback = function(fileItem) {};
    var onComplete = function() {
        return function(fileItem, response) {
            if (response) {
                file = response['file'];
                uploadedCallback(file);
            }
        };
    };

    var onError = function() {
        return function(fileItem, response, status) {
            if (response == '413') {
                Toaster.error("File Size Error", "The file is larger than 25MB. Please upload a smaller file.");
            } else {
                Toaster.reqerror("Attachment Fail", status);
            }
        };
    };

    var reset = function() {
        return function() {
            file = null;
        };
    };

    var getFile = function() {
        return file;
    };

    return {
        getUploader: getUploader,
        getFile: getFile,
        reset: reset,
        setUploadedCallback: function(callback) {
            uploadedCallback = callback;
        }
    };
}]);

/***** Controllers *****/

})();
