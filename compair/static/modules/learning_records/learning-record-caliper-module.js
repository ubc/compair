// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.learning_records.caliper', [
    'ngResource',
    'angular-uuid',
    'ubc.ctlt.compair.session',
    'ubc.ctlt.compair.comparison',
    'ubc.ctlt.compair.learning_records.learning_record'
]);

/***** Providers *****/
module.factory('CaliperEventResource', ["$resource", function($resource)
{
    var ret = $resource('/api/learning_records/caliper/events', {},
        {
            'save': { method: 'POST', ignoreLoadingBar: true, bypassErrorsInterceptor: true }
        }
    );
    return ret;
}]);


module.constant('CaliperEntityTypes', {
    'AGENT': 'Agent',
    'ANNOTATION': 'Annotation',
    'ASSESSMENT': 'Assessment',
    'ASSESSMENT_ITEM': 'AssessmentItem',
    'ASSIGNABLE_DIGITAL_RESOURCE': 'AssignableDigitalResource',
    'ATTEMPT': 'Attempt',
    'AUDIO_OBJECT': 'AudioObject',
    'BOOKMARK_ANNOTATION': 'BookmarkAnnotation',
    'CHAPTER': 'Chapter',
    'COURSE_OFFERING': 'CourseOffering',
    'COURSE_SECTION': 'CourseSection',
    'DIGITAL_RESOURCE': 'DigitalResource',
    'DIGITAL_RESOURCE_COLLECTION': 'DigitalResourceCollection',
    'DOCUMENT': 'Document',
    'ENTITY': 'Entity',
    'EPUB_CHAPTER': 'EpubChapter',
    'EPUB_PART': 'EpubPart',
    'EPUB_SUB_CHAPTER': 'EpubSubChapter',
    'EPUB_VOLUME': 'EpubVolume',
    'FILLINBLANK': 'FillinBlankResponse',
    'FORUM': 'Forum',
    'FRAME': 'Frame',
    'GROUP': 'Group',
    'HIGHLIGHT_ANNOTATION': 'HighlightAnnotation',
    'IMAGE_OBJECT': 'ImageObject',
    'LEARNING_OBJECTIVE': 'LearningObjective',
    'LTI_SESSION': 'LtiSession',
    'MEDIA_LOCATION': 'MediaLocation',
    'MEDIA_OBJECT': 'MediaObject',
    'MEMBERSHIP': 'Membership',
    'MESSAGE': 'Message',
    'MULTIPLECHOICE': 'MultipleChoiceResponse',
    'MULTIPLERESPONSE': 'MultipleResponseResponse',
    'ORGANIZATION': 'Organization',
    'PAGE': 'Page',
    'PERSON': 'Person',
    'READING': 'Reading',
    'RESPONSE': 'Response',
    'RESULT': 'Result',
    'SCORE': 'Score',
    'SELECTTEXT': 'SelectTextResponse',
    'SESSION': 'Session',
    'SHARED_ANNOTATION': 'SharedAnnotation',
    'SOFTWARE_APPLICATION': 'SoftwareApplication',
    'TAG_ANNOTATION': 'TagAnnotation',
    'TEXT_POSITION_SELECTOR': 'TextPositionSelector',
    'THREAD': 'Thread',
    'TRUEFALSE': 'TrueFalseResponse',
    'VIDEO_OBJECT': 'VideoObject',
    'WEB_PAGE': 'WebPage'
});


module.constant('CaliperEventTypes', {
    'ANNOTATION_EVENT': 'AnnotationEvent',
    'ASSESSMENT_EVENT': 'AssessmentEvent',
    'ASSESSMENT_ITEM_EVENT': 'AssessmentItemEvent',
    'ASSIGNABLE_EVENT': 'AssignableEvent',
    'EVENT': 'Event',
    'FORUM_EVENT': 'ForumEvent',
    'MEDIA_EVENT': 'MediaEvent',
    'MESSAGE_EVENT': 'MessageEvent',
    'NAVIGATION_EVENT': 'NavigationEvent',
    'GRADE_EVENT': 'GradeEvent',
    'SESSION_EVENT': 'SessionEvent',
    'THREAD_EVENT': 'ThreadEvent',
    'TOOL_USE_EVENT': 'ToolUseEvent',
    'VIEW_EVENT': 'ViewEvent',
});

