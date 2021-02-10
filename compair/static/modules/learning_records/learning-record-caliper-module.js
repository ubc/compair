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
module.constant('CaliperEntityTypes', {
    'AGENT': 'Agent',
    'AGGREGATE_MEASURE': 'AggregateMeasure',
    'AGGREGATE_MEASURE_COLLECTION': 'AggregateMeasureCollection',
    'AGGREGATE_PROGRESS': 'AggregateProgress',
    'AGGREGATE_TIME_ON_TASK': 'AggregateTimeOnTask',
    'ANNOTATION': 'Annotation',
    'ASSESSMENT': 'Assessment',
    'ASSESSMENT_ITEM': 'AssessmentItem',
    'ASSIGNABLE_DIGITAL_RESOURCE': 'AssignableDigitalResource',
    'ATTEMPT': 'Attempt',
    'AUDIO_OBJECT': 'AudioObject',
    'BOOKMARK_ANNOTATION': 'BookmarkAnnotation',
    'CHAPTER': 'Chapter',
    'COLLECTION': 'Collection',
    'COMMENT': 'Comment',
    'COURSE_OFFERING': 'CourseOffering',
    'COURSE_SECTION': 'CourseSection',
    'DATE_TIME_QUESTION': 'DateTimeQuestion',
    'DATE_TIME_RESPONSE': 'DateTimeResponse',
    'DIGITAL_RESOURCE': 'DigitalResource',
    'DIGITAL_RESOURCE_COLLECTION': 'DigitalResourceCollection',
    'DOCUMENT': 'Document',
    'ENTITY': 'Entity',
    'EPUB_CHAPTER': 'EpubChapter',
    'EPUB_PART': 'EpubPart',
    'EPUB_SUB_CHAPTER': 'EpubSubChapter',
    'EPUB_VOLUME': 'EpubVolume',
    'FILL_IN_BLANK_RESPONSE': 'FillinBlankResponse',
    'FORUM': 'Forum',
    'FRAME': 'Frame',
    'GROUP': 'Group',
    'HIGHLIGHT_ANNOTATION': 'HighlightAnnotation',
    'IMAGE_OBJECT': 'ImageObject',
    'LEARNING_OBJECTIVE': 'LearningObjective',
    'LINK': 'Link',
    'LIKERT_SCALE': 'LikertScale',
    'LTI_LINK': 'LtiLink',
    'LTI_SESSION': 'LtiSession',
    'MEDIA_LOCATION': 'MediaLocation',
    'MEDIA_OBJECT': 'MediaObject',
    'MEMBERSHIP': 'Membership',
    'MESSAGE': 'Message',
    'MULTIPLE_CHOICE_RESPONSE': 'MultipleChoiceResponse',
    'MULTIPLE_RESPONSE_RESPONSE': 'MultipleResponseResponse',
    'MULTISELECT_QUESTION': 'MultiselectQuestion',
    'MULTISELECT_RESPONSE': 'MultiselectResponse',
    'MULTISELECT_SCALE': 'MultiselectScale',
    'NUMERIC_SCALE': 'NumericScale',
    'OPEN_ENDED_QUESTION': 'OpenEndedQuestion',
    'OPEN_ENDED_RESPONSE': 'OpenEndedResponse',
    'ORGANIZATION': 'Organization',
    'PAGE': 'Page',
    'PERSON': 'Person',
    'QUERY': 'Query',
    'QUESTION': 'Question',
    'QUESTIONNAIRE': 'Questionnaire',
    'QUESTIONNAIRE_ITEM': 'QuestionnaireItem',
    'RATING': 'Rating',
    'RATING_SCALE_QUESTION': 'RatingScaleQuestion',
    'RATING_SCALE_RESPONSE': 'RatingScaleResponse',
    'READING': 'Reading',
    'RESPONSE': 'Response',
    'RESULT': 'Result',
    'SCALE': 'Scale',
    'SCORE': 'Score',
    'SEARCH_RESPONSE': 'SearchResponse',
    'SELECT_TEXT_RESPONSE': 'SelectTextResponse',
    'SESSION': 'Session',
    'SHARED_ANNOTATION': 'SharedAnnotation',
    'SOFTWARE_APPLICATION': 'SoftwareApplication',
    'SURVEY': 'Survey',
    'SURVEY_INVITATION': 'SurveyInvitation',
    'SYSTEM_IDENTIFIER': 'SystemIdentifier',
    'TAG_ANNOTATION': 'TagAnnotation',
    'TEXT_POSITION_SELECTOR': 'TextPositionSelector',
    'THREAD': 'Thread',
    'TRUE_FALSE_RESPONSE': 'TrueFalseResponse',
    'VIDEO_OBJECT': 'VideoObject',
    'WEB_PAGE': 'WebPage'
});


