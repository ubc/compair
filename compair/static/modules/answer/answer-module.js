// Handles answer creation and editing.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.answer',
    [
        'ngResource',
        'timer',
        'ui.bootstrap',
        'localytics.directives',
        'ubc.ctlt.compair.classlist',
        'ubc.ctlt.compair.common.xapi',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.common.timer',
        'ubc.ctlt.compair.rich.content',
        'ubc.ctlt.compair.assignment',
        'ubc.ctlt.compair.attachment',
        'ubc.ctlt.compair.toaster'
    ]
);

/***** Providers *****/
module.factory("AnswerResource", ['$resource', '$cacheFactory', function ($resource, $cacheFactory) {
    var url = '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId';
    // keep a list of answer list query URLs so that we can invalidate caches for those later
    var listCacheKeys = [];
    var cache = $cacheFactory.get('$http');

        function invalidListCache(url) {
            // remove list caches. As list query may contain pagination and query parameters
            // we have to invalidate all.
            _.remove(listCacheKeys, function(key) {
                if (url == undefined || _.startsWith(key, url)) {
                    cache.remove(key);
                    return true;
                }
                return false;
            });
        }

    var cacheInterceptor = {
        response: function(response) {
            cache.remove(response.config.url);	// remove cached GET response
            // removing the suffix of some of the actions - eg. flagged
            var url = response.config.url.replace(/\/(flagged|top)/g, "");
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
            topAnswer: {
                method: 'POST',
                url: '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId/top',
                interceptor: cacheInterceptor
            },
            user: {url: '/api/courses/:courseId/assignments/:assignmentId/answers/user'},
            userUnsaved: {url: '/api/courses/:courseId/assignments/:assignmentId/answers/user', params:{draft: true, unsaved: true}, cache: false}
        }
    );
    ret.MODEL = "Answer";
    ret.invalidListCache = invalidListCache;
    return ret;
}]);