module.constant('CaliperEventActions', {
    basic: {
        'ABANDONED': 'Abandoned',
        'ACTIVATED': 'Activated',
        'ADDED': 'Added',
        'ATTACHED': 'Attached',
        'BOOKMARKED': 'Bookmarked',
        'CHANGED_RESOLUTION': 'ChangedResolution',
        'CHANGED_SIZE': 'ChangedSize',
        'CHANGED_SPEED': 'ChangedSpeed',
        'CHANGED_VOLUME': 'ChangedVolume',
        'CLASSIFIED': 'Classified',
        'CLOSED_POPOUT': 'ClosedPopout',
        'COMMENTED': 'Commented',
        'COMPLETED': 'Completed',
        'CREATED': 'Created',
        'DEACTIVATED': 'Deactivated',
        'DELETED': 'Deleted',
        'DESCRIBED': 'Described',
        'DISABLED_CLOSED_CAPTIONING': 'DisabledClosedCaptioning',
        'DISLIKED': 'Disliked',
        'EARNED': 'Earned',
        'ENABLED_CLOSED_CAPTIONING': 'EnabledClosedCaptioning',
        'ENDED': 'Ended',
        'ENTERED_FULLSCREEN': 'EnteredFullScreen',
        'EXITED_FULLSCREEN': 'ExitedFullScreen',
        'FORWARDED_TO': 'ForwardedTo',
        'GRADED': 'Graded',
        'HID': 'Hid',
        'HIGHLIGHTED': 'Highlighted',
        'IDENTIFIED': 'Identified',
        'JUMPED_TO': 'JumpedTo',
        'LIKED': 'Liked',
        'LINKED': 'Linked',
        'LOGGED_IN': 'LoggedIn',
        'LOGGED_OUT': 'LoggedOut',
        'MARKED_AS_READ': 'MarkedAsRead',
        'MARKED_AS_UNREAD': 'MarkedAsUnread',
        'MODIFIED': 'Modified',
        'MUTED': 'Muted',
        'NAVIGATED_TO': 'NavigatedTo',
        'OPENED_POPOUT': 'OpenedPopout',
        'PAUSED': 'Paused',
        'POSTED': 'Posted',
        'QUESTIONED': 'Questioned',
        'RANKED': 'Ranked',
        'RECOMMENDED': 'Recommended',
        'REMOVED': 'Removed',
        'REPLIED': 'Replied',
        'RESET': 'Reset',
        'RESTARTED': 'Restarted',
        'RESUMED': 'Resumed',
        'RETRIEVED': 'Retrieved',
        'REVIEWED': 'Reviewed',
        'REWOUND': 'Rewound',
        'SEARCHED': 'Searched',
        'SHARED': 'Shared',
        'SHOWED': 'Showed',
        'SKIPPED': 'Skipped',
        'STARTED': 'Started',
        'SUBMITTED': 'Submitted',
        'SUBSCRIBED': 'Subscribed',
        'TAGGED': 'Tagged',
        'TIMED_OUT': 'TimedOut',
        'UNMUTED': 'Unmuted',
        'UNSUBSCRIBED': 'Unsubscribed',
        'USED': 'Used',
        'VIEWED': 'Viewed'
    },
    annotation: {
        'BOOKMARKED': 'Bookmarked',
        'HIGHLIGHTED': 'Highlighted',
        'SHARED': 'Shared',
        'TAGGED': 'Tagged',
    },
    assessment: {
        'PAUSED': 'Paused',
        'RESTARTED': 'Restarted',
        'RESUMED': 'Resumed',
        'STARTED': 'Started',
        'SUBMITTED': 'Submitted',
    },
    assessment_item: {
        'COMPLETED': 'Completed',
        'SKIPPED': 'Skipped',
        'STARTED': 'Started',
    },
    assignable: {
        'ACTIVATED': 'Activated',
        'COMPLETED': 'Completed',
        'DEACTIVATED': 'Deactivated',
        'STARTED': 'Started',
        'SUBMITTED': 'Submitted',
    },
    forum: {
        'SUBSCRIBED': 'Subscribed',
        'UNSUBSCRIBED': 'Unsubscribed',
    },
    grade: {
        'GRADED': 'Graded',
    },
    media: {
        'CHANGED_RESOLUTION': 'ChangedResolution',
        'CHANGED_SIZE': 'ChangedSize',
        'CHANGED_SPEED': 'ChangedSpeed',
        'CHANGED_VOLUME': 'ChangedVolume',
        'CLOSED_POPOUT': 'ClosedPopout',
        'DISABLED_CLOSED_CAPTIONING': 'DisabledClosedCaptioning',
        'ENABLED_CLOSED_CAPTIONING': 'EnabledClosedCaptioning',
        'ENDED': 'Ended',
        'ENTERED_FULLSCREEN': 'EnteredFullScreen',
        'EXITED_FULLSCREEN': 'ExitedFullScreen',
        'FORWARDED_TO': 'ForwardedTo',
        'JUMPED_TO': 'JumpedTo',
        'MUTED': 'Muted',
        'OPENED_POPOUT': 'OpenedPopout',
        'PAUSED': 'Paused',
        'RESUMED': 'Resumed',
        'RESTARTED': 'Restarted',
        'REWOUND': 'Rewound',
        'STARTED': 'Started',
        'UNMUTED': 'Unmuted',
    },
    message: {
        'MARKED_AS_READ': 'MarkedAsRead',
        'MARKED_AS_UNREAD': 'MarkedAsUnread',
        'POSTED': 'Posted',
    },
    navigation: {
        'NAVIGATED_TO': 'NavigatedTo',
    },
    session: {
        'LOGGED_IN': 'LoggedIn',
        'LOGGED_OUT': 'LoggedOut',
        'TIMED_OUT': 'TimedOut',
    },
    thread: {
        'MARKED_AS_READ': 'MarkedAsRead',
        'MARKED_AS_UNREAD': 'MarkedAsUnread',
    },
    tool_use: {
        'USED': 'Used',
    },
    view: {
        'VIEWED': 'Viewed'
    },
});