module.constant('CaliperEventTypes', {
    'ANNOTATION_EVENT': 'AnnotationEvent',
    'ASSESSMENT_EVENT': 'AssessmentEvent',
    'ASSESSMENT_ITEM_EVENT': 'AssessmentItemEvent',
    'ASSIGNABLE_EVENT': 'AssignableEvent',
    'EVENT': 'Event',
    'FEEDBACK_EVENT': 'FeedbackEvent',
    'FORUM_EVENT': 'ForumEvent',
    'MEDIA_EVENT': 'MediaEvent',
    'MESSAGE_EVENT': 'MessageEvent',
    'NAVIGATION_EVENT': 'NavigationEvent',
    'GRADE_EVENT': 'GradeEvent',
    'QUESTIONNAIRE_EVENT': 'QuestionnaireEvent',
    'QUESTIONNAIRE_ITEM_EVENT': 'QuestionnaireItemEvent',
    'RESOURCE_MANAGEMENT_EVENT': 'ResourceManagementEvent',
    'SEARCH_EVENT': 'SearchEvent',
    'SESSION_EVENT': 'SessionEvent',
    'SURVEY_EVENT': 'SurveyEvent',
    'SURVEY_INVITATION_EVENT': 'SurveyInvitationEvent',
    'THREAD_EVENT': 'ThreadEvent',
    'TOOL_LAUNCH_EVENT': 'ToolLaunchEvent',
    'TOOL_USE_EVENT': 'ToolUseEvent',
    'VIEW_EVENT': 'ViewEvent',
});

module.constant('CaliperProfiles', {
    'ANNOTATION': 'AnnotationProfile',
    'ASSESSMENT': 'AssessmentProfile',
    'ASSIGNABLE': 'AssignableProfile',
    'FEEDBACK': 'FeedbackProfile',
    'FORUM': 'ForumProfile',
    'GENERAL': 'GeneralProfile',
    'GRADING': 'GradingProfile',
    'MEDIA': 'MediaProfile',
    'READING': 'ReadingProfile',
    'RESOURCE_MANAGEMENT': 'ResourceManagementProfile',
    'SEARCH': 'SearchProfile',
    'SESSION': 'SessionProfile',
    'SURVEY': 'SurveyProfile',
    'TOOL_LAUNCH': 'ToolLaunchProfile',
    'TOOL_USE': 'ToolUseProfile',
});

module.constant('CaliperEventActions', {
    'ABANDONED': 'Abandoned',
    'ACTIVATED': 'Activated',
    'ACCEPTED': 'Accepted',
    'ADDED': 'Added',
    'ARCHIVED': 'Archived',
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
    'COPIED': 'Copied',
    'CREATED': 'Created',
    'DEACTIVATED': 'Deactivated',
    'DECLINED': 'Declined',
    'DELETED': 'Deleted',
    'DESCRIBED': 'Described',
    'DISABLED_CLOSED_CAPTIONING': 'DisabledClosedCaptioning',
    'DISLIKED': 'Disliked',
    'DOWNLOADED': 'Downloaded',
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
    'LAUNCHED': 'Launched',
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
    'OPTED_IN': 'OptedIn',
    'OPTED_OUT': 'OptedOut',
    'PAUSED': 'Paused',
    'POSTED': 'Posted',
    'PRINTED': 'Printed',
    'PUBLISHED': 'Published',
    'QUESTIONED': 'Questioned',
    'RANKED': 'Ranked',
    'RECOMMENDED': 'Recommended',
    'REMOVED': 'Removed',
    'REPLIED': 'Replied',
    'RESET': 'Reset',
    'RESTARTED': 'Restarted',
    'RESTORED': 'Restored',
    'RESUMED': 'Resumed',
    'RETRIEVED': 'Retrieved',
    'REVIEWED': 'Reviewed',
    'RETURNED': 'Returned',
    'REWOUND': 'Rewound',
    'SAVED': 'Saved',
    'SEARCHED': 'Searched',
    'SENT': 'Sent',
    'SHARED': 'Shared',
    'SHOWED': 'Showed',
    'SKIPPED': 'Skipped',
    'STARTED': 'Started',
    'SUBMITTED': 'Submitted',
    'SUBSCRIBED': 'Subscribed',
    'TAGGED': 'Tagged',
    'TIMED_OUT': 'TimedOut',
    'UNMUTED': 'Unmuted',
    'UNPUBLISHED': 'Unpublished',
    'UNSUBSCRIBED': 'Unsubscribed',
    'UPLOADED': 'Uploaded',
    'USED': 'Used',
    'VIEWED': 'Viewed'
});

module.service('Caliper',
    [ "ResourceIRI", "Session", "LearningRecordSettings", "CaliperEntityTypes", "CaliperEventTypes",
      "CaliperEventActions", "CaliperProfiles",
    function(ResourceIRI, Session, LearningRecordSettings, CaliperEntityTypes, CaliperEventTypes,
             CaliperEventActions, CaliperProfiles) {
        var _this = this;

        this.events = CaliperEventTypes;
        this.actions = CaliperEventActions;
        this.profiles = CaliperProfiles;

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
                var eventJson = JSON.stringify(eventParams);
                navigator.sendBeacon('/api/learning_records/caliper/events', eventJson);
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