/***** Controllers *****/
module.controller(
    "AnswerWriteController",
    ["$scope", "$location", "$routeParams", "AnswerResource", "ClassListResource", "$route",
        "AssignmentResource", "Toaster", "$timeout", "UploadValidator",
        "answerAttachService", "EditorOptions", "xAPI", "xAPIStatementHelper", "resolvedData",
    function ($scope, $location, $routeParams, AnswerResource, ClassListResource, $route,
        AssignmentResource, Toaster, $timeout, UploadValidator,
        answerAttachService, EditorOptions, xAPI, xAPIStatementHelper, resolvedData)
    {
        $scope.courseId = $routeParams.courseId;
        $scope.assignmentId = $routeParams.assignmentId;
        $scope.answerId = $routeParams.answerId || undefined;

        $scope.course = resolvedData.course;
        $scope.assignment = resolvedData.assignment;
        $scope.answer = resolvedData.answer || {};
        if ($scope.answer.file) {
            $scope.answer.uploadedFile = true;
        }
        $scope.loggedInUserId = resolvedData.loggedInUser.id;
        $scope.canManageAssignment = resolvedData.canManageAssignment;

        $scope.method = $scope.answer.id ? 'edit' : 'create';
        $scope.preventExit = true; //user should be warned before leaving page by default
        $scope.UploadValidator = UploadValidator;
        $scope.tracking = xAPI.generateTracking();
        $scope.editorOptions = xAPI.ckeditorContentTracking(EditorOptions.basic, function(duration) {
            xAPIStatementHelper.interacted_answer_solution(
                $scope.answer, $scope.tracking.getRegistration(), duration
            );
        });

        if ($scope.method == "create") {
            $scope.answer = {
                draft: true,
                course_id: $scope.courseId,
                assignment_id: $scope.assignmentId
            };
            if (!resolvedData.answerUnsaved.objects.length) {
                // if no answers found, create a new draft answer
                AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, {draft: true}).$promise.then(
                    function (ret) {
                        // set answer id to new answer id
                        $scope.answer.id = ret.id;
                    }
                );
            } else {
                // draft found for user, use it
                $scope.answer.id = resolvedData.answerUnsaved.objects[0].id;
            }
        }
        if ($scope.canManageAssignment) {
            // get list of users in the course
            ClassListResource.get({'courseId': $scope.courseId}).$promise.then(
                function (ret) {
                    $scope.classlist = ret.objects;
                }
            );
            $scope.answer.user_id = $scope.loggedInUserId;
        }

        if ($scope.method == "create" || !$scope.answer.draft) {
            xAPIStatementHelper.initialize_assignment_question(
                $scope.assignment, $scope.tracking.getRegistration()
            );
        } else {
            xAPIStatementHelper.resume_assignment_question(
                $scope.assignment, $scope.tracking.getRegistration()
            );
        }

        var due_date = new Date($scope.assignment.answer_end);
        if (!$scope.canManageAssignment) {
            var current_time = resolvedData.timer.date;
            var trigger_time = due_date.getTime() - current_time  - 600000; //(10 mins)
            if (trigger_time < 86400000) { //(1 day)
                $timeout(function() {
                    $scope.showCountDown = true;
                }, trigger_time);
            }
        }

        $scope.uploader = answerAttachService.getUploader();
        $scope.resetFileUploader = function() {
            var file = answerAttachService.getFile();
            if (file) {
                xAPIStatementHelper.deleted_answer_attachment(
                    file, $scope.answer, $scope.tracking.getRegistration()
                );
            }
            answerAttachService.reset();
        };
        answerAttachService.setUploadedCallback(function(file) {
            xAPIStatementHelper.attached_answer_attachment(
                file, $scope.answer, $scope.tracking.getRegistration()
            );
        });

        $scope.deleteFile = function(file) {
            $scope.answer.file = null;
            $scope.answer.uploadedFile = false;

            xAPIStatementHelper.deleted_answer_attachment(
                file, $scope.answer, $scope.tracking.getRegistration()
            );
        };

        $scope.trackExited = function() {
            xAPIStatementHelper.exited_assignment_question(
                $scope.assignment, $scope.tracking.getRegistration(), $scope.tracking.getDuration()
            );
        };

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

            // copy answer so we don't lose draft state on failed submit
            var answer = angular.copy($scope.answer);
            answer.draft = $scope.saveDraft;
            answer.tracking = $scope.tracking.toParams();

            AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, answer).$promise.then(
                function (ret) {
                    $scope.answer = ret;
                    $scope.preventExit = false; //user has saved answer, does not need warning when leaving page

                    if (ret.draft) {
                        Toaster.success("Draft Saved", "Remember to submit your answer before the deadline.");
                        $location.path('/course/' + $scope.courseId + '/assignment/' + $scope.assignmentId + '/answer/' + $scope.answer.id + '/edit');
                    } else {
                        // if was a draft, show new success message
                        if (wasDraft) {
                            Toaster.success("Answer Saved");
                        } else {
                            Toaster.success("Answer Updated");
                        }
                        $location.path('/course/' + $scope.courseId + '/assignment/' +$scope.assignmentId);
                    }
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }
]);


