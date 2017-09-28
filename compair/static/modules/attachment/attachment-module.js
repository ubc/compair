(function() {

var module = angular.module('ubc.ctlt.compair.attachment',
    [
        'angularFileUpload',
        'ngResource',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.toaster'
    ]
);

module.constant('UploadSettings', {
    importExtensions: ['csv'],
    attachmentExtensions: [],
    attachmentUploadLimit: 26214400, //1024 * 1024 * 25 -> max 25 MB
    kalturaExtensions: null, //only set when kaltura is enabled
});

/***** Providers *****/
module.factory('UploadValidator',
    ['UploadSettings',
    function(UploadSettings)
    {
        return {
            kalturaEnabled: function() {
                return UploadSettings.kalturaExtensions && UploadSettings.kalturaExtensions.length > 0
            },

            getAttachmentUploadLimit: function() {
                return UploadSettings.attachmentUploadLimit;
            },

            validImportExtension: function(extension) {
                return this.isAttachmentExtension(extension);
            },
            validAttachmentExtension: function(extension) {
                return this.isKalturaExtension(extension) || this.isAttachmentExtension(extension);
            },

            isImportExtension: function(extension) {
                return _.includes(UploadSettings.importExtensions, extension);
            },
            isKalturaExtension: function(extension) {
                return this.kalturaEnabled() && _.includes(UploadSettings.kalturaExtensions, extension);
            },
            isAttachmentExtension: function(extension) {
                return _.includes(UploadSettings.attachmentExtensions, extension);
            },

            displayExtensions: function(extensions) {
                extensions = _.map(extensions, function(extension) {
                    return extension.toUpperCase()+"s";
                });
                extensions.sort();

                if (extensions.length >= 3) {
                    extensions[extensions.length-1] = "and "+extensions[extensions.length-1];
                    return extensions.join(", ");
                } else if (extensions.length == 1 || extensions.length == 2) {
                    return extensions.join(" and ");
                } else {
                    return "";
                }
            },

            getAttachmentExtensionsForDisplay: function() {
                var extensions = UploadSettings.attachmentExtensions;
                if (this.kalturaEnabled()) {
                    extensions = _.uniq(_.concat(UploadSettings.attachmentExtensions, UploadSettings.kalturaExtensions));
                }
                return this.displayExtensions(extensions);
            },
            getImportExtensionsForDisplay: function() {
                return this.displayExtensions(UploadSettings.importExtensions);
            }
        }
    }
]);

module.factory('KalturaResource',
    ['$resource',
    function($resource)
    {
        var ret = $resource('/api/attachment/kaltura/:id', {id: '@id'});
        return ret;
    }
]);

/***** Services *****/
module.service('importService',
        ['FileUploader', '$location', "$cacheFactory", "CourseResource", "Toaster", "UploadValidator",
        function(FileUploader, $location, $cacheFactory, CourseResource, Toaster, UploadValidator) {
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
                if (results.invalids && results.invalids.length > 0) {
                    Toaster.success("Some Users Enrolled", "Successfully enrolled "+count+" users.");
                    $location.path('/course/' + courseId + '/user/import/results');
                } else {
                    Toaster.success("All Users Enrolled", "Successfully enrolled "+count+" users.");
                    $location.path('/course/' + courseId + '/user');
                }
                break;
            case 'groups':
                if (results.invalids && results.invalids.length > 0) {
                    Toaster.success("Some Groups Added", "Successfully added "+ results.success +" groups.");
                    $location.path('/course/'+courseId+'/user/group/import/results');
                } else {
                    Toaster.success("All Groups Added", "Successfully added "+ results.success +" groups.");
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

        uploader.onErrorItem = function(fileItem, response, status, headers) {
            // nothing to do
        };

        uploader.filters.push({
            name: 'importExtensionFilter',
            fn: function(item) {
                var extension = item.name.slice(item.name.lastIndexOf('.') + 1).toLowerCase();
                var valid = UploadValidator.isImportExtension(extension);

                if (!valid) {
                    var allowedExtensions = UploadValidator.getImportExtensionsForDisplay();
                    Toaster.error("File Not Uploaded", "Please try again with an approved file type, which includes: "+allowedExtensions+".")
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


    var getResults = function() {
        return results;
    };

    return {
        getUploader: getUploader,
        onComplete: onComplete,
        getResults: getResults
    };
}]);

module.service('attachService',
        ["FileUploader", "$location", "Toaster", "UploadValidator", "KalturaResource",
        function(FileUploader, $location, Toaster, UploadValidator, KalturaResource) {
    var file = null;

    var getUploader = function() {
        var uploader = new FileUploader({
            url: '/api/attachment',
            queueLimit: 1,
            autoUpload: false,
            headers: {
                Accept: 'application/json'
            }
        });

        file = null;

        uploader.onSuccessItem = function(fileItem, response) {
            var extension = fileItem.file.name.slice(fileItem.file.name.lastIndexOf('.') + 1).toLowerCase();

            if (UploadValidator.kalturaEnabled() && UploadValidator.isKalturaExtension(extension)) {
                if (response && response.id) {
                    uploader.waitForKalturaComplete = true;
                    // upload successful, notify back-end to retrieve file reference
                    KalturaResource.save({id: response.id},
                        function(ret) {
                            file = ret.file;
                            uploader.waitForKalturaComplete = undefined;
                        }, function(ret) {
                            uploader.waitForKalturaComplete = undefined;
                        }
                    );
                }
            } else if (response && response.file) {
                file = response.file;
            }
        };

        uploader.onErrorItem = function(fileItem, response, status) {
            fileItem.cancel();
            fileItem.remove();
            reset();
            if (response == '413') {
                var upload_limit = UploadValidator.getAttachmentUploadLimit();
                var limit_size = upload_limit / 1048576; // convert to MB
                Toaster.error("File Not Uploaded", "The file is larger than the "+limit_size.toFixed(0)+"MB maximum. Please upload a smaller file instead.");
            }
        };

        uploader.onAfterAddingFile = function(fileItem) {
            var extension = fileItem.file.name.slice(fileItem.file.name.lastIndexOf('.') + 1).toLowerCase();

            if (UploadValidator.kalturaEnabled() && UploadValidator.isKalturaExtension(extension)) {
                KalturaResource.get({}, function(ret) {
                    fileItem.url = ret.upload_url;
                    fileItem.alias = "fileData";
                    uploader.uploadItem(fileItem);
                });
            } else {
                uploader.uploadItem(fileItem);
            }
        };

        uploader.filters.push({
            name: 'attachmentExtensionFilter',
            fn: function(item) {
                var extension = item.name.slice(item.name.lastIndexOf('.') + 1).toLowerCase();
                var valid = UploadValidator.validAttachmentExtension(extension);
                if (!valid) {
                    var allowedExtensions = UploadValidator.getAttachmentExtensionsForDisplay();
                    Toaster.error("File Not Uploaded", "Please try again with an approved file type, which includes: "+allowedExtensions+".")
                }
                return valid;
            }
        });

        uploader.filters.push({
            name: 'sizeFilter',
            fn: function(item) {
                var upload_limit = UploadValidator.getAttachmentUploadLimit();

                valid = item.size <= upload_limit;
                if (!valid) {
                    var size = item.size / 1048576; // convert to MB
                    var limit_size = upload_limit / 1048576; // convert to MB
                    Toaster.error("File Not Uploaded", "The file size is "+size.toFixed(2)+"MB, which exceeds the "+limit_size.toFixed(0)+"MB maximum. Please upload a smaller file instead.")
                }
                return valid;
            }
        });

        return uploader;
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
        ["FileUploader", "$location", "Toaster", "UploadValidator", "KalturaResource",
        function(FileUploader, $location, Toaster, UploadValidator, KalturaResource) {
    var file = null;

    var getUploader = function(initParams) {
        var uploader = new FileUploader({
            url: '/api/attachment',
            queueLimit: 1,
            autoUpload: false,
            headers: {
                Accept: 'application/json'
            }
        });

        file = null;

        uploader.onErrorItem = function() {
            return function(fileItem, response, status) {
                fileItem.cancel();
                fileItem.remove();
                reset();
                if (response == '413') {
                    var upload_limit = UploadValidator.getAttachmentUploadLimit();
                    var limit_size = upload_limit / 1048576; // convert to MB
                    Toaster.error("File Not Uploaded", "The file is larger than the "+limit_size.toFixed(0)+"MB maximum. Please upload a smaller file instead.");
                }
            };
        }

        uploader.onSuccessItem = function(fileItem, response) {
            var extension = fileItem.file.name.slice(fileItem.file.name.lastIndexOf('.') + 1).toLowerCase();

            if (UploadValidator.kalturaEnabled() && UploadValidator.isKalturaExtension(extension)) {
                if (response && response.id) {
                    uploader.waitForKalturaComplete = true;
                    // upload successful, notify back-end to retrieve file reference
                    KalturaResource.save({id: response.id},
                        function(ret) {
                            file = ret.file;
                            uploader.waitForKalturaComplete = undefined;
                            uploadedCallback(file);
                        }, function(ret) {
                            uploader.waitForKalturaComplete = undefined;
                        }
                    );
                }
            } else if (response && response.file) {
                file = response.file;
                uploadedCallback(file);
            }
        };

        uploader.onAfterAddingFile = function(fileItem) {
            var extension = fileItem.file.name.slice(fileItem.file.name.lastIndexOf('.') + 1).toLowerCase();

            if (UploadValidator.kalturaEnabled() && UploadValidator.isKalturaExtension(extension)) {
                KalturaResource.get({}, function(ret) {
                    fileItem.url = ret.upload_url;
                    fileItem.alias = "fileData";
                    uploader.uploadItem(fileItem);
                });
            } else {
                uploader.uploadItem(fileItem);
            }
        };

        uploader.filters.push({
            name: 'attachmentExtensionFilter',
            fn: function(item) {
                var extension = item.name.slice(item.name.lastIndexOf('.') + 1).toLowerCase();
                var valid = UploadValidator.validAttachmentExtension(extension);

                if (!valid) {
                    var allowedExtensions = UploadValidator.getAttachmentExtensionsForDisplay();
                    Toaster.error("File Not Uploaded", "Please try again with an approved file type, which includes: "+allowedExtensions+".")
                }
                return valid;
            }
        });

        uploader.filters.push({
            name: 'sizeFilter',
            fn: function(item) {
                var upload_limit = UploadValidator.getAttachmentUploadLimit();

                valid = item.size <= upload_limit;
                if (!valid) {
                    var size = item.size / 1048576; // convert to MB
                    var limit_size = upload_limit / 1048576; // convert to MB
                    Toaster.error("File Not Uploaded", "The file is larger than the "+limit_size.toFixed(0)+"MB maximum. Please upload a smaller file instead.")
                }
                return valid;
            }
        });

        return uploader;
    };

    var uploadedCallback = function(fileItem) {};

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
