// Handles answer creation and editing.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.answer',
    [
        'ngResource',
        'timer',
        'ui.bootstrap',
        'localytics.directives',
        'ubc.ctlt.acj.classlist',
        'ubc.ctlt.acj.common.form',
        'ubc.ctlt.acj.common.interceptor',
        'ubc.ctlt.acj.common.mathjax',
        'ubc.ctlt.acj.common.highlightjs',
        'ubc.ctlt.acj.common.timer',
        'ubc.ctlt.acj.assignment',
        'ubc.ctlt.acj.toaster'
    ]
);


/***** Services *****/
module.service('answerAttachService',
        ["FileUploader", "$location", "Toaster",
        function(FileUploader, $location, Toaster) {
    var file = null;
    var fileItemRef = null;

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
        fileItemRef = null;

        if (initParams) {
            if (initParams.file) {
                file = initParams.file;
            }
            if (initParams.fileRef) {
                var dummy = new FileUploader.FileItem(uploader, initParams.fileRef);
                dummy.progress = 100;
                dummy.isUploaded = true;
                dummy.isSuccess = true;
                uploader.queue.push(dummy);
                fileItemRef = dummy;
            }
        }

        uploader.onCompleteItem = onComplete();
        uploader.onErrorItem = onError();

        uploader.filters.push({
            name: 'pdfFilter',
            fn: function(item) {
                var type = '|' + item.type.slice(item.type.lastIndexOf('/') + 1) + '|';
                var valid = '|pdf|'.indexOf(type) !== -1;
                if (!valid) {
                    Toaster.error("File Type Error", "Only PDF files are accepted.")
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
                fileItemRef = fileItem;
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
            fileItemRef = null;
        };
    };

    var getFile = function() {
        return file;
    };

    var getFileRef = function() {
        return fileItemRef ? fileItemRef.file : null;
    };

    return {
        getUploader: getUploader,
        getFile: getFile,
        getFileRef: getFileRef,
        reset: reset
    };
}]);

/***** Providers *****/
module.factory("AnswerResource", ['$resource', '$cacheFactory', function ($resource, $cacheFactory) {
        var url = '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId';
        // keep a list of answer list query URLs so that we can invalidate caches for those later
        var listCacheKeys = [];
        var cache = $cacheFactory.get('$http');

        function invalidListCache(url) {
            // remove list caches. As list query may contain pagination and query parameters
            // we have to invalidate all.
            _.forEach(listCacheKeys, function(key, index, keys) {
                if (url == undefined || _.startsWith(key, url)) {
                    cache.remove(key);
                    keys.splice(index, 1);
                }
            });
        }

        var cacheInterceptor = {
            response: function(response) {
                cache.remove(response.config.url);	// remove cached GET response
                // removing the suffix of some of the actions - eg. flagged
                var url = response.config.url.replace(/\/(flagged)/g, "");
                cache.remove(url);
                url = url.replace(/\/[A-Za-z0-9_-]{22}$/g, "");

                invalidListCache(url);

                return response.data;
            }
        };
        // this function is copied from angular $http to build request URL
        function buildUrl(url, serializedParams) {
            if (serializedParams.length > 0) {
                url += ((url.indexOf('?') == -1) ? '?' : '&') + serializedParams;
            }
            return url;
        }

        // store answer list query URLs
        var cacheKeyInterceptor = {
            response: function(response) {
                var url = buildUrl(response.config.url, response.config.paramSerializer(response.config.params));
                if (url.match(/\/api\/courses\/[A-Za-z0-9_-]{22}\/assignments\/[A-Za-z0-9_-]{22}\/answers\?.*/)) {
                    listCacheKeys.push(url);
                }

                return response.data;
            }
        };

        var ret = $resource(
            url, {answerId: '@id'},
            {
                get: {url: url, cache: true, interceptor: cacheKeyInterceptor},
                save: {method: 'POST', url: url, interceptor: cacheInterceptor},
                delete: {method: 'DELETE', url: url, interceptor: cacheInterceptor},
                flagged: {
                    method: 'POST',
                    url: '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId/flagged',
                    interceptor: cacheInterceptor
                },
                comparisons: {url: '/api/courses/:courseId/assignments/:assignmentId/answers/comparisons'},
                user: {url: '/api/courses/:courseId/assignments/:assignmentId/answers/user'}
            }
        );
        ret.MODEL = "Answer";
        ret.invalidListCache = invalidListCache;
        return ret;
    }]
);

/***** Controllers *****/
module.controller(
    "AnswerWriteController",
    ["$scope", "$log", "$location", "$routeParams", "AnswerResource", "ClassListResource", "$route",
        "AssignmentResource", "TimerResource", "Toaster", "Authorize", "Session", "$timeout",
        "answerAttachService", "AttachmentResource", "EditorOptions",
    function ($scope, $log, $location, $routeParams, AnswerResource, ClassListResource, $route,
        AssignmentResource, TimerResource, Toaster, Authorize, Session, $timeout,
        answerAttachService, AttachmentResource, EditorOptions)
    {
        $scope.courseId = $routeParams['courseId'];
        var assignmentId = $routeParams['assignmentId'];
        $scope.assignment = {};
        $scope.answer = {};
        $scope.preventExit = true; //user should be warned before leaving page by default
        $scope.editorOptions = EditorOptions.basic;

        if ($route.current.method == "new") {
            $scope.showUserList = true;
            $scope.answer.draft = true;
        } else if ($route.current.method == "edit") {
            $scope.answerId = $routeParams['answerId'];
            AnswerResource.get({'courseId': $scope.courseId, 'assignmentId': assignmentId, 'answerId': $scope.answerId}).$promise.then(
                function (ret) {
                    $scope.answer = ret;

                    if (ret.file) {
                        $scope.answer.uploadedFile = ret.file
                    }
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
                }
            );
        }

        $scope.uploader = answerAttachService.getUploader();
        $scope.resetFileUploader = answerAttachService.reset();

        var countDown = function() {
            $scope.showCountDown = true;
        };

        Authorize.can(Authorize.MANAGE, AssignmentResource.MODEL, $scope.courseId).then(function(canManageAssignment){
            $scope.canManageAssignment = canManageAssignment;

            if ($route.current.method == "new" && $scope.canManageAssignment) {
                // get list of users in the course
                ClassListResource.get({'courseId': $scope.courseId}).$promise.then(
                    function (ret) {
                        $scope.classlist = ret.objects;
                    },
                    function (ret) {
                        Toaster.reqerror("No Users Found For Course ID "+$scope.courseId, ret);
                    }
                );
                Session.getUser().then(function(user) {
                    $scope.answer.user_id = user.id
                });
                // There isn't a need to submit drafts on behalf of students
                $scope.answer.draft = false;
            }
        });

        $scope.deleteFile = function(file) {
            AttachmentResource.delete({'fileId': file.id}).$promise.then(
                function (ret) {
                    Toaster.success('Attachment deleted successfully');
                    $scope.answer.file = null;
                    $scope.answer.uploadedFile = false;
                },
                function (ret) {
                    Toaster.reqerror('Attachment deletion failed', ret);
                }
            );
        };

        AssignmentResource.get({'courseId': $scope.courseId, 'assignmentId': assignmentId}).$promise.then(
            function (ret) {
                $scope.assignment = ret;
                var due_date = new Date($scope.assignment.answer_end);
                if (!$scope.canManageAssignment) {
                    TimerResource.get(
                        function (ret) {
                            var current_time = ret.date;
                            var trigger_time = due_date.getTime() - current_time  - 600000; //(10 mins)
                            if (trigger_time < 86400000) { //(1 day)
                                $timeout(countDown, trigger_time);
                            }
                        },
                        function (ret) {
                            Toaster.reqerror("Unable to get the current time", ret);
                        }
                    );
                }
            },
            function (ret) {
                Toaster.reqerror("Unable to load assignment.", ret);
            }
        );

        $scope.answerSubmit = function () {
            $scope.submitted = true;
            var wasDraft = $scope.answer.draft;

            var file = answerAttachService.getFile();
            if (file) {
                $scope.answer.file = file;
                $scope.answer.file_id = file.id
            } else if ($scope.answer.file) {
                $scope.answer.file_id = $scope.answer.file.id;
            } else {
                $scope.answer.file_id = null;
            }

            AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': assignmentId}, $scope.answer).$promise.then(
                function (ret) {
                    $scope.submitted = false;
                    $scope.preventExit = false; //user has saved answer, does not need warning when leaving page

                    if (ret.draft) {
                        Toaster.success("Saved Draft Successfully!", "Remember to submit your answer before the deadline.");
                         //user has saved answer, does not need warning when leaving page
                        $location.path('/course/' + $scope.courseId + '/assignment/' + assignmentId + '/answer/' + $scope.answer.id + '/edit');
                    } else {
                        // if was a draft, show new success message
                        if (wasDraft) {
                            Toaster.success("New Answer Posted!");
                        } else {
                            Toaster.success("Answer Updated!");
                        }
                        $location.path('/course/' + $scope.courseId + '/assignment/' +assignmentId);
                    }
                },
                function (ret) {
                    $scope.submitted = false;
                    // if answer period is not in session
                    if (ret.status == '403' && 'error' in ret.data) {
                        Toaster.error(ret.data.error);
                    } else {
                        Toaster.reqerror("Answer Save Failed.", ret);
                    }
                }
            );
        };
    }
]);


module.controller(
    "AnswerModalController",
    ["$scope", "AnswerResource", "Toaster",
        "answerAttachService", "AttachmentResource", "EditorOptions", "$modalInstance",
    function ($scope, AnswerResource, Toaster,
        answerAttachService, AttachmentResource, EditorOptions, $modalInstance)
    {
        //$scope.courseId
        //$scope.assignmentId
        $scope.answer = typeof($scope.answer) != 'undefined' ? $scope.answer : {};
        $scope.method = $scope.answer.id ? 'edit' : 'new';
        $scope.editorOptions = EditorOptions.basic;
        $scope.uploader = answerAttachService.getUploader();
        $scope.resetFileUploader = answerAttachService.reset();
        $scope.modalInstance = $modalInstance;

        if ($scope.method == 'new') {
            // if answer is new, prepopulate the file upload area if needed
            if ($scope.answer.fileRef) {
                $scope.uploader = answerAttachService.getUploader({
                    'file': $scope.answer.file,
                    'fileRef': $scope.answer.fileRef
                });
            }
        } else if($scope.method == 'edit') {
            // refresh the answer if already exists
            AnswerResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId, 'answerId': $scope.answer.id})
            .$promise.then(
                function (ret) {
                    $scope.answer = ret;
                    if (ret.file) {
                        $scope.answer.uploadedFile = ret.file
                    }
                },
                function (ret) {
                    Toaster.reqerror("Unable to retrieve answer "+answerId, ret);
                }
            );
        }

        $scope.deleteFile = function(file) {
            AttachmentResource.delete({'fileId': file.id}).$promise.then(
                function (ret) {
                    Toaster.success('Attachment deleted successfully');
                    $scope.answer.file = null;
                    $scope.answer.uploadedFile = false;
                    $scope.answer.fileRef = null;
                },
                function (ret) {
                    Toaster.reqerror('Attachment deletion failed', ret);
                }
            );
        };

        $scope.answerSubmit = function () {
            $scope.submitted = true;

            var file = answerAttachService.getFile();
            if (file) {
                $scope.answer.file = file;
                $scope.answer.file_id = file.id
            } else if ($scope.answer.file) {
                $scope.answer.file_id = $scope.answer.file.id;
            } else {
                $scope.answer.file_id = null;
            }

            if ($scope.example == true && $scope.method == 'new') {
                // save the uploaded file info in case modal is reopened
                $scope.answer.fileRef = answerAttachService.getFileRef();
                $modalInstance.close($scope.answer);
            } else {
                // save the answer
                AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $scope.answer).$promise.then(
                    function (ret) {
                        $scope.answer = ret;
                        $scope.submitted = false;

                        if ($scope.example == true) {
                            Toaster.success("Practice Answer Updated!");
                        } else {
                            if ($scope.method == 'new') {
                                Toaster.success("Answer Created!");
                            } else {
                                Toaster.success("Answer Updated!");
                            }
                        }
                        $modalInstance.close($scope.answer);
                    },
                    function (ret) {
                        $scope.submitted = false;
                        if ($scope.example == true) {
                            Toaster.reqerror("Practice Answer Save Failed.", ret);
                        } else {
                            Toaster.reqerror("Answer Save Failed.", ret);
                        }
                    }
                );
            }
        };
    }
]);

// End anonymous function
})();