module.controller(
    "AnswerEditModalController",
    ["$scope", "AnswerResource", "Toaster", "xAPI", "xAPIStatementHelper",
        "answerAttachService", "UploadValidator", "EditorOptions", "$uibModalInstance",
    function ($scope, AnswerResource, Toaster, xAPI, xAPIStatementHelper,
        answerAttachService, UploadValidator, EditorOptions, $uibModalInstance)
    {
        //$scope.courseId
        //$scope.assignmentId
        $scope.assignment = typeof($scope.assignment) != 'undefined' ? $scope.assignment : {};
        $scope.answer = typeof($scope.answer) != 'undefined' ? $scope.answer : {};
        $scope.method = 'edit';
        $scope.modalInstance = $uibModalInstance;
        $scope.UploadValidator = UploadValidator;
        $scope.tracking = xAPI.generateTracking();
        $scope.editorOptions =  xAPI.ckeditorContentTracking(EditorOptions.basic, function(duration) {
            xAPIStatementHelper.interacted_answer_solution(
                $scope.answer, $scope.tracking.getRegistration(), duration
            );
        });

        AnswerResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId, 'answerId': $scope.answer.id}).$promise.then(
            function (ret) {
                $scope.answer = ret;
                if (ret.file) {
                    $scope.answer.uploadedFile = true;
                }
            }
        );
        xAPIStatementHelper.resume_assignment_question(
            $scope.assignment, $scope.tracking.getRegistration()
        );

        $scope.uploader = answerAttachService.getUploader();
        $scope.resetFileUploader = function() {
            var file = answerAttachService.getFile();
            if (file) {
                xAPIStatementHelper.deleted_answer_attachment(
                    file, $scope.answer, $scope.tracking.getRegistration()
                );
            }
            answerAttachService.reset();
        };
        answerAttachService.setUploadedCallback(function(file) {
            xAPIStatementHelper.attached_answer_attachment(
                file, $scope.answer, $scope.tracking.getRegistration()
            );
        });

        $scope.deleteFile = function(file) {
            $scope.answer.file = null;
            $scope.answer.uploadedFile = false;

            xAPIStatementHelper.deleted_answer_attachment(
                file, $scope.answer, $scope.tracking.getRegistration()
            );
        };

        // track modal exited
        $scope.modalInstance.result.then(function (answerUpdated) {
            // closed
        }, function() {
            // dismissed
            xAPIStatementHelper.exited_assignment_question(
                $scope.assignment, $scope.tracking.getRegistration(), $scope.tracking.getDuration()
            );
        });

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

            $scope.answer.tracking =$scope.tracking.toParams();
            // save the answer
            AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $scope.answer).$promise.then(
                function (ret) {
                    $scope.answer = ret;
                    Toaster.success("Answer Updated");
                    $uibModalInstance.close($scope.answer);
                }
            ).finally(function() {
                $scope.submitted = false;
            });
        };
    }
]);

module.controller(
    "ComparisonExampleModalController",
    ["$scope", "AnswerResource", "Toaster", "UploadValidator",
        "answerAttachService", "EditorOptions", "$uibModalInstance",
    function ($scope, AnswerResource, Toaster, UploadValidator,
        answerAttachService, EditorOptions, $uibModalInstance)
    {
        //$scope.courseId
        //$scope.assignmentId
        $scope.answer = typeof($scope.answer) != 'undefined' ? $scope.answer : {};
        $scope.method = $scope.answer.id ? 'edit' : 'create';
        $scope.modalInstance = $uibModalInstance;
        $scope.comparison_example = true;
        $scope.UploadValidator = UploadValidator;

        $scope.editorOptions = EditorOptions.basic;

        if ($scope.method == 'create') {
            // if answer is new, pre-populate the file upload area if needed
            if ($scope.answer.file) {
                $scope.answer.uploadedFile = true;
            }
        } else if($scope.method == 'edit') {
            // refresh the answer if already exists
            AnswerResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId, 'answerId': $scope.answer.id})
            .$promise.then(
                function (ret) {
                    $scope.answer = ret;
                    if (ret.file) {
                        $scope.answer.uploadedFile = true;
                    }
                }
            );
        }

        $scope.uploader = answerAttachService.getUploader();
        $scope.resetFileUploader = answerAttachService.reset();

        $scope.deleteFile = function(file) {
            $scope.answer.file = null;
            $scope.answer.uploadedFile = false;
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

            if ($scope.method == 'create') {
                // save the uploaded file info in case modal is reopened
                $uibModalInstance.close($scope.answer);
            } else {
                // save the answer
                AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, $scope.answer).$promise.then(
                    function (ret) {
                        $scope.answer = ret;
                        Toaster.success("Practice Answer Updated");
                        $uibModalInstance.close($scope.answer);
                    }
                ).finally(function() {
                    $scope.submitted = false;
                });
            }
        };
    }
]);

// End anonymous function
})();

