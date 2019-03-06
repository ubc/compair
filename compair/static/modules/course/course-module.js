// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

function combineDateTime(datetime) {
    var date = new Date(datetime.date);
    var time = new Date(datetime.time);
    date.setHours(time.getHours(), time.getMinutes(), time.getSeconds(), time.getMilliseconds());
    return date;
}

function getWeeksDelta(firstDate, secondDate) {
    firstDate = firstDate == null ? moment() : moment(firstDate);
    secondDate = secondDate == null ? moment() : moment(secondDate);
    // By default, moment#diff will return a number rounded towards zero (down for positive, up for negative).
    // we instead want to always Math.floor for both positive and negative numbers
    return Math.floor(firstDate.startOf('day').diff(secondDate.startOf('day'), 'weeks', true));
}

function getNewDuplicateDate(originalDate, weekDelta) {
    originalDate = originalDate == null ? moment() : moment(originalDate);
    weekDelta = weekDelta || 0;
    return originalDate.add(weekDelta, 'weeks')
}

var module = angular.module('ubc.ctlt.compair.course',
    [
        'angularMoment',
        'ngResource',
        'ngRoute',
        'ui.bootstrap',
        'ubc.ctlt.compair.comment',
        'ubc.ctlt.compair.learning_records.learning_record',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.common.interceptor',
        'ubc.ctlt.compair.comparison',
        'ubc.ctlt.compair.assignment',
        'ubc.ctlt.compair.rich.content',
        'ubc.ctlt.compair.toaster'
    ]
);

/***** Directives *****/
module.directive('courseMetadata', function() {

    return {
        restrict : 'E',
        scope: true,
        templateUrl: 'modules/common/element-metadata-template.html',
        replace: true,
        link: function ($scope, $element, $attributes) {
            $scope.metadataName = $attributes.name;
        },
        controller: ["$scope", "$filter", "CoursePermissions",
            function ($scope, $filter, CoursePermissions) {
                $scope.$watchCollection("[course, course.status, metadataName]", function(newStatus){

                    var permissions = CoursePermissions.getAll($scope.course);

                    if ($scope.course.status !== undefined) {
                        var courseId = $scope.course.id;
                        var course = $scope.course;
                        var allMetadata = {
                            'editLink' : {
                                'label': "Edit",
                                'href' : "#/course/" + courseId + "/edit",
                                'show' : {
                                    'user' : false,
                                    'instructor' : permissions.canEdit
                                }
                            },
                            'duplicateLink' : {
                                'label': "Duplicate",
                                'href' : "#/course/" + courseId + "/duplicate",
                                'show' : {
                                    'user' : false,
                                    'instructor' : permissions.canEdit
                                }
                            },
                            'assignmentCount' : {
                                'label': course.assignment_count + " assignment" + (course.assignment_count != 1 ? "s" : ""),
                                'title': course.assignment_count + " assignment" + (course.assignment_count != 1 ? "s" : ""),
                                'show' : {
                                    'user' : false,
                                    'instructor' : true
                                }
                            },
                            'assignmentCountStudent' : {
                                'label': course.student_assignment_count + " assignment" + (course.student_assignment_count != 1 ? "s" : "") + " total",
                                'title': course.student_assignment_count + " assignment" + (course.student_assignment_count != 1 ? "s" : ""),
                                'show' : {
                                    'user' : true,
                                    'instructor' : false
                                }
                            },
                            'assignmentsToDo' : {
                                'label': course.status.incomplete_assignments + " assignment" + (course.status.incomplete_assignments != 1 ? "s" : "") + " to do",
                                'title': course.status.incomplete_assignments + " unfinished",
                                'class': 'label label-warning',
                                'show' : {
                                    'user' : permissions.hasAssignmentsLeft,
                                    'instructor' : false
                                }
                            },
                            'noAssignmentsToDo' : {
                                'label': "No assignments to do",
                                'title': course.status.incomplete_assignments + " unfinished",
                                'show' : {
                                    'user' : !permissions.hasAssignmentsLeft,
                                    'instructor' : false
                                }
                            },
                            'studentCount' : {
                                'label': course.student_count + " student" + (course.student_count != 1 ? "s" : ""),
                                'show' : {
                                    'user' : false,
                                    'instructor' : permissions.canEdit
                                }
                            },
                            'courseDates' : {
                                'label': course.year + " " + course.term,
                                'show' : {
                                    'user' : true,
                                    'instructor' : true
                                }
                            },
                            'sandbox' : {
                                'label': "Sandbox Course",
                                'show' : {
                                    'user' : false,
                                    'instructor' : permissions.canEdit && course.isSandbox
                                }
                            },
                            'deleteLink' : {
                                'label': 'Delete',
                                'class': 'pointer',
                                'title' : "Delete",
                                'confirmationNeeded' : 'deleteCourse(course)' ,
                                'confirmationWarning': course.delete_warning,
                                'keyword' : "course and its assignments",
                                'show' : {
                                    'user' : false,
                                    'instructor' : permissions.canDelete
                                }
                            }
                        };

                        if (allMetadata[$scope.metadataName]) {
                            if (course.canManageAssignment && allMetadata[$scope.metadataName].show.instructor) {
                                $scope.meta = allMetadata[$scope.metadataName];
                            }
                            else if (!course.canManageAssignment && allMetadata[$scope.metadataName].show.user) {
                                $scope.meta = allMetadata[$scope.metadataName];
                            }
                            else {
                                $scope.meta = { 'hide': true };
                            }
                        }
                    }
                    else {
                        $scope.meta = { 'hide': true };
                    }
                });
            }
        ]
    };
});

