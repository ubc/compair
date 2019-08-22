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
        'ubc.ctlt.compair.learning_records.learning_record',
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
            // removing the suffix of some of the actions - eg. top
            var url = response.config.url.replace(/\/(top)/g, "");
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
            topAnswer: {
                method: 'POST',
                url: '/api/courses/:courseId/assignments/:assignmentId/answers/:answerId/top',
                interceptor: cacheInterceptor
            },
            user: {url: '/api/courses/:courseId/assignments/:assignmentId/answers/user'}
        }
    );
    ret.MODEL = "Answer";
    ret.invalidListCache = invalidListCache;
    return ret;
}]);

/***** Controllers *****/
module.controller(
    "AnswerWriteModalController",
    ["$scope", "$location", "$filter", "AnswerResource", "ClassListResource", "$route", "TimerResource",
        "AssignmentResource", "Toaster", "$timeout", "UploadValidator", "CourseRole", "$uibModalInstance",
        "answerAttachService", "EditorOptions", "LearningRecord", "LearningRecordStatementHelper", "$q", "Session",
        "CourseResource", "GroupResource",
    function ($scope, $location, $filter, AnswerResource, ClassListResource, $route, TimerResource,
        AssignmentResource, Toaster, $timeout, UploadValidator, CourseRole, $uibModalInstance,
        answerAttachService, EditorOptions, LearningRecord, LearningRecordStatementHelper, $q, Session,
        CourseResource, GroupResource)
    {
        if ($scope.answer.file) {
            $scope.answer.uploadedFile = true;
            $scope.answer.existingFile = true;
        }
        $scope.method = $scope.answer.id ? 'edit' : 'create';
        $scope.preventExit = true; // user should be warned before leaving page by default
        $scope.refreshOnExit = false; // when set to true, the page refreshes when modal is closed (when data in view needs to be updated)
        $scope.UploadValidator = UploadValidator;
        $scope.tracking = LearningRecord.generateAttemptTracking();
        $scope.showAssignment = ($scope.answer.id == undefined);
        // since the "submit as" dropdown (if enabled) is default to current user (or empty if sys admin),
        // the default value of submitAsInstructorOrTA is based on canManageAssignment
        $scope.selectedIsStudent = false;
        $scope.isImpersonating = Session.isImpersonating();
        $scope.answer.rotated = false;
        $scope.saveAnswerAttempted = false;
        $scope.editorOptions = EditorOptions.basic;

        if ($scope.method == "create") {
            $scope.answer = {
                draft: true,
                course_id: $scope.courseId,
                assignment_id: $scope.assignmentId,
                comparable: true,
                existingFile: false
            };
        }
        
        if ($scope.canManageAssignment) {
            ClassListResource.get({'courseId': $scope.courseId}, function (ret) {
                $scope.classlist = ret.objects;
            });
            GroupResource.get({'courseId': $scope.courseId}, function (ret) {
                $scope.groups = ret.objects;
            });
            CourseResource.getInstructors({'id': $scope.courseId}, function (ret) {
                $scope.instructors = ret.objects;

                var found = $filter('filter')($scope.instructors, $scope.loggedInUserId, true);
                if (found != "") {
                    // preset the user_id if instructors creating new answers
                    $scope.answer.user_id = $scope.loggedInUserId;
                }

            });
        }

        LearningRecordStatementHelper.initialize_assignment_question(
            $scope.assignment, $scope.tracking
        );

        var due_date = new Date($scope.assignment.answer_end);
        if (!$scope.canManageAssignment) {
            TimerResource.get().$promise.then(function(timer) {
                var current_time = timer.date;
                var trigger_time = due_date.getTime() - current_time  - 600000; //(10 mins)
                if (trigger_time < 86400000) { //(1 day)
                    $timeout(function() {
                        $scope.showCountDown = true;
                    }, trigger_time);
                }
            });
        }

        $scope.uploader = answerAttachService.getUploader();
        $scope.resetFileUploader = answerAttachService.reset;
        $scope.canSupportPreview = answerAttachService.canSupportPreview;
        if ($scope.answer.file && $scope.canSupportPreview($scope.answer.file)) {
            answerAttachService.reuploadFile($scope.answer.file, $scope.uploader);
        }

        $scope.deleteFile = function(file) {
            $scope.answer.file = null;
            $scope.answer.uploadedFile = false;
        };

        $uibModalInstance.result.then(function (answerUpdated) {
            // closed
            if ($scope.refreshOnExit) {
                $route.reload();
            }
        }, function() {
            // dismissed
            LearningRecordStatementHelper.exited_assignment_question(
                $scope.assignment, $scope.tracking
            );
            if ($scope.refreshOnExit) {
                $route.reload();
            }
        });

        $scope.submitAsUserChanged = function(selectedUserId) {
            $scope.selectedIsStudent = $scope.instructors.filter(function (el) {
                return el.id == selectedUserId
            }).length == 0;
            if ($scope.selectedIsStudent) {
                $scope.answer.comparable = true;
            }
            $scope.answer.group_id = null;
        }

        $scope.submitAsGroupChanged = function() {
            $scope.selectedIsStudent = true;
            $scope.answer.comparable = true;
            $scope.answer.user_id = null;
        }
        
        // decide on showing inline errors
        $scope.showErrors = function($event, formValid, answerContent, existingFile, saveOnly) {

            // show errors if invalid form and no answer content written or uploaded
            if (!formValid && (!answerContent && existingFile < 1)) {

                // don't save/submit
                $event.preventDefault();

                // set helper text and Toast
                $scope.helperMsg = "Sorry, this answer couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this answer couldn't be saved yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";

                // display messages
                $scope.saveAnswerAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);

            } else {
                
                if (saveOnly) {
                    $scope.answerSubmit(true); // save draft
                } else {
                    $scope.answerSubmit(false); // submit answer
                }
                
            }//closes if valid

        };//closes showErrors

        $scope.answerSubmit = function (saveDraft) {
            $scope.submitted = true;
            $scope.saveDraft = saveDraft;
            var wasDraft = $scope.answer.draft;

            $q.all(answerAttachService.reUploadPromises($scope.uploader)).then(function() {
                var file = answerAttachService.getFile();
                if (file) {
                    $scope.answer.file = file;
                    $scope.answer.file_id = file.id;
                } else if ($scope.answer.file) {
                    $scope.answer.file_id = $scope.answer.file.id;
                } else {
                    $scope.answer.file_id = null;
                }

                // copy answer so we don't lose draft state on failed submit
                var answer = angular.merge(
                    angular.copy($scope.answer),
                    $scope.tracking.toParams()
                );
                answer.draft = !!saveDraft;

                AnswerResource.save({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId}, answer).$promise.then(
                    function (ret) {
                        $scope.answer = ret;
                        $scope.preventExit = false; // user has saved answer, does not need warning when leaving page
                        $scope.refreshOnExit = ret.draft; // if draft was saved, we need to refresh to show updated data when modal is closed

                        $uibModalInstance.close($scope.answer);
                        if (ret.draft) {
                            Toaster.success("Answer Draft Saved", "Remember to submit your answer before the deadline.");
                            if (saveDraft && answer.file) { $scope.answer.existingFile = true; }
                        } else {
                            if (wasDraft) {
                                Toaster.success("Answer Submitted");
                            }
                            else {
                                Toaster.success("Answer Updated");
                            }
                            $location.path('/course/' + $scope.courseId + '/assignment/' + $scope.assignmentId);
                            $route.reload();

                            if (!$scope.canManageAssignment) {
                                $location.search({'tab':'your_feedback', 'highlightAnswer':'1'});
                            }
                        }
                    }
                );
            }).finally(function() {
                $scope.submitted = false;
            });
        };
    }
]);

