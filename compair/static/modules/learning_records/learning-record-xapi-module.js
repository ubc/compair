// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.learning_records.xapi', [
    'ngResource',
    'angularMoment',
    'angular-uuid',
    'ubc.ctlt.compair.session',
    'ubc.ctlt.compair.comparison',
    'ubc.ctlt.compair.learning_records.learning_record'
]);


/***** Providers *****/
module.constant('xAPIVerb', {
    'viewed': {
        id: 'http://id.tincanapi.com/verb/viewed',
        display: { 'en-US': 'viewed' }
    },
    'commented': {
        id: 'http://adlnet.gov/expapi/verbs/commented',
        display: { 'en-US': 'commented' }
    },
    'authored': {
        id: 'http://activitystrea.ms/schema/1.0/author',
        display: { 'en-US': 'authored' }
    },
    'removed': {
        id: 'https://w3id.org/xapi/dod-isd/verbs/removed',
        display: { 'en-US': 'removed' }
    },
    'archived': {
        id: 'https://w3id.org/xapi/dod-isd/verbs/archived',
        display: { 'en-US': 'archived' }
    },
    'updated': {
        id: 'http://activitystrea.ms/schema/1.0/update',
        display: { 'en-US': 'updated' }
    },

    'initialized': {
        id: 'http://adlnet.gov/expapi/verbs/initialized',
        display: { 'en-US': 'initialized' }
    },
    'resumed': {
        id: 'http://adlnet.gov/expapi/verbs/resumed',
        display: { 'en-US': 'resumed' }
    },
    'interacted': {
        id: 'http://adlnet.gov/expapi/verbs/interacted',
        display: { 'en-US': 'interacted' }
    },
    'completed': {
        id: 'http://adlnet.gov/expapi/verbs/completed',
        display: { 'en-US': 'completed' }
    },
    'suspended': {
        id: 'http://adlnet.gov/expapi/verbs/suspended',
        display: { 'en-US': 'suspended' }
    },
    'exited': {
        id: 'http://adlnet.gov/expapi/verbs/exited',
        display: { 'en-US': 'exited' }
    },

    'attached': {
        id: 'http://activitystrea.ms/schema/1.0/attach',
        display: { 'en-US': 'attached' }
    },
    'submitted': {
        id: 'http://activitystrea.ms/schema/1.0/submit',
        display: { 'en-US': 'submitted' }
    },
    'evaluated': {
        id: 'http://www.tincanapi.co.uk/verbs/evaluated',
        display: { 'en-US': 'evaluated' }
    },
    'downloaded': {
        id: 'http://id.tincanapi.com/verb/downloaded',
        display: { 'en-US': 'downloaded' }
    },

    'logged in': {
        id: 'https://brindlewaye.com/xAPITerms/verbs/loggedin/',
        display: { 'en-US': 'logged in' }
    },
    'logged out': {
        id: 'https://brindlewaye.com/xAPITerms/verbs/loggedout/',
        display: { 'en-US': 'logged out' }
    },
    'opened': {
        id: 'http://activitystrea.ms/schema/1.0/open',
        display: { 'en-US': 'opened' }
    },
    'closed': {
        id: 'http://activitystrea.ms/schema/1.0/close',
        display: { 'en-US': 'closed' }
    },
    'drafted': {
        id: 'http://xapi.learninganalytics.ubc.ca/verb/draft',
        display: { 'en-US': 'drafted' }
    },
    'filtered': {
        id: 'http://xapi.learninganalytics.ubc.ca/verb/filter',
        display: { 'en-US': 'filtered' }
    },
    'sorted': {
        id: 'http://xapi.learninganalytics.ubc.ca/verb/sort',
        display: { 'en-US': 'sorted' }
    }
});