module.directive('courseActionButton', function() {

    return {
        restrict : 'E',
        scope: false,
        templateUrl: 'modules/common/element-button-template.html',
        replace: true,
        link: function ($scope, $element, $attributes) {
            $scope.actionElementName = $attributes.name;
        },
        controller: ["$scope", "$filter", "CoursePermissions",
            function ($scope, $filter, CoursePermissions) {
                $scope.$watchCollection("[course, course.status, actionElementName]", function(newStatus){

                    var permissions = CoursePermissions.getAll($scope.course);

                    if ($scope.course.status !== undefined) {
                        var courseId = $scope.course.id;
                        var course = $scope.course;
                        var allButtons = {
                            'viewCourse' : {
                                'label' : "See Assignments",
                                'href'  : "#/course/" + courseId,
                                'class' : 'btn-success',
                                'title' : "See Assignments",
                                'show' : {
                                    'user' : true,
                                    'instructor' : true
                                }
                            },
                        };

                        if (allButtons[$scope.actionElementName]) {
                            if (course.canManageAssignment && allButtons[$scope.actionElementName].show.instructor) {
                                $scope.button = allButtons[$scope.actionElementName];
                            }
                            else if (!course.canManageAssignment && allButtons[$scope.actionElementName].show.user) {
                                $scope.button = allButtons[$scope.actionElementName];
                            }
                            else {
                                $scope.button = { 'hide': true };
                            }
                        }
                    }
                    else {
                        $scope.button = { 'hide': true };
                    }
                });
            }
        ]
    };
});

/***** Providers *****/
module.factory('CourseResource',
    ["$q", "$routeParams", "$resource", "Interceptors",
    function($q, $routeParams, $resource, Interceptors)
{
    var url = '/api/courses/:id';
    var ret = $resource('/api/courses/:courseId', {id: '@id'},
        {
            // would enable caching for GET but there's no automatic cache
            // invalidation, I don't want to deal with that manually
            'get': {url: url, cache: true},
            'save': {method: 'POST', url: url, interceptor: Interceptors.cache},
            'delete': {method: 'DELETE', url: url, interceptor: Interceptors.cache},
            'createDuplicate': {method: 'POST', url: '/api/courses/:id/duplicate'},
            'getCurrentUserStatus': {url: '/api/courses/:id/assignments/status'},
            'getStudents': {url: '/api/courses/:id/users/students'},
            'getInstructors': {url: '/api/courses/:id/users/instructors'},
        }
    );
    ret.MODEL = "Course"; // add constant to identify the model
        // being used, this is for permissions checking
        // and should match the server side model name
    return ret;
}]);