module.controller(
    "ComparisonExampleModalController",
    ["$scope", "AnswerResource", "Toaster", "UploadValidator",
        "answerAttachService", "EditorOptions", "$uibModalInstance", "$q",
    function ($scope, AnswerResource, Toaster, UploadValidator,
        answerAttachService, EditorOptions, $uibModalInstance, $q)
    {
        //$scope.courseId
        //$scope.assignmentId
        $scope.answer = typeof($scope.answer) != 'undefined' ? $scope.answer : {};
        $scope.method = $scope.answer.id ? 'edit' : 'create';
        $scope.modalInstance = $uibModalInstance;
        $scope.comparison_example = true;
        $scope.UploadValidator = UploadValidator;

        $scope.editorOptions = EditorOptions.basic;

        $scope.uploader = answerAttachService.getUploader();
        $scope.resetFileUploader = answerAttachService.reset;
        $scope.canSupportPreview = answerAttachService.canSupportPreview;
        $scope.saveAnswerAttempted = false;

        if ($scope.method == 'create') {
            $scope.answer.existingFile = false;
            // if answer is new, pre-populate the file upload area if needed
            if ($scope.answer.file) {
                $scope.answer.uploadedFile = true;
                $scope.answer.existingFile = true;
                if (answerAttachService.canSupportPreview($scope.answer.file)) {
                    answerAttachService.reuploadFile($scope.answer.file, $scope.uploader);
                }
            }
        } else if($scope.method == 'edit') {
            // refresh the answer if already exists
            AnswerResource.get({'courseId': $scope.courseId, 'assignmentId': $scope.assignmentId, 'answerId': $scope.answer.id})
            .$promise.then(
                function (ret) {
                    $scope.answer = ret;
                    if (ret.file) {
                        $scope.answer.uploadedFile = true;
                        $scope.answer.existingFile = true;
                        if (answerAttachService.canSupportPreview(ret.file)) {
                            answerAttachService.reuploadFile(ret.file, $scope.uploader);
                        }
                    }
                }
            );
        }

        $scope.deleteFile = function(file) {
            $scope.answer.file = null;
            $scope.answer.uploadedFile = false;
        };

        // decide on showing inline errors
        $scope.showErrors = function($event, formValid, answerContent, existingFile, saveOnly) {

            // show errors if invalid form and no answer content written or uploaded
            if (!formValid && (!answerContent && existingFile < 1)) {

                // don't save/submit
                $event.preventDefault();

                // set helper text and Toast
                $scope.helperMsg = "Sorry, this answer couldn't be saved yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this answer couldn't be saved yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";

                // display messages
                $scope.saveAnswerAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);

            } else {
                
                if (saveOnly) {
                    $scope.answerSubmit(true); // save draft
                } else {
                    $scope.answerSubmit(false); // submit answer
                }
                
            }//closes if valid

        };//closes showErrors
        
        $scope.answerSubmit = function (saveDraft) {
            $scope.saveDraft = saveDraft;
            $scope.submitted = true;

            $q.all(answerAttachService.reUploadPromises($scope.uploader)).then(function() {

                var file = answerAttachService.getFile();
                if (file) {
                    $scope.answer.file = file;
                    $scope.answer.file_id = file.id;
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
                            Toaster.success("Practice Answer Saved");
                            $uibModalInstance.close($scope.answer);
                        }
                    );
                }
            }).finally(function() {
                $scope.submitted = false;
            });
        };
    }
]);

// End anonymous function
})();