module.constant('xAPIActivityType', {
    'page': 'http://activitystrea.ms/schema/1.0/page',
    'comment': 'http://activitystrea.ms/schema/1.0/comment',

    'attempt': 'http://adlnet.gov/expapi/activities/attempt',
    'course': 'http://adlnet.gov/expapi/activities/course',
    'assessment': 'http://adlnet.gov/expapi/activities/assessment',
    'question': 'http://adlnet.gov/expapi/activities/question',
    'solution': 'http://id.tincanapi.com/activitytype/solution',
    'file': 'http://activitystrea.ms/schema/1.0/file',
    'review': 'http://activitystrea.ms/schema/1.0/review',
    'section': 'http://id.tincanapi.com/activitytype/section',
    'modal': 'http://xapi.learninganalytics.ubc.ca/activitytype/modal',
    'user profile': 'http://id.tincanapi.com/activitytype/user-profile',
    'service': 'http://activitystrea.ms/schema/1.0/service'
});

module.service('xAPI',
    [ "LearningRecord", "ResourceIRI", "Session", "LearningRecordSettings", "xAPIVerb", "xAPIActivityType",
    function(LearningRecord, ResourceIRI, Session, LearningRecordSettings, xAPIVerb, xAPIActivityType) {
        var _this = this;

        this.verb = xAPIVerb;
        this.activityType = xAPIActivityType;

        this.generateStatement = function(course_id, params) {
            var statementParams = angular.copy(params);

            if (!statementParams.timestamp) {
                statementParams.timestamp = (new Date()).toISOString();
            }
            var statement = new TinCan.Statement(statementParams);
            _this.save_statement(course_id, statement);
        }

        this.save_statement = function(course_id, statement) {
            if (LearningRecordSettings.xapi_enabled && Session.isLoggedIn()) {
                statementParams = statement.asVersion('1.0.3');
                if (course_id) {
                    statementParams['course_id'] = course_id;
                }
                var statementJson = JSON.stringify(statementParams);
                navigator.sendBeacon('/api/learning_records/xapi/statements', statementJson);
            }
        };

        this.object = {
            assignment: function(assignment) {
                var object = {
                    id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                    definition: {
                        type: _this.activityType.assessment,
                        name: { 'en-US': assignment.name }
                    }
                };

                if (assignment.description) {
                    object.definition.description = { 'en-US': assignment.description }
                }

                return object;
            },
            assignment_attempt: function(assignment, tracking, full_tracking) {
                var object = {
                    id: ResourceIRI.assignment_attempt(assignment.course_id, assignment.id, tracking.getUUID()),
                    definition: {
                        type: _this.activityType.attempt,
                        extensions: {}
                    }
                };

                object.definition.extensions["http://id.tincanapi.com/extension/attempt"] = {
                    startedAtTime: tracking.getStarted()
                };

                if (full_tracking) {
                    angular.merge(object.definition.extensions["http://id.tincanapi.com/extension/attempt"], {
                        duration: tracking.getDuration(),
                        endedAtTime: tracking.getEnded()
                    });
                }

                return object;
            },

            assignment_question: function(assignment) {
                var object = {
                    id: ResourceIRI.assignment_question(assignment.course_id, assignment.id),
                    definition: {
                        type: _this.activityType.question,
                        name: { 'en-US': assignment.name }
                    }
                }

                if (assignment.description) {
                    object.definition.description = { 'en-US': assignment.description }
                }

                return object;
            },
            answer_attempt: function(assignment, tracking, full_tracking) {
                var object = {
                    id: ResourceIRI.answer_attempt(assignment.course_id, assignment.id, tracking.getUUID()),
                    definition: {
                        type: _this.activityType.attempt,
                        extensions: {}
                    }
                }
                object.definition.extensions["http://id.tincanapi.com/extension/attempt"] = {
                    startedAtTime: tracking.getStarted()
                };
                if (full_tracking) {
                    angular.merge(object.definition.extensions["http://id.tincanapi.com/extension/attempt"], {
                        duration: tracking.getDuration(),
                        endedAtTime: tracking.getEnded()
                    });
                }

                return object;
            },

            comparison_question: function(assignment, comparison_number) {
                return {
                    id: ResourceIRI.comparison_question(assignment.course_id, assignment.id, comparison_number),
                    definition: {
                        type: _this.activityType.question,
                        name: { 'en-US': "Assignment comparison #"+comparison_number }
                    }
                }
            },
            comparison_attempt: function(assignment, comparison_number, tracking, full_tracking) {
                var object = {
                    id: ResourceIRI.comparison_attempt(assignment.course_id, assignment.id, comparison_number, tracking.getUUID()),
                    definition: {
                        type: _this.activityType.attempt,
                        extensions: {}
                    }
                }
                object.definition.extensions["http://id.tincanapi.com/extension/attempt"] = {
                    startedAtTime: tracking.getStarted()
                };
                if (full_tracking) {
                    angular.merge(object.definition.extensions["http://id.tincanapi.com/extension/attempt"], {
                        duration: tracking.getDuration(),
                        endedAtTime: tracking.getEnded()
                    });
                }

                return object;
            },

            evaluation_question: function(assignment, evaluation_number) {
                var object = {
                    id: ResourceIRI.evaluation_question(assignment.course_id, assignment.id, evaluation_number),
                    definition: {
                        type: _this.activityType.question,
                        name: { 'en-US': "Assignment Answer Evaluation #"+evaluation_number }
                    }
                }

                if (assignment.peer_feedback_prompt) {
                    object.definition.description = { 'en-US': assignment.peer_feedback_prompt }
                }

                return object;
            },
            evaluation_attempt: function(assignment, evaluation_number, tracking, full_tracking) {
                var object = {
                    id: ResourceIRI.evaluation_attempt(assignment.course_id, assignment.id, evaluation_number, tracking.getUUID()),
                    definition: {
                        type: _this.activityType.attempt,
                        extensions: {}
                    }
                }
                object.definition.extensions["http://id.tincanapi.com/extension/attempt"] = {
                    startedAtTime: tracking.getStarted()
                };
                if (full_tracking) {
                    angular.merge(object.definition.extensions["http://id.tincanapi.com/extension/attempt"], {
                        duration: tracking.getDuration(),
                        endedAtTime: tracking.getEnded()
                    });
                }

                return object;
            },

            self_evaluation_question: function(assignment) {
                return {
                    id: ResourceIRI.self_evaluation_question(assignment.course_id, assignment.id),
                    definition: {
                        type: _this.activityType.question,
                        name: { 'en-US': "Assignment self-evaluation" }
                    }
                }
            },
            self_evaluation_attempt: function(assignment, tracking, full_tracking) {
                var object = {
                    id: ResourceIRI.self_evaluation_attempt(assignment.course_id, assignment.id, tracking.getUUID()),
                    definition: {
                        type: _this.activityType.attempt,
                        extensions: {}
                    }
                }
                object.definition.extensions["http://id.tincanapi.com/extension/attempt"] = {
                    startedAtTime: tracking.getStarted()
                };
                if (full_tracking) {
                    angular.merge(object.definition.extensions["http://id.tincanapi.com/extension/attempt"], {
                        duration: tracking.getDuration(),
                        endedAtTime: tracking.getEnded()
                    });
                }

                return object;
            },

            page: function(relativePath) {
                return {
                    id: ResourceIRI.page(relativePath),
                    definition: {
                        type: _this.activityType.page
                    }
                }
            },

            page_section: function(relativePath, sectionName) {
                return {
                    id: ResourceIRI.page_section(relativePath, sectionName),
                    definition: {
                        type: _this.activityType.section,
                        name: { 'en-US': sectionName }
                    }
                }
            },

            modal: function(relativePath, modalName) {
                return {
                    id: ResourceIRI.modal(relativePath, modalName),
                    definition: {
                        type: _this.activityType.modal,
                        name: { 'en-US': modalName }
                    }
                }
            }
        };

        this.context = {
            basic: function(options) {
                options = options || {};

                var context = {};

                if (options.registration) {
                    context.registration = options.registration;
                }

                if (options.filters) {
                    if (!context.extensions) { context.extensions = {}; }
                    context.extensions['http://xapi.learninganalytics.ubc.ca/extension/filters'] = options.filters;
                }

                if (options.sortOrder) {
                    if (!context.extensions) { context.extensions = {}; }
                    context.extensions['http://xapi.learninganalytics.ubc.ca/extension/sort-order'] = options.sortOrder;
                }

                return context;
            },

            assignment: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is course
                        parent: [{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },
            assignment_attempt: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }],
                    }
                }, _this.context.basic(options));

                return context;
            },

            assignment_question: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },
            answer_attempt: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.assignment_question(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        },{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }],
                    }
                }, _this.context.basic(options));

                return context;
            },

            comparison_question: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },
            comparison_attempt: function(assignment, comparison_number, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.comparison_question(assignment.course_id, assignment.id, comparison_number),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        },{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }],
                    }
                }, _this.context.basic(options));

                return context;
            },

            evaluation_question: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },
            evaluation_attempt: function(assignment, evaluation_number, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.evaluation_question(assignment.course_id, assignment.id, evaluation_number),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        },{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }],
                    }
                }, _this.context.basic(options));

                return context;
            },

            self_evaluation_question: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },
            self_evaluation_attempt: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        parent: [{
                            id: ResourceIRI.self_evaluation_question(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        }],
                        grouping: [{
                            id: ResourceIRI.assignment(assignment.course_id, assignment.id),
                            objectType: "Activity"
                        },{
                            id: ResourceIRI.course(assignment.course_id),
                            objectType: "Activity"
                        }],
                    }
                }, _this.context.basic(options));

                return context;
            },

            page: function(locationUrl, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // other page's url unrelated to baseUrl
                        other: [{
                            id: LearningRecord.urlSafeEncode(locationUrl),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            page_section: function(relativePath, locationUrl, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent page's url related to baseUrl
                        parent: [{
                            id: ResourceIRI.page(relativePath),
                            objectType: "Activity"
                        }],
                        // other page's url unrelated to baseUrl
                        other: [{
                            id: LearningRecord.urlSafeEncode(locationUrl),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            modal: function(relativePath, locationUrl, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent page's url related to baseUrl
                        parent: [{
                            id: ResourceIRI.page(relativePath),
                            objectType: "Activity"
                        }],
                        // other page's url unrelated to baseUrl
                        other: [{
                            id: LearningRecord.urlSafeEncode(locationUrl),
                            objectType: "Activity"
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            answer_page_section: function(answer, relativePath, locationUrl, options) {
                var context = _this.context.page_section(relativePath, locationUrl, options);
                context.contextActivities.other.push({
                    id: ResourceIRI.answer(answer.course_id, answer.assignment_id, answer.id),
                    objectType: "Activity"
                });
                return context;
            },

            attachment_inline: function(attachment_name, relativePath, locationUrl, options) {
                var context = _this.context.page_section(relativePath, locationUrl, options);
                context.contextActivities.other.push({
                    id: ResourceIRI.attachment(attachment_name),
                    objectType: "Activity"
                });
                return context;
            },

            attachment_modal: function(attachment_name, relativePath, locationUrl, options) {
                var context = _this.context.modal(relativePath, locationUrl, options);
                context.contextActivities.other.push({
                    id: ResourceIRI.attachment(attachment_name),
                    objectType: "Activity"
                });
                return context;
            },

            embeddable_content_modal: function(contentUrl, relativePath, locationUrl, options) {
                var context = _this.context.modal(relativePath, locationUrl, options);

                // ensure is valid url
                if (!/^https?:\/\//i.test(contentUrl)) {
                    contentUrl = 'http://' + contentUrl;
                }
                context.contextActivities.other.push({
                    id: contentUrl,
                    objectType: "Activity"
                });
                return context;
            },
        };

        this.result = {
            basic: function(options) {
                options = options || {};

                var result = {};

                if (options.success != undefined) {
                    result.success = options.success;
                }

                if (options.completion != undefined) {
                    result.completion = options.completion;
                }

                return result;
            },

            basic_attempt: function(tracking, full_tracking, options) {
                options = options || {};
                var result = _this.result.basic(options);

                if (full_tracking) {
                    result.duration = tracking.getDuration();
                }

                return result;
            }
        }
    }]
);

// End anonymous function
})();