module.factory( "CoursePermissions", function (){

    return {
        'getAll' : function(course) {
            return {
                'canEdit'   : !!course.canEditCourse,
                'canDelete' : !!course.canDeleteCourse,
                'isSandbox' : !!course.sandbox,
                'hasAssignmentsLeft' : !!course.status && course.status.incomplete_assignments > 0,
            }
        }
    }
});

/***** Controllers *****/
module.controller(
    'CourseAssignmentsController',
    ["$scope", "$routeParams", "CourseResource", "AssignmentResource", "AssignmentPermissions",
    "AnswerResource", "moment", "resolvedData", "Toaster", "LearningRecordStatementHelper", "$uibModal",
   function($scope, $routeParams, CourseResource, AssignmentResource, AssignmentPermissions,
            AnswerResource, moment, resolvedData, Toaster, LearningRecordStatementHelper, $uibModal)
    {
        // get course info
        $scope.courseId = $routeParams.courseId;

        $scope.course = resolvedData.course;
        $scope.loggedInUserId = resolvedData.loggedInUser.id;
        $scope.assignments = resolvedData.courseAssignments.objects;
        $scope.count = {};
        $scope.canEditCourse = resolvedData.canEditCourse;
        $scope.canCreateAssignment = resolvedData.canCreateAssignment;
        $scope.canManageAssignment = resolvedData.canManageAssignment;
        $scope.canManageUsers = resolvedData.canManageUsers;

        // get course assignments status
        $scope.assignments.forEach(function(assignment) {
            if (assignment.lti_linked) {
                assignment.delete_warning = "This will also unlink all LTI direct links to this assignment.";
            }
        });

        $scope.openAnswerModal = function($args) {

            var modalScope = $scope.$new();
            modalScope.assignment = $args.assignment;
            modalScope.courseId = angular.copy($scope.courseId);
            modalScope.assignmentId = angular.copy($args.assignment.id);

            modalScope.course = $scope.course;
            modalScope.answer = {};
            modalScope.loggedInUserId = resolvedData.loggedInUser.id;
            modalScope.canManageAssignment = resolvedData.canManageAssignment;

            if ($args.answerId) {
                modalScope.answerId = $args.answerId;
                AnswerResource.get({'courseId': modalScope.courseId, 'assignmentId': modalScope.assignmentId, 'answerId': modalScope.answerId}).$promise.then(
                    function (ret) {
                        modalScope.answer = ret;
                        $scope.modalInstance = $uibModal.open({
                            animation: true,
                            backdrop: 'static',
                            controller: "AnswerWriteModalController",
                            templateUrl: 'modules/answer/answer-modal-partial.html',
                            scope: modalScope
                        });
                    }
                );
            }
            else {
                $scope.modalInstance = $uibModal.open({
                    animation: true,
                    backdrop: 'static',
                    controller: "AnswerWriteModalController",
                    templateUrl: 'modules/answer/answer-modal-partial.html',
                    scope: modalScope
                });
            }

        }

        CourseResource.getCurrentUserStatus({'id': $scope.courseId}).$promise.then(
            function(ret) {
                var statuses = ret.statuses;

                // get course assignments status
                $scope.assignments.forEach(function(assignment) {
                    assignment.status = statuses[assignment.id]

                    // comparison count
                    assignment.comparisons_left = assignment.status.comparisons.left;
                    assignment.self_evaluation_needed = assignment.enable_self_evaluation && !assignment.status.comparisons.self_evaluation_completed;

                    // if evaluation period is set answers can be seen after it ends
                    if (assignment.compare_end) {
                        assignment.see_answers = assignment.after_comparing;
                    // if an evaluation period is NOT set - answers can be seen after req met
                    } else {
                        assignment.see_answers = assignment.after_comparing && assignment.comparisons_left == 0;
                    }
                });
            }
        );

        $scope.filters = ['All course assignments'];
        if ($scope.canManageAssignment) {
            $scope.filters.push('Assignments being answered', 'Assignments being compared', 'Upcoming assignments');
        } else {
            $scope.filters.push('My unfinished assignments', 'Assignments with drafts', 'Assignments with feedback');
        }
        $scope.filter = $scope.filters[0];

        $scope.sortOptions = ['Assignment start date', 'Answer due date', 'Comparisons due date'];
        $scope.sortOrder = $scope.sortOptions[0];

        $scope.deleteAssignment = function(assignment) {
            AssignmentResource.delete({'courseId': assignment.course_id, 'assignmentId': assignment.id}).$promise.then(
                function (ret) {
                    Toaster.success("Assignment Deleted");
                    $scope.assignments = _.filter($scope.assignments, function(a) {
                        return a.id != assignment.id;
                    });
                }
            );
        };

        $scope.assignmentFilter = function(filter) {
            return function(assignment) {

                var permissions = AssignmentPermissions.getAll(assignment, $scope.canManageAssignment, $scope.loggedInUserId);

                switch(filter) {
                    // return all assignments
                    case "All course assignments":
                        return true;
                    // INSTRUCTOR: return all assignments in answer period
                    case "Assignments being answered":
                        return assignment.answer_period;
                    // INSTRUCTOR: return all assignments in comparison period
                    case "Assignments being compared":
                        return assignment.compare_period;
                    // INSTRUCTOR: return all assignments that are unavailable to students at the moment
                    case "Upcoming assignments":
                        return !assignment.available;
                    // STUDENTS: return all assignments that need to be answered or compared
                    case "My unfinished assignments":
                        return (permissions.canAnswer && permissions.needsAnswer) ||
                        (permissions.canCompare && permissions.needsCompare) ||
                        (permissions.canSelfEval && permissions.needsSelfEval);
                    // STUDENTS: return all assignments that have a saved draft answer, comparison, or self-eval
                    case "Assignments with drafts":
                        return (permissions.canAnswer && permissions.needsAnswer && permissions.hasDraftAnswer) ||
                            (permissions.canCompare && permissions.needsCompare && permissions.hasDraftComparison) ||
                            (permissions.canCompare && permissions.needsSelfEval && permissions.hasDraftSelfEval);
                    // STUDENTS: return all assignments that have received feedback
                    case "Assignments with feedback":
                        return permissions.hasFeedback;
                    default:
                        return false;
                }
            }
        }

        $scope.assignmentSortOrder = function(sortOrder) {
            switch (sortOrder) {
                case "Answer due date":
                    return function(assignment) {
                        // return rather undefined if empty, otherwise answer_end if it occurs in the future
                        if (moment(assignment.answer_end).diff(moment()) > 0) {
                            return moment(assignment.answer_end).valueOf();
                        }
                        return undefined;
                    };
                    break;
                case "Comparisons due date":
                    return function(assignment) {
                        // return rather undefined if empty, otherwise compare_end if it occurs in the future
                        if (assignment.compare_end && moment(assignment.compare_end).diff(moment()) > 0) {
                            return moment(assignment.compare_end).valueOf();
                        }
                        else if (!assignment.compare_end && moment(assignment.answer_end).diff(moment()) > 0) {
                            return moment(assignment.answer_end).valueOf();
                        }
                        return undefined;
                    };
                    break;
                case "Assignment start date":
                default:
                    return function(assignment) {
                        return - moment(assignment.answer_start).valueOf();
                    }
            }
        }

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            LearningRecordStatementHelper.filtered_page({
                display: $scope.filter
            });
        };
        $scope.$watchCollection('filter', filterWatcher);
    }
]);