module.service('Caliper',
    [ "CaliperEventResource", "LearningRecord", "ResourceIRI", "Session", "WinningAnswer",
      "LearningRecordSettings", "CaliperEntityTypes", "CaliperEventTypes", "CaliperEventActions",
    function(CaliperEventResource, LearningRecord, ResourceIRI, Session, WinningAnswer,
             LearningRecordSettings, CaliperEntityTypes, CaliperEventTypes, CaliperEventActions) {
        var _this = this;

        this.events = CaliperEventTypes;
        this.actions = CaliperEventActions;

        this.generateEvent = function(course_id, params) {
            var eventParams = angular.copy(params);

            if (!eventParams.eventTime) {
                eventParams.eventTime = (new Date()).toISOString();
            }
            _this.emitEvent(course_id, eventParams);
        }

        this.emitEvent = function(course_id, eventParams) {
            if (LearningRecordSettings.caliper_enabled && Session.isLoggedIn()) {
                if (course_id) {
                    eventParams['course_id'] = course_id;
                }
                CaliperEventResource.save(eventParams);
            }
        };

        this.entities = {
            assignment: function(assignment) {
                return {
                    "id": ResourceIRI.assignment(assignment.course_id, assignment.id),
                    "type": CaliperEntityTypes["ASSESSMENT"],
                };
            },
            assignment_attempt: function(assignment, tracking, full_tracking) {
                entity = {
                    "id": ResourceIRI.assignment_attempt(assignment.course_id, assignment.id, tracking.getUUID()),
                    "type": CaliperEntityTypes["ATTEMPT"],
                    "assignable": ResourceIRI.assignment(assignment.course_id, assignment.id),
                    "startedAtTime": tracking.getStarted()
                };

                if (full_tracking) {
                    entity.duration = tracking.getDuration();
                    entity.endedAtTime = tracking.getEnded();
                }

                return entity;
            },


            assignment_question: function(assignment) {
                return {
                    "id": ResourceIRI.assignment_question(assignment.course_id, assignment.id),
                    "type": CaliperEntityTypes["ASSESSMENT_ITEM"],
                };
            },
            answer_attempt: function(assignment, tracking, full_tracking) {
                entity = {
                    "id": ResourceIRI.answer_attempt(assignment.course_id, assignment.id, tracking.getUUID()),
                    "type": CaliperEntityTypes["ATTEMPT"],
                    "assignable": ResourceIRI.assignment_question(assignment.course_id, assignment.id),
                    "startedAtTime": tracking.getStarted()
                }

                if (full_tracking) {
                    entity.duration = tracking.getDuration();
                    entity.endedAtTime = tracking.getEnded();
                }

                return entity;
            },


            comparison_question: function(assignment, comparison_number) {
                return {
                    "id": ResourceIRI.comparison_question(assignment.course_id, assignment.id, comparison_number),
                    "type": CaliperEntityTypes["ASSESSMENT_ITEM"],
                };
            },
            comparison_attempt: function(assignment, comparison_number, tracking, full_tracking) {
                entity = {
                    "id": ResourceIRI.comparison_attempt(assignment.course_id, assignment.id, comparison_number, tracking.getUUID()),
                    "type": CaliperEntityTypes["ATTEMPT"],
                    "assignable": ResourceIRI.comparison_question(assignment.course_id, assignment.id, comparison_number),
                    "startedAtTime": tracking.getStarted()
                }

                if (full_tracking) {
                    entity.duration = tracking.getDuration();
                    entity.endedAtTime = tracking.getEnded();
                }

                return entity;
            },


            evaluation_question: function(assignment, evaluation_number) {
                return {
                    "id": ResourceIRI.evaluation_question(assignment.course_id, assignment.id, evaluation_number),
                    "type": CaliperEntityTypes["ASSESSMENT_ITEM"],
                };
            },
            evaluation_attempt: function(assignment, evaluation_number, tracking, full_tracking) {
                entity = {
                    "id": ResourceIRI.evaluation_attempt(assignment.course_id, assignment.id, evaluation_number, tracking.getUUID()),
                    "type": CaliperEntityTypes["ATTEMPT"],
                    "assignable": ResourceIRI.evaluation_question(assignment.course_id, assignment.id, evaluation_number),
                    "startedAtTime": tracking.getStarted()
                }

                if (full_tracking) {
                    entity.duration = tracking.getDuration();
                    entity.endedAtTime = tracking.getEnded();
                }

                return entity;
            },


            self_evaluation_question: function(assignment) {
                return {
                    "id": ResourceIRI.self_evaluation_question(assignment.course_id, assignment.id),
                    "type": CaliperEntityTypes["ASSESSMENT_ITEM"],
                };
            },
            self_evaluation_attempt: function(assignment, tracking, full_tracking) {
                entity = {
                    "id": ResourceIRI.self_evaluation_attempt(assignment.course_id, assignment.id, tracking.getUUID()),
                    "type": CaliperEntityTypes["ATTEMPT"],
                    "assignable": ResourceIRI.self_evaluation_question(assignment.course_id, assignment.id),
                    "startedAtTime": tracking.getStarted()
                }

                if (full_tracking) {
                    entity.duration = tracking.getDuration();
                    entity.endedAtTime = tracking.getEnded();
                }

                return entity;
            },


            page: function(relativePath) {
                return {
                    "id": ResourceIRI.page(relativePath),
                    "type": CaliperEntityTypes["WEB_PAGE"],
                };
            },


            page_section: function(relativePath, sectionName) {
                return {
                    "id": ResourceIRI.page_section(relativePath, sectionName),
                    "type": CaliperEntityTypes["FRAME"],
                    "name": sectionName,
                };
            },

            modal: function(relativePath, modalName) {
                return {
                    "id": ResourceIRI.modal(relativePath, modalName),
                    "type": CaliperEntityTypes["FRAME"],
                    "name": modalName,
                };
            },

        }
    }]
);


// End anonymous function
})();
