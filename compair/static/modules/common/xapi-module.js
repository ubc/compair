// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.common.xapi', [
    'ngResource',
    'angularMoment',
    'angular-uuid',
    'ubc.ctlt.compair.session',
    'ubc.ctlt.compair.comparison'
]);

/***** Providers *****/
module.factory('StatementResource',
    ["$resource",
    function($resource)
{
    var ret = $resource('/api/statements', {},
        {
            'save': { method: 'POST', ignoreLoadingBar: true }
        }
    );
    return ret;
}]);

module.constant('xAPISettings', {
    enabled: false,
    baseUrl: '',
});

module.constant('xAPIVerb', {
    'earned': {
        id: 'http://specification.openbadges.org/xapi/verbs/earned',
        display: { 'en-US': 'earned' }
    },
    'viewed': {
        id: 'http://id.tincanapi.com/verb/viewed',
        display: { 'en-US': 'viewed' }
    },
    'commented': {
        id: 'http://adlnet.gov/expapi/verbs/commented',
        display: { 'en-US': 'commented' }
    },
    'up voted': {
        id: 'http://id.tincanapi.com/verb/voted-up',
        display: { 'en-US': 'up voted' }
    },
    'down voted': {
        id: 'http://id.tincanapi.com/verb/voted-down',
        display: { 'en-US': 'down voted' }
    },
    'vote canceled': {
        id: 'http://id.tincanapi.com/verb/voted-cancel',
        display: { 'en-US': 'vote canceled' }
    },
    'favorited': {
        id: 'http://activitystrea.ms/schema/1.0/favorite',
        display: { 'en-US': 'favorited' }
    },
    'unfavorited': {
        id: 'http://activitystrea.ms/schema/1.0/unfavorite',
        display: { 'en-US': 'unfavorited' }
    },
    'authored': {
        id: 'http://activitystrea.ms/schema/1.0/author',
        display: { 'en-US': 'authored' }
    },
    'deleted': {
        id: 'http://activitystrea.ms/schema/1.0/delete',
        display: { 'en-US': 'deleted' }
    },
    'updated': {
        id: 'http://activitystrea.ms/schema/1.0/update',
        display: { 'en-US': 'updated' }
    },
    'retracted': {
        id: 'http://activitystrea.ms/schema/1.0/retract',
        display: { 'en-US': 'retracted' }
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
    'flagged': {
        id: 'http://xapi.learninganalytics.ubc.ca/verb/flag',
        display: { 'en-US': 'flagged' }
    },
    'unflagged': {
        id: 'http://xapi.learninganalytics.ubc.ca/verb/unflag',
        display: { 'en-US': 'unflagged' }
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
    'badge': 'http://activitystrea.ms/schema/1.0/badge',
    'page': 'http://activitystrea.ms/schema/1.0/page',
    'comment': 'http://activitystrea.ms/schema/1.0/comment',

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

module.constant('xAPIExtensions', {
    // context
    'browser information': 'http://id.tincanapi.com/extension/browser-info',
    'referer': 'http://nextsoftwaresolutions.com/xapi/extensions/referer',
    'filters': 'http://xapi.learninganalytics.ubc.ca/extension/filters',
    'sort order': 'http://xapi.learninganalytics.ubc.ca/extension/sort-order',
    'login method': 'http://xapi.learninganalytics.ubc.ca/extension/login-method',

    // object
    'badgeclass': 'http://standard.openbadges.org/xapi/extensions/badgeclass',
    'comparison': 'http://xapi.learninganalytics.ubc.ca/extension/comparison',
    'pair algorithm': 'http://xapi.learninganalytics.ubc.ca/extension/score-algorithm',

    // result
    'fields changed': 'http://xapi.learninganalytics.ubc.ca/extension/fields-changed',
    'character count': 'http://xapi.learninganalytics.ubc.ca/extension/character-count',
    'word count': 'http://xapi.learninganalytics.ubc.ca/extension/word-count',
    'attachment response': 'http://xapi.learninganalytics.ubc.ca/extension/attachment-response',
    'score details': 'http://xapi.learninganalytics.ubc.ca/extension/score-details'
});

module.service('xAPI',
    [ "uuid", "StatementResource", "Session", "moment", "WinningAnswer",
      "xAPISettings", "xAPIVerb", "xAPIActivityType", "xAPIExtensions",
    function(uuid, StatementResource, Session, moment, WinningAnswer,
             xAPISettings, xAPIVerb, xAPIActivityType, xAPIExtensions) {
        var _this = this;

        this.verb = xAPIVerb;
        this.activityType = xAPIActivityType;
        this.extension = xAPIExtensions;

        this.generateStatement = function(params) {
            var statementParams = angular.copy(params);

            if (!statementParams.timestamp) {
                statementParams.timestamp = (new Date()).toISOString();
            }
            var statement = new TinCan.Statement(statementParams);
            _this.save_statement(statement);
        }

        this.save_statement = function(statement) {
            if (xAPISettings.enabled && Session.isLoggedIn()) {
                statement_json = statement.asVersion('1.0.1');
                StatementResource.save(statement_json);
            }
        };

        this.generateTracking = function() {
            var registration = uuid.v4();
            var startDuration = moment();
            return {
                getRegistration: function() {
                    return registration;
                },
                getDuration: function() {
                    var duration = moment.duration(moment().diff(startDuration));
                    return duration.toISOString();
                },
                toParams: function(params) {
                    params = params || {};

                    return angular.merge({
                        registration: this.getRegistration(),
                        duration: this.getDuration()
                    }, params);
                }
            }
        };

        this.ckeditorContentTracking = function(editorOptions, blurCallback) {
            var startDuration = null;
            return angular.merge({}, editorOptions, {
                on: {
                    focus: function() {
                        startDuration = moment();
                    },
                    blur: function() {
                        var duration = moment.duration(moment().diff(startDuration));
                        blurCallback(duration.toISOString());
                    }
                }
            });
        };

        this._resourceIRI = {
            _appPageUrl: function() {
                return xAPISettings.baseUrl + "app/#";
            },
            _appUrl: function() {
                return xAPISettings.baseUrl + "app/xapi/";
            },
            _attachmentUrl: function() {
                return xAPISettings.baseUrl + "app/attachment/";
            },
            criterion: function(criterion_id) {
                return _this._resourceIRI._appUrl() + "criterion/"+criterion_id;
            },
            course: function(course_id) {
                return _this._resourceIRI._appUrl() + "course/"+course_id;
            },
            assignment: function(assignment_id) {
                return _this._resourceIRI._appUrl() + "assignment/"+assignment_id;
            },
            assignment_question: function(assignment_id) {
                return _this._resourceIRI._appUrl() + "assignment/"+assignment_id+"/question";
            },
            comparison_question: function(comparison_id) {
                return _this._resourceIRI._appUrl() + "comparison/"+comparison_id+"/question";
            },
            self_evaluation_question: function(assignment_id) {
                return _this._resourceIRI._appUrl() + "assignment/"+assignment_id+"/self-evaluation";
            },
            answer: function(answer_id) {
                return _this._resourceIRI._appUrl() + "answer/"+answer_id;
            },
            answer_comment: function(comment_id) {
                return _this._resourceIRI._appUrl() + "answer/comment/"+comment_id;
            },
            comparison: function(comparison_id) {
                return _this._resourceIRI._appUrl() + "comparison/"+comparison_id;
            },
            comparison_criterion: function(comparison_criterion_id) {
                return _this._resourceIRI._appUrl() + "comparison/criterion/"+comparison_criterion_id;
            },
            attachment: function(fileName) {
                return _this._resourceIRI._attachmentUrl() + fileName;
            },
            page: function(relativePath) {
                return _this._resourceIRI._appPageUrl() + relativePath;
            },
            page_section: function(relativePath, sectionName) {
                return _this._resourceIRI.page(relativePath) + "?section="+encodeURIComponent(sectionName);
            },
            modal: function(relativePath, modalName) {
                return _this._resourceIRI.page(relativePath) + "?modal="+encodeURIComponent(modalName);
            }
        };

        this._stripHTML = function(text) {
            text = String(text) || '';
            text = text.replace(/<[^>]+>/g, '');
            text = text.replace('&nbsp;', ' ');
		    return _.unescape(text);
        };

        this._characterCount = function(text) {
            text = String(text) || '';
            text = _this._stripHTML(text);
            // replace linebreaks with whitespace to help get a more accurate count
            text = text.replace(/(\r\n|\n|\r)/g, ' ');
            return text.length;
        };

        this._wordCount = function(text) {
            text = String(text) || '';
            text = _this._stripHTML(text);
            // replace linebreaks with whitespace to help get a more accurate count
            text = text.replace(/(\r\n|\n|\r)/g, ' ');
            words = _.filter(text.split(/\s+/), function(word) {
                return word.length > 0;
            });
            return words.length;
        };

        this.object = {
            assignment: function(assignment) {
                var object = {
                    id: _this._resourceIRI.assignment(assignment.id),
                    definition: {
                        type: _this.activityType.assessment,
                        name: { 'en-US': assignment.name }
                    }
                }

                if (assignment.description) {
                    object.definition.description = { 'en-US': assignment.description }
                }

                return object;
            },

            assignment_question: function(assignment) {
                var object = {
                    id: _this._resourceIRI.assignment_question(assignment.id),
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

            comparison_question: function(comparison, comparison_number, pairing_algorithm) {
                var object = {
                    id: _this._resourceIRI.comparison_question(comparison.id),
                    definition: {
                        type: _this.activityType.question,
                        name: { 'en-US': "Assignment comparison #"+comparison_number }
                    }
                }

                object.definition.extensions = {};
                object.definition.extensions[_this.extension['comparison']] = comparison_number;
                object.definition.extensions[_this.extension['pair algorithm']] = pairing_algorithm;

                return object;
            },

            self_evaluation_question: function(comment) {
                return {
                    id: _this._resourceIRI.self_evaluation_question(comment.assignment_id),
                    definition: {
                        type: _this.activityType.question,
                        name: { 'en-US': "Assignment self-evaluation" }
                    }
                }
            },

            answer: function(answer) {
                return {
                    id: _this._resourceIRI.answer(answer.id),
                    definition: {
                        type: _this.activityType.solution,
                        name: { 'en-US': "Assignment answer" }
                    }
                }
            },

            answer_attachment: function(file) {
                return {
                    id: _this._resourceIRI.attachment(file.name),
                    definition: {
                        type: _this.activityType.file,
                        name: { 'en-US': "Assignment answer attachment" }
                    }
                }
            },

            answer_comment: function(comment) {
                return {
                    id: _this._resourceIRI.answer_comment(comment.id),
                    definition: {
                        type: _this.activityType.comment,
                        name: { 'en-US': "Assignment answer comment" }
                    }
                }
            },

            answer_evaluation_comment: function(comment) {
                return {
                    id: _this._resourceIRI.answer_comment(comment.id),
                    definition: {
                        type: _this.activityType.comment,
                        name: { 'en-US': "Assignment answer evaluation comment" }
                    }
                }
            },

            comparison: function(comparison) {
                return {
                    id: _this._resourceIRI.comparison(comparison.id),
                    definition: {
                        type: _this.activityType.solution,
                        name: { 'en-US': "Assignment comparison" }
                    }
                }
            },

            comparison_criterion: function(comparison, comparison_criterion) {
                return {
                    id: _this._resourceIRI.comparison_criterion(comparison_criterion.id),
                    definition: {
                        type: _this.activityType.solution,
                        name: { 'en-US': "Assignment criterion comparison" }
                    }
                }
            },

            self_evaluation: function(comment) {
                return {
                    id: _this._resourceIRI.answer_comment(comment.id),
                    definition: {
                        type: _this.activityType.review,
                        name: { 'en-US': "Assignment self-evaluation review" }
                    }
                }
            },

            page: function(relativePath) {
                return {
                    id: _this._resourceIRI.page(relativePath),
                    definition: {
                        type: _this.activityType.page
                    }
                }
            },

            page_section: function(relativePath, sectionName) {
                return {
                    id: _this._resourceIRI.page_section(relativePath, sectionName),
                    definition: {
                        type: _this.activityType.section,
                        name: { 'en-US': sectionName }
                    }
                }
            },

            modal: function(relativePath, modalName) {
                return {
                    id: _this._resourceIRI.modal(relativePath, modalName),
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
                    context.extensions[_this.extension['filters']] = options.filters;
                }

                if (options.sortOrder) {
                    if (!context.extensions) { context.extensions = {}; }
                    context.extensions[_this.extension['sort order']] = options.sortOrder;
                }

                return context;
            },

            assignment: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is course
                        parent: [{
                            id: _this._resourceIRI.course(assignment.course_id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            assignment_question: function(assignment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is assignment
                        parent: [{
                            id: _this._resourceIRI.assignment(assignment.id)
                        }],
                        // grouping is course
                        grouping: [{
                            id: _this._resourceIRI.course(assignment.course_id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            comparison_question: function(comparison, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is assignment + answer1 + answer2
                        parent: [{
                            id: _this._resourceIRI.assignment(comparison.assignment_id)
                        }, {
                            id: _this._resourceIRI.answer(comparison.answer1.id)
                        }, {
                            id: _this._resourceIRI.answer(comparison.answer2.id)
                        }],
                        // grouping is course
                        grouping: [{
                            id: _this._resourceIRI.course(comparison.course_id)
                        }]
                    }
                }, _this.context.basic(options));

                _.forEach(comparison.comparison_criteria, function(comparison_criterion) {
                    context.contextActivities.grouping.push({
                        id: _this._resourceIRI.criterion(comparison_criterion.criterion_id)
                    })
                });

                return context;
            },

            self_evaluation_question: function(comment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is assignment + answer
                        parent: [{
                            id: _this._resourceIRI.assignment(comment.assignment_id)
                        }, {
                            id: _this._resourceIRI.answer(comment.answer_id)
                        }],
                        // grouping is course
                        grouping: [{
                            id: _this._resourceIRI.course(comment.course_id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            answer: function(answer, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is assignment question
                        parent: [{
                            id: _this._resourceIRI.assignment_question(answer.assignment_id)
                        }],
                        // grouping is course + assignment
                        grouping: [{
                            id: _this._resourceIRI.course(answer.course_id)
                        }, {
                            id: _this._resourceIRI.assignment(answer.assignment_id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            comparison: function(comparison, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is assignment question
                        parent: [{
                            id: _this._resourceIRI.comparison_question(comparison.id)
                        }],
                        // grouping is course + assignment
                        grouping: [{
                            id: _this._resourceIRI.course(comparison.course_id)
                        }, {
                            id: _this._resourceIRI.assignment(comparison.assignment_id)
                        }, {
                            id: _this._resourceIRI.answer(comparison.answer1.id)
                        }, {
                            id: _this._resourceIRI.answer(comparison.answer2.id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            comparison_criterion: function(comparison, comparison_criterion, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is assignment question
                        parent: [{
                            id: _this._resourceIRI.comparison(comparison.id)
                        }, {
                            id: _this._resourceIRI.criterion(comparison_criterion.criterion_id)
                        }],
                        // grouping is course + assignment
                        grouping: [{
                            id: _this._resourceIRI.course(comparison.course_id)
                        }, {
                            id: _this._resourceIRI.assignment(comparison.assignment_id)
                        }, {
                            id: _this._resourceIRI.answer(comparison.answer1.id)
                        }, {
                            id: _this._resourceIRI.answer(comparison.answer2.id)
                        }, {
                            id: _this._resourceIRI.comparison_question(comparison.id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            self_evaluation: function(comment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is self-evaulation question
                        parent: [{
                            id: _this._resourceIRI.self_evaluation_question(comment.assignment_id)
                        }],
                        // grouping is course + assignment + answer
                        grouping: [{
                            id: _this._resourceIRI.course(comment.course_id)
                        }, {
                            id: _this._resourceIRI.assignment(comment.assignment_id)
                        }, {
                            id: _this._resourceIRI.answer(comment.answer_id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            answer_comment: function(comment, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is answer
                        parent: [{
                            id: _this._resourceIRI.answer(comment.answer_id)
                        }],
                        // grouping is course + assignment + assignment question
                        grouping: [{
                            id: _this._resourceIRI.course(comment.course_id)
                        }, {
                            id: _this._resourceIRI.assignment(comment.assignment_id)
                        }, {
                            id: _this._resourceIRI.assignment_question(comment.assignment_id)
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            answer_attachment: function(answer, options) {
                options = options || {};

                var context = angular.merge({
                    contextActivities: {
                        // parent is answer
                        parent: [{
                            id: _this._resourceIRI.answer(answer.id)
                        }],
                        // grouping is course + assignment + assignment question
                        grouping: [{
                            id: _this._resourceIRI.course(answer.course_id)
                        }, {
                            id: _this._resourceIRI.assignment(answer.assignment_id)
                        }, {
                            id: _this._resourceIRI.assignment_question(answer.assignment_id)
                        }]
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
                            id: locationUrl
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
                            id: _this._resourceIRI.page(relativePath),
                        }],
                        // other page's url unrelated to baseUrl
                        other: [{
                            id: locationUrl
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
                            id: _this._resourceIRI.page(relativePath),
                        }],
                        // other page's url unrelated to baseUrl
                        other: [{
                            id: locationUrl
                        }]
                    }
                }, _this.context.basic(options));

                return context;
            },

            inline_pdf: function(pdf_name, relativePath, locationUrl, options) {
                var context = _this.context.page_section(relativePath, locationUrl, options);
                context.contextActivities.other.push({
                    id: _this._resourceIRI.attachment(pdf_name),
                });
                return context;
            },

            answer_page_section: function(answer, relativePath, locationUrl, options) {
                var context = _this.context.page_section(relativePath, locationUrl, options);
                context.contextActivities.other.push({
                    id: _this._resourceIRI.answer(answer.id),
                });
                return context;
            },

            pdf_modal: function(pdf_name, relativePath, locationUrl, options) {
                var context = _this.context.modal(relativePath, locationUrl, options);
                context.contextActivities.other.push({
                    id: _this._resourceIRI.attachment(pdf_name),
                });
                return context;
            },
        };

        this.result = {
            basic: function(options) {
                options = options || {};

                var result = {};

                if (options.duration) {
                    result.duration = options.duration;
                }

                if (options.success != undefined) {
                    result.success = options.success;
                }

                if (options.completion != undefined) {
                    result.completion = options.completion;
                }

                return result;
            },

            answer: function(answer, options) {
                options = options || {};

                var result = angular.merge({
                    response: answer.content,
                    extensions: {}
                }, _this.result.basic(options));

                characterCount = answer.content ? _this._characterCount(answer.content) : 0;
                result.extensions[_this.extension['character count']] = characterCount;
                wordCount = answer.content ? _this._wordCount(answer.content) : 0;
                result.extensions[_this.extension['word count']] = wordCount;

                if (options.includeAttachment) {
                    if (answer.file) {
                        var fileIRI = _this._resourceIRI.attachment(answer.file.name);
                        result.extensions[_this.extension['attachment response']] = fileIRI;
                    }
                }

                return result;
            },

            answer_comment: function(comment, options) {
                options = options || {};

                var result = angular.merge({
                    response: comment.content,
                    extensions: {}
                }, _this.result.basic(options));

                characterCount = comment.content ? _this._characterCount(comment.content) : 0;
                result.extensions[_this.extension['character count']] = characterCount;
                wordCount = comment.content ? _this._wordCount(comment.content) : 0;
                result.extensions[_this.extension['word count']] = wordCount;

                return result;
            },

            comparison: function(comparison, options) {
                options = options || {};

                var response = "Undecided"
                if (comparison.winner == WinningAnswer.draw) {
                    response = "Draw"
                } else if (comparison.winner == WinningAnswer.answer1) {
                    response = _this._resourceIRI.answer(comparison.answer1_id)
                } else if (comparison.winner == WinningAnswer.answer2) {
                    response = _this._resourceIRI.answer(comparison.answer2_id)
                }

                var result = angular.merge({
                    response: response
                }, _this.result.basic(options));

                return result;
            },

            comparison_criterion: function(comparison, comparison_criterion, options) {
                options = options || {};

                var response = "Undecided"
                if (comparison_criterion.winner == WinningAnswer.answer1) {
                    response = _this._resourceIRI.answer(comparison.answer1_id)
                } else if (comparison_criterion.winner == WinningAnswer.answer2) {
                    response = _this._resourceIRI.answer(comparison.answer2_id)
                }

                var result = angular.merge({
                    response: response
                }, _this.result.basic(options));

                return result;
            },

            self_evaluation: function(comment, options) {
                options = options || {};

                var result = angular.merge({
                    response: comment.content,
                    extensions: {}
                }, _this.result.basic(options));

                characterCount = comment.content ? _this._characterCount(comment.content) : 0;
                result.extensions[_this.extension['character count']] = characterCount;
                wordCount = comment.content ? _this._wordCount(comment.content) : 0;
                result.extensions[_this.extension['word count']] = wordCount;

                return result;
            }
        }
    }]
);
module.service('xAPIStatementHelper',
    ["$location", "xAPI",
    function($location, xAPI) {
        // verb_answer_solution
        this.interacted_answer_solution = function(answer, registration, duration) {
            // skip if not yet loaded
            if (!answer.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.interacted,
                object: xAPI.object.answer(answer),
                context: xAPI.context.answer(answer, {
                    registration: registration
                }),
                result: xAPI.result.answer(answer, {
                    duration: duration
                })
            });
        };


        // verb_answer_attachment
        this.attached_answer_attachment = function(file, answer, registration) {
            // skip if not yet loaded
            if (!file.id || !answer.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.attached,
                object: xAPI.object.answer_attachment(file),
                context: xAPI.context.answer_attachment(answer, {
                    registration: registration
                })
            });
        };

        this.deleted_answer_attachment = function(file, answer, registration) {
            // skip if not yet loaded
            if (!file.id || !answer.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.deleted,
                object: xAPI.object.answer_attachment(file),
                context: xAPI.context.answer_attachment(answer, {
                    registration: registration
                })
            });
        };



        // verb_assignment_question
        this.initialize_assignment_question = function(assignment, registration) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.initialized,
                object: xAPI.object.assignment_question(assignment),
                context: xAPI.context.assignment_question(assignment, {
                    registration: registration
                })
            });
        };

        this.resume_assignment_question = function(assignment, registration) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.resumed,
                object: xAPI.object.assignment_question(assignment),
                context: xAPI.context.assignment_question(assignment, {
                    registration: registration
                })
            });
        };

        this.exited_assignment_question = function(assignment, registration, duration) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.exited,
                object: xAPI.object.assignment_question(assignment),
                context: xAPI.context.assignment_question(assignment, {
                    registration: registration
                }),
                result: xAPI.result.basic({
                    duration: duration,
                    success: false
                })
            });
        };


        // verb_page
        this.viewed_page = function() {
            var relativePath = $location.path();
            var pageUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.viewed,
                object: xAPI.object.page(relativePath),
                context: xAPI.context.page(pageUrl)
            });
        };

        this.filtered_page = function(filterParams) {
            var relativePath = $location.path();
            var pageUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.filtered,
                object: xAPI.object.page(relativePath),
                context: xAPI.context.page(pageUrl, {
                    filters: filterParams
                })
            });
        };

        this.sorted_page = function(sortOrder) {
            var relativePath = $location.path();
            var pageUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.sorted,
                object: xAPI.object.page(relativePath),
                context: xAPI.context.page(pageUrl, {
                    sortOrder: sortOrder
                })
            });
        };



        // verb_page_section
        this.opened_page_section = function(sectionName) {
            var relativePath = $location.path();
            var pageUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.opened,
                object: xAPI.object.page_section(relativePath, sectionName),
                context: xAPI.context.page_section(relativePath, pageUrl)
            });
        };

        this.closed_page_section = function(sectionName) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.closed,
                object: xAPI.object.page_section(relativePath, sectionName),
                context: xAPI.context.page_section(relativePath, locationUrl)
            });
        };

        this.filtered_page_section = function(sectionName, filterParams) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.filtered,
                object: xAPI.object.page_section(relativePath, sectionName),
                context: xAPI.context.page_section(relativePath, locationUrl, {
                    filters: filterParams
                })
            });
        };

        this.sorted_page_section = function(sectionName, sortOrder) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.sorted,
                object: xAPI.object.page_section(relativePath, sectionName),
                context: xAPI.context.page_section(relativePath, locationUrl, {
                    sortOrder: sortOrder
                })
            });
        };


        // verb_modal
        this.opened_modal = function(modalName) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.opened,
                object: xAPI.object.modal(relativePath, modalName),
                context: xAPI.context.modal(relativePath, locationUrl)
            });
        };

        this.closed_modal = function(modalName) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.closed,
                object: xAPI.object.modal(relativePath, modalName),
                context: xAPI.context.modal(relativePath, locationUrl)
            });
        };

        this.filtered_modal = function(modalName, filterParams) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.filtered,
                object: xAPI.object.modal(relativePath, modalName),
                context: xAPI.context.modal(relativePath, locationUrl, {
                    filters: filterParams
                })
            });
        };

        this.sorted_modal = function(modalName, sortOrder) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.sorted,
                object: xAPI.object.modal(relativePath, modalName),
                context: xAPI.context.modal(relativePath, locationUrl, {
                    sortOrder: sortOrder
                })
            });
        };


        // verb_inline_pdf
        this.opened_inline_pdf = function(pdf_name) {
            var relativePath = $location.path();
            var pageUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.opened,
                object: xAPI.object.page_section(relativePath, "Inline PDF Attachment"),
                context: xAPI.context.inline_pdf(pdf_name, relativePath, pageUrl)
            });
        };

        this.closed_inline_pdf = function(pdf_name) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.closed,
                object: xAPI.object.page_section(relativePath, "Inline PDF Attachment"),
                context: xAPI.context.inline_pdf(pdf_name, relativePath, locationUrl)
            });
        };



        // verb_pdf_modal
        this.opened_pdf_modal = function(pdf_name) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.opened,
                object: xAPI.object.modal(relativePath, "View PDF Attachment"),
                context: xAPI.context.pdf_modal(pdf_name, relativePath, locationUrl)
            });
        };

        this.closed_pdf_modal = function(pdf_name) {
            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.closed,
                object: xAPI.object.modal(relativePath, "View PDF Attachment"),
                context: xAPI.context.pdf_modal(pdf_name, relativePath, locationUrl)
            });
        };



        // verb_answer_replies_section
        this.opened_answer_replies_section = function(answer) {
            if (!answer.id) { return; }

            var relativePath = $location.path();
            var pageUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.opened,
                object: xAPI.object.page_section(relativePath, "Answer replies"),
                context: xAPI.context.answer_page_section(answer, relativePath, pageUrl)
            });
        };

        this.closed_answer_replies_section = function(answer) {
            if (!answer.id) { return; }

            var relativePath = $location.path();
            var locationUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.closed,
                object: xAPI.object.page_section(relativePath, "Answer replies"),
                context: xAPI.context.answer_page_section(answer, relativePath, locationUrl)
            });
        };


        // verb_answer_show_all_section
        this.opened_answer_show_all_section = function(answer) {
            if (!answer.id) { return; }

            var relativePath = $location.path();
            var pageUrl = $location.absUrl();

            xAPI.generateStatement({
                verb: xAPI.verb.opened,
                object: xAPI.object.page_section(relativePath, "Answer show all"),
                context: xAPI.context.answer_page_section(answer, relativePath, pageUrl)
            });
        };


        // verb_comparison_question
        this.initialize_comparison_question = function(comparison, comparison_number, pairing_algorithm, registration) {
            // skip if not yet loaded
            if (!comparison.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.initialized,
                object: xAPI.object.comparison_question(comparison, comparison_number, pairing_algorithm),
                context: xAPI.context.comparison_question(comparison, {
                    registration: registration
                })
            });
        };

        this.resume_comparison_question = function(comparison, comparison_number, pairing_algorithm, registration) {
            // skip if not yet loaded
            if (!comparison.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.resumed,
                object: xAPI.object.comparison_question(comparison, comparison_number, pairing_algorithm),
                context: xAPI.context.comparison_question(comparison, {
                    registration: registration
                })
            });
        };

        this.exited_comparison_question = function(comparison, comparison_number, pairing_algorithm, registration, duration) {
            // skip if not yet loaded
            if (!comparison.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.exited,
                object: xAPI.object.comparison_question(comparison, comparison_number, pairing_algorithm),
                context: xAPI.context.comparison_question(comparison, {
                    registration: registration
                }),
                result: xAPI.result.basic({
                    duration: duration,
                    success: false
                })
            });
        };

        // verb_comparison_criterion_solution
        this.interacted_comparison_criterion_solution = function(comparison, comparison_criterion, registration) {
            // skip if not yet loaded
            if (!comparison.id || !comparison_criterion.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.interacted,
                object: xAPI.object.comparison_criterion(comparison, comparison_criterion),
                context: xAPI.context.comparison_criterion(comparison, comparison_criterion, {
                    registration: registration
                }),
                result: xAPI.result.comparison_criterion(comparison, comparison_criterion)
            });
        };


        // verb_answer_comment
        this.interacted_answer_comment = function(comment, registration, duration) {
            // skip if not yet loaded
            if (!comment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.interacted,
                object: xAPI.object.answer_evaluation_comment(comment),
                context: xAPI.context.answer_comment(comment, {
                    registration: registration
                }),
                result: xAPI.result.answer_comment(comment, {
                    duration: duration
                })
            });
        };



        // verb_self_evaluation_question
        this.initialize_self_evaluation_question = function(comment, registration) {
            // skip if not yet loaded
            if (!comment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.initialized,
                object: xAPI.object.self_evaluation_question(comment),
                context: xAPI.context.self_evaluation_question(comment, {
                    registration: registration
                })
            });
        };

        this.resume_self_evaluation_question = function(comment, registration) {
            // skip if not yet loaded
            if (!comment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.resumed,
                object: xAPI.object.self_evaluation_question(comment),
                context: xAPI.context.self_evaluation_question(comment, {
                    registration: registration
                })
            });
        };

        this.exited_self_evaluation_question = function(comment, registration, duration) {
            // skip if not yet loaded
            if (!comment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.exited,
                object: xAPI.object.self_evaluation_question(comment),
                context: xAPI.context.self_evaluation_question(comment, {
                    registration: registration
                }),
                result: xAPI.result.basic({
                    duration: duration,
                    success: false
                })
            });
        };


        // verb_self_evaluation_review
        this.interacted_self_evaluation_review = function(comment, registration, duration) {
            // skip if not yet loaded
            if (!comment.id) { return; }

            xAPI.generateStatement({
                verb: xAPI.verb.interacted,
                object: xAPI.object.self_evaluation(comment),
                context: xAPI.context.self_evaluation(comment, {
                    registration: registration
                }),
                result: xAPI.result.self_evaluation(comment, {
                    duration: duration
                })
            });
        };
    }]
);

module.run(
    ['$rootScope', '$location', 'xAPIStatementHelper',
    function ($rootScope, $location, xAPIStatementHelper) {

    $rootScope.$on('$routeChangeSuccess', function() {
        xAPIStatementHelper.viewed_page();
    });
}]);

// End anonymous function
})();