module.controller(
    'CourseSelectModalController',
    ["$rootScope", "$scope", "$uibModalInstance", "AssignmentResource",
     "Session", "CourseResource", "Toaster", "UserResource", "LTI", "LearningRecordStatementHelper",
    function ($rootScope, $scope, $uibModalInstance, AssignmentResource,
              Session, CourseResource, Toaster, UserResource, LTI, LearningRecordStatementHelper) {

        $scope.submitted = false;
        $scope.totalNumCourses = 0;
        $scope.courseFilters = {
            page: 1,
            perPage: 10
        };
        $scope.courses = [];
        $scope.originalCourse = {};

        $scope.selectCourse = function(courseId) {
            $uibModalInstance.close(courseId);
        };

        $scope.showDuplicateForm = false;
        $scope.course = {
            year: new Date().getFullYear(),
            name: LTI.getCourseName()
        };
        $scope.format = 'dd-MMMM-yyyy';
        $scope.date = {
            'course_start': {'date': null, 'time': new Date().setHours(0, 0, 0, 0)},
            'course_end': {'date': null, 'time': new Date().setHours(23, 59, 0, 0)},
        };

        $scope.selectDuplicateCourse = function(course) {
            $scope.showDuplicateForm = true;
            $scope.originalCourse = angular.copy(course);
        };

        $scope.datePickerOpen = function($event, object) {
            $event.preventDefault();
            $event.stopPropagation();

            object.opened = true;
        };

        $scope.save = function() {
            $scope.submitted = true;

            if ($scope.date.course_start.date != null) {
                $scope.course.start_date = combineDateTime($scope.date.course_start);
            } else {
                $scope.course.start_date = null;
            }
            if ($scope.date.course_end.date != null) {
                $scope.course.end_date = combineDateTime($scope.date.course_end);
            } else {
                $scope.course.end_date = null;
            }

            if ($scope.course.start_date == null) {
                Toaster.warning('Course Not Saved', 'Please indicate the course start time and save again.');
                $scope.submitted = false;
                return;
            }
            else if ($scope.course.end_date != null && $scope.course.start_date > $scope.course.end_date) {
                Toaster.warning('Course Not Saved', 'Please set course end time after course start time and save again.');
                $scope.submitted = false;
                return;
            }

            CourseResource.save({}, $scope.course, function (ret) {
                Toaster.success("Course Saved");
                // refresh permissions
                Session.expirePermissions();
                $scope.selectCourse(ret.id);
            }).$promise.finally(function() {
                $scope.submitted = false;
            });
        };

        $scope.closeDuplicate = function(courseId) {
            $scope.selectCourse(courseId);
        };
        $scope.dismissDuplicate = function() {
            $scope.showDuplicateForm = false;
        };

        $scope.updateCourseList = function() {
            UserResource.getUserCourses($scope.courseFilters).$promise.then(
                function(ret) {
                    $scope.courses = ret.objects;
                    $scope.totalNumCourses = ret.total;
                }
            );
        };

        var filterWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            $scope.updateCourseList();
            LearningRecordStatementHelper.filtered_modal("Select Course", $scope.courseFilters);
        };
        $scope.$watchCollection('courseFilters', filterWatcher);
        $scope.updateCourseList();
    }
]);


module.controller(
    'CourseDuplicateController',
    ["$rootScope", "$scope", "AssignmentResource", "moment", '$routeParams', '$location',
     "Session", "CourseResource", "Toaster", "UserResource",
    function ($rootScope, $scope, AssignmentResource, moment, $routeParams, $location,
              Session, CourseResource, Toaster, UserResource) {

        $scope.showAssignments = false;
        $scope.submitted = false;
        $scope.format = 'dd-MMMM-yyyy';

        $scope.setupDuplicateCourse = function() {
            $scope.duplicateCourse = {
                name: $scope.originalCourse.name,
                year: new Date().getFullYear(),
                term: $scope.originalCourse.term,
                sandbox: $scope.originalCourse.sandbox,
                date: {
                    course_start: {date: null, time: new Date().setHours(0, 0, 0, 0)},
                    course_end: {date: null, time: new Date().setHours(23, 59, 0, 0)}
                }
            };
            if (!$scope.originalCourse.id) {
                return;
            }

            if ($scope.originalCourse.start_date) {
                var weekDelta = getWeeksDelta(moment(), $scope.originalCourse.start_date);
                $scope.duplicateCourse.date.course_start.date = getNewDuplicateDate($scope.originalCourse.start_date, weekDelta).toDate();

                if ($scope.originalCourse.end_date) {
                    $scope.duplicateCourse.date.course_end.date = getNewDuplicateDate($scope.originalCourse.end_date, weekDelta).toDate();
                }
            }

            $scope.originalAssignments = [];
            $scope.duplicateAssignments = [];
            AssignmentResource.get({'courseId': $scope.originalCourse.id}).$promise.then(
                function (ret) {
                    $scope.originalAssignments = ret.objects;
                    $scope.adjustDuplicateAssignmentDates();
                }
            );
        };

        $scope.canGoBack = function(theFormToCheck) {
            return (theFormToCheck.$pristine || confirm('Are you sure you want to leave this page? Any dates you\'ve manually changed for assignments here will be lost.'));
        }

        $scope.adjustDuplicateAssignmentDates = function() {
            // startPoint is original course start_date if set
            // if not set, then it is the earliest assignment answer start date
            // duplicated assignment dates will moved around based on this date and the original assignments dates
            var startPoint = null;
            if ($scope.originalCourse.start_date) {
                startPoint = moment($scope.originalCourse.start_date).startOf('isoWeek');
            } else if($scope.originalAssignments.length > 0) {
                startPoint = moment($scope.originalAssignments[0].answer_start).startOf('isoWeek');
                angular.forEach($scope.originalAssignments, function(assignment) {
                    var answerStartPoint = moment(assignment.answer_start).startOf('isoWeek');
                    if (answerStartPoint < startPoint) {
                        startPoint = answerStartPoint;
                    }
                });
            }
            var weekDelta = getWeeksDelta($scope.duplicateCourse.date.course_start.date, startPoint);

            $scope.duplicateAssignments = [];
            angular.forEach($scope.originalAssignments, function(assignment) {
                var duplicate_assignment = {
                    id: assignment.id,
                    name: assignment.name,
                    date: {
                        astart: {date: null, time: new Date().setHours(0, 0, 0, 0)},
                        aend: {date: null, time: new Date().setHours(23, 59, 0, 0)},
                        cstart: {date: null, time: new Date().setHours(0, 0, 0, 0)},
                        cend: {date: null, time: new Date().setHours(23, 59, 0, 0)},
                        sestart: {date: null, time: new Date().setHours(0, 0, 0, 0)},
                        seend: {date: null, time: new Date().setHours(23, 59, 0, 0)},
                    },
                    enable_self_evaluation: assignment.enable_self_evaluation,
                }

                duplicate_assignment.date.astart.date = getNewDuplicateDate(assignment.answer_start, weekDelta).toDate();
                duplicate_assignment.date.astart.time = moment(assignment.answer_start).toDate();

                duplicate_assignment.date.aend.date = getNewDuplicateDate(assignment.answer_end, weekDelta).toDate();
                duplicate_assignment.date.aend.time = moment(assignment.answer_end).toDate();

                if (assignment.compare_start) {
                    duplicate_assignment.date.cstart.date = getNewDuplicateDate(assignment.compare_start, weekDelta).toDate();
                    duplicate_assignment.date.cstart.time = moment(assignment.compare_start).toDate();
                }

                if (assignment.compare_end) {
                    duplicate_assignment.date.cend.date = getNewDuplicateDate(assignment.compare_end, weekDelta).toDate();
                    duplicate_assignment.date.cend.time = moment(assignment.compare_end).toDate();
                }

                if (assignment.compare_start && assignment.compare_end) {
                    duplicate_assignment.availableCheck = true;
                }

                if (assignment.self_eval_start) {
                    duplicate_assignment.date.sestart.date = getNewDuplicateDate(assignment.self_eval_start, weekDelta).toDate();
                    duplicate_assignment.date.sestart.time = moment(assignment.self_eval_start).toDate();
                }

                if (assignment.self_eval_start) {
                    duplicate_assignment.selfEvalCheck = true;
                }

                if (assignment.self_eval_end) {
                    duplicate_assignment.date.seend.date =  getNewDuplicateDate(assignment.self_eval_end, weekDelta).toDate();
                    duplicate_assignment.date.seend.time = moment(assignment.self_eval_end).toDate();
                }

                $scope.duplicateAssignments.push(duplicate_assignment);
            });
        };

        $scope.datePickerOpen = function($event, object) {
            $event.preventDefault();
            $event.stopPropagation();

            object.opened = true;
        };

        $scope.datePickerMinDate = function() {
            var dates = Array.prototype.slice.call(arguments).filter(function(val) {
                return typeof val !== 'undefined' && val !== null;
            });
            if (dates.length == 0) {
                return null;
            }
            return moment(dates.reduce(function (left, right) {
                return moment(left) > moment(right) ? left : right;
            }, dates[0])).toDate();
        };

        $scope.datePickerMaxDate = function() {
            var dates = Array.prototype.slice.call(arguments).filter(function(val) {
                return typeof val !== 'undefined' && val !== null;
            });
            if (dates.length == 0) {
                return null;
            }
            return moment(dates.reduce(function (left, right) {
                return moment(left) < moment(right) ? left : right;
            }, dates[0])).toDate();
        };

        $scope.duplicateNext = function() {
            $scope.showAssignments = true;
            $scope.adjustDuplicateAssignmentDates();
        }

        $scope.duplicate = function() {
            $scope.submitted = true;
            $scope.duplicateCourse.assignments = [];

            if ($scope.duplicateCourse.date.course_start.date != null) {
                $scope.duplicateCourse.start_date = combineDateTime($scope.duplicateCourse.date.course_start);
            } else {
                $scope.duplicateCourse.start_date = null;
            }
            if ($scope.duplicateCourse.date.course_end.date != null) {
                $scope.duplicateCourse.end_date = combineDateTime($scope.duplicateCourse.date.course_end);
            } else {
                $scope.duplicateCourse.end_date = null;
            }

            if ($scope.duplicateCourse.start_date == null) {
                Toaster.warning('Course Not Saved', 'Please indicate the course start time and try again.');
                $scope.submitted = false;
                return;
            }
            else if ($scope.duplicateCourse.start_date != null && $scope.duplicateCourse.end_date != null && $scope.duplicateCourse.start_date > $scope.duplicateCourse.end_date) {
                Toaster.warning('Course Not Duplicated', 'Please set course end time after course start time and try again.');
                $scope.submitted = false;
                return;
            }

            for (var index = 0; index < $scope.duplicateAssignments.length; index++) {
                var assignment = $scope.duplicateAssignments[index];

                var assignment_submit = {
                    id: assignment.id,
                    name: assignment.name,
                    answer_start: combineDateTime(assignment.date.astart),
                    answer_end: combineDateTime(assignment.date.aend),
                    compare_start: combineDateTime(assignment.date.cstart),
                    compare_end: combineDateTime(assignment.date.cend),
                    enable_self_evaluation: assignment.enable_self_evaluation,
                    self_eval_start: assignment.enable_self_evaluation && assignment.selfEvalCheck? combineDateTime(assignment.date.sestart) : null,
                    self_eval_end: assignment.enable_self_evaluation && assignment.selfEvalCheck? combineDateTime(assignment.date.seend) : null,
                }

                // answer end datetime has to be after answer start datetime
                if (assignment_submit.answer_start >= assignment_submit.answer_end) {
                    Toaster.warning('Assignment Not Duplicated', 'Please set answer end time after answer start time and try again.');
                    $scope.submitted = false;
                    return;
                } else if (assignment.availableCheck && assignment_submit.answer_start > assignment_submit.compare_start) {
                    Toaster.warning('Assignment Not Duplicated', 'Please double-check the answer and comparison start and end times for mismatches and try again.');
                    $scope.submitted = false;
                    return;
                } else if (assignment.availableCheck && assignment_submit.compare_start >= assignment_submit.compare_end) {
                    Toaster.warning('Assignment Not Duplicated', 'Please set comparison end time after comparison start time and try again.');
                    $scope.submitted = false;
                    return;
                } else if (assignment.enable_self_evaluation && assignment.selfEvalCheck && assignment_submit.self_eval_start >= assignment_submit.self_eval_end) {
                    Toaster.warning('Assignment Not Duplicated', 'Please set self-evaluation end time after self-evaluation start time and try again.');
                    $scope.submitted = false;
                    return;
                }

                // if option is not checked; make sure no compare dates are saved.
                if (!assignment.availableCheck) {
                    assignment_submit.compare_start = null;
                    assignment_submit.compare_end = null;
                }
                // same for self-evaluation dates
                if (!assignment.selfEvalCheck) {
                    assignment_submit.self_eval_start = null;
                    assignment_submit.self_eval_end = null;
                }

                $scope.duplicateCourse.assignments.push(assignment_submit);
            }

            CourseResource.createDuplicate({id: $scope.originalCourse.id}, $scope.duplicateCourse, function (ret) {
                Toaster.success("Course Duplicated");
                // refresh permissions
                Session.expirePermissions();

                var course = ret;
                submitted = false;
                if ($scope.closeDuplicate) {
                    $scope.closeDuplicate(course.id);
                }
                else {
                    $location.path('/course/' + ret.id);
                }

            }).$promise.finally(function() {
                $scope.submitted = false;
            });
        };

        var originalCourseWatcher = function(newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) return;
            $scope.setupDuplicateCourse();
        };

        if (typeof($scope.originalCourse) == 'undefined') {
            CourseResource.get({'id': $routeParams.courseId}).$promise.then(
                function(ret) {
                    $scope.originalCourse = ret;
                    $scope.$watchCollection('originalCourse', originalCourseWatcher);
                    $scope.setupDuplicateCourse();
                }
            );
        }
        else {
            $scope.$watchCollection('originalCourse', originalCourseWatcher);
            $scope.setupDuplicateCourse();
        }
    }
]);

module.controller(
    'CourseController',
    ['$scope', '$route', '$routeParams', '$location', 'Session',
     'CourseResource', 'Toaster', 'EditorOptions',  "resolvedData",
    function($scope, $route, $routeParams, $location, Session,
             CourseResource, Toaster, EditorOptions, resolvedData)
    {
        $scope.courseId = $routeParams.courseId;
        $scope.course = resolvedData.course || {};
        $scope.loggedInUserId = resolvedData.loggedInUser.id;
        $scope.editorOptions = EditorOptions.basic;

        $scope.method = $scope.course.id ? "edit" : "create";
        // unlike for assignments, course dates initially blank
        $scope.format = 'dd-MMMM-yyyy';
        $scope.date = {
            'course_start': {'date': null, 'time': new Date().setHours(0, 0, 0, 0)},
            'course_end': {'date': null, 'time': new Date().setHours(23, 59, 0, 0)},
        };

        if ($scope.method == "create") {
            $scope.course.year = new Date().getFullYear();
        } else if ($scope.method == "edit") {
            // dates may be left blank
            $scope.date.course_start.date = $scope.course.start_date != null ? new Date($scope.course.start_date) : null;
            $scope.date.course_end.date = $scope.course.end_date != null ? new Date($scope.course.end_date) : null;
            $scope.date.course_start.time = new Date($scope.course.start_date);
            $scope.date.course_end.time = new Date($scope.course.end_date);
        }

        $scope.datePickerOpen = function($event, object) {
            $event.preventDefault();
            $event.stopPropagation();

            object.opened = true;
        };

        $scope.save = function() {
            $scope.submitted = true;

            if ($scope.date.course_start.date != null) {
                $scope.course.start_date = combineDateTime($scope.date.course_start);
            } else {
                $scope.course.start_date = null;
            }

            if ($scope.date.course_end.date != null) {
                $scope.course.end_date = combineDateTime($scope.date.course_end);
            } else {
                $scope.course.end_date = null;
            }

            if ($scope.course.start_date == null) {
                Toaster.warning('Course Not Saved', 'Please indicate the course start time and save again.');
                $scope.submitted = false;
                return;
            }
            else if ($scope.course.end_date != null && $scope.course.start_date > $scope.course.end_date) {
                Toaster.warning('Course Not Saved', 'Please set course end time after course start time and save again.');
                $scope.submitted = false;
                return;
            }

            CourseResource.save({id: $scope.course.id}, $scope.course, function (ret) {
                Toaster.success("Course Saved");

                // refresh permissions
                Session.expirePermissions();
                $location.path('/course/' + ret.id);
            }).$promise.finally(function() {
                $scope.submitted = false;
            });
        };
    }]
);

// End anonymous function
})();