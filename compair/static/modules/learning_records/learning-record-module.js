// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.learning_records.learning_record', [
    'ngResource',
    'angularMoment',
    'angular-uuid',
    'ubc.ctlt.compair.learning_records.caliper',
    'ubc.ctlt.compair.learning_records.xapi'
]);

/***** Providers *****/
module.constant('LearningRecordSettings', {
    xapi_enabled: false,
    caliper_enabled: false,
    baseUrl: '',
});

module.service('LearningRecord',
    [ "uuid", "moment",
    function(uuid, moment) {
        return {
            generateAttemptTracking: function() {
                var attempt_uuid = uuid.v4();
                var started = moment();
                return {
                    getUUID: function() {
                        return attempt_uuid;
                    },
                    getDuration: function() {
                        var duration = moment.duration(moment().diff(started));
                        return duration.toISOString();
                    },
                    getStarted: function() {
                        return started.toISOString();
                    },
                    getEnded: function() {
                        return moment().toISOString();
                    },
                    toParams: function() {
                        return angular.copy({
                            attempt_uuid: this.getUUID(),
                            attempt_started: started.toDate(),
                            attempt_ended: moment().toDate(),
                            attempt_duration: this.getDuration()
                        });
                    }
                }
            },
            urlSafeEncode: function(url) {
                var first = true;
                return url.replace(/#/g, function(value) {
                    if (first) {
                        first = false;
                        return value;
                    } else {
                        return "%23";
                    }
                });
            },
            _stripHTML: function(text) {
                text = String(text) || '';
                text = text.replace(/<[^>]+>/g, '');
                text = text.replace('&nbsp;', ' ');
                return _.unescape(text);
            },
            _characterCount: function(text) {
                text = String(text) || '';
                text = this._stripHTML(text);
                // replace linebreaks with whitespace to help get a more accurate count
                text = text.replace(/(\r\n|\n|\r)/g, ' ');
                return text.length;
            },
            _wordCount: function(text) {
                text = String(text) || '';
                text = this._stripHTML(text);
                // replace linebreaks with whitespace to help get a more accurate count
                text = text.replace(/(\r\n|\n|\r)/g, ' ');
                words = _.filter(text.split(/\s+/), function(word) {
                    return word.length > 0;
                });
                return words.length;
            }
        };
    }]
);

module.service('ResourceIRI',
    [ "LearningRecordSettings",
    function(LearningRecordSettings) {
        return {
            _baseUrl: function() {
                return LearningRecordSettings.baseUrl.replace(/\/+$/, "");
            },
            _relativePathSaveEncode: function(relativePath) {
                return relativePath.replace(/#/g, "%23");
            },
            _appPageUrl: function() {
                return this._baseUrl() + "/app/#";
            },
            _appUrl: function() {
                return this._baseUrl() + "/app/";
            },
            _attachmentUrl: function() {
                return this._baseUrl() + "/app/attachment/";
            },

            course: function(course_id) {
                return this._appUrl() + "course/"+course_id;
            },
            criterion: function(criterion_id) {
                return this._appUrl() + "criterion/"+criterion_id;
            },

            assignment: function(course_id, assignment_id) {
                return this.course(course_id) + "/assignment/"+assignment_id;
            },
            assignment_attempt: function(course_id, assignment_id, attempt_id) {
                return this.assignment(course_id, assignment_id) + "/attempt/"+attempt_id;
            },


            assignment_question: function(course_id, assignment_id) {
                return this.assignment(course_id, assignment_id) + "/question";
            },
            answer: function(course_id, assignment_id, answer_id) {
                return this.assignment(course_id, assignment_id) + "/answer/"+answer_id;
            },
            answer_attempt: function(course_id, assignment_id, attempt_id) {
                return this.assignment_question(course_id, assignment_id) + "/attempt/"+attempt_id;
            },


            comparison_question: function(course_id, assignment_id, comparison_number) {
                return this.assignment(course_id, assignment_id) + "/comparison/question/"+comparison_number;
            },
            comparison: function(course_id, assignment_id, comparison_id) {
                return this.assignment(course_id, assignment_id) + "/comparison/"+comparison_id;
            },
            comparison_attempt: function(course_id, assignment_id, comparison_number, attempt_id) {
                return this.comparison_question(course_id, assignment_id, comparison_number) + "/attempt/"+attempt_id;
            },



            evaluation_question: function(course_id, assignment_id, evaluation_number) {
                return this.assignment(course_id, assignment_id) + "/evaluation/question/"+evaluation_number;
            },
            evaluation: function(course_id, assignment_id, answer_id, answer_comment_id) {
                return this.answer_comment(course_id, assignment_id, answer_id, answer_comment_id) + "/evaluation";
            },
            evaluation_attempt: function(course_id, assignment_id, evaluation_number, attempt_id) {
                return this.evaluation_question(course_id, assignment_id, evaluation_number) + "/attempt/"+attempt_id;
            },




            self_evaluation_question: function(course_id, assignment_id) {
                return this.assignment(course_id, assignment_id) + "/self-evaluation/question";
            },
            self_evaluation: function(course_id, assignment_id, answer_id, answer_comment_id) {
                return this.answer_comment(course_id, assignment_id, answer_id, answer_comment_id) + "/self-evaluation";
            },
            self_evaluation_attempt: function(course_id, assignment_id, attempt_id) {
                return this.self_evaluation_question(course_id, assignment_id) + "/attempt/"+attempt_id;
            },


            answer_comment: function(course_id, assignment_id, answer_id, answer_comment_id) {
                return this.answer(course_id, assignment_id, answer_id) + "/comment/"+comment_id;
            },
            attachment: function(fileName) {
                return this._attachmentUrl() + encodeURIComponent(fileName);
            },


            page: function(relativePath) {
                return this._appPageUrl() + this._relativePathSaveEncode(relativePath);
            },
            page_section: function(relativePath, sectionName) {
                var safeRelativePath = this._relativePathSaveEncode(relativePath);
                return this.page(safeRelativePath) + "?section="+encodeURIComponent(sectionName);
            },
            modal: function(relativePath, modalName) {
                var safeRelativePath = this._relativePathSaveEncode(relativePath);
                return this.page(safeRelativePath) + "?modal="+encodeURIComponent(modalName);
            }
        };
    }]
);

module.service('LearningRecordStatementHelper',
    ["$location", "xAPI", "Caliper", "LearningRecordSettings", 'LearningRecord',
    "$routeParams",
    function($location, xAPI, Caliper, LearningRecordSettings, LearningRecord,
             $routeParams) {

        // verb_assignment_question
        this.initialize_assignment_question = function(assignment, tracking) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.answer_attempt(assignment, tracking, false),
                    context: xAPI.context.answer_attempt(assignment, {
                        registration: tracking.getUUID()
                    })
                });

                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.assignment_attempt(assignment, tracking, false),
                    context: xAPI.context.assignment_attempt(assignment, {
                        registration: tracking.getUUID()
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_ITEM_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.assignment_question(assignment),
                    generated: Caliper.entities.answer_attempt(assignment, tracking, false),
                }, true)

                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.assignment(assignment),
                    generated: Caliper.entities.assignment_attempt(assignment, tracking, false),
                }, true)
            }
        };

        this.exited_assignment_question = function(assignment, tracking) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.exited,
                    object: xAPI.object.assignment_attempt(assignment, tracking, true),
                    context: xAPI.context.assignment_attempt(assignment, {
                        registration: tracking.getUUID()
                    }),
                    result: xAPI.result.basic_attempt(tracking, true, {
                        success: false
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_EVENT'],
                    action: Caliper.actions['PAUSED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.assignment(assignment),
                    generated: Caliper.entities.assignment_attempt(assignment, tracking, true),
                })
            }
        };


        // verb_comparison_question
        this.initialize_comparison_question = function(assignment, comparison_number, tracking) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            var evaluation_number1 = (comparison_number*2)-1;
            var evaluation_number2 = (comparison_number*2);

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.comparison_attempt(assignment, comparison_number, tracking, false),
                    context: xAPI.context.comparison_attempt(assignment, comparison_number, {
                        registration: tracking.getUUID()
                    })
                });

                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.evaluation_attempt(assignment, evaluation_number1, tracking, false),
                    context: xAPI.context.evaluation_attempt(assignment, evaluation_number1, {
                        registration: tracking.getUUID()
                    })
                });
                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.evaluation_attempt(assignment, evaluation_number2, tracking, false),
                    context: xAPI.context.evaluation_attempt(assignment, evaluation_number2, {
                        registration: tracking.getUUID()
                    })
                });

                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.assignment_attempt(assignment, tracking, false),
                    context: xAPI.context.assignment_attempt(assignment, {
                        registration: tracking.getUUID()
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_ITEM_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.comparison_question(assignment, comparison_number),
                    generated: Caliper.entities.comparison_attempt(assignment, comparison_number, tracking, false),
                })

                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_ITEM_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.evaluation_question(assignment, evaluation_number1),
                    generated: Caliper.entities.evaluation_attempt(assignment, evaluation_number1, tracking, false),
                })
                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_ITEM_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.evaluation_question(assignment, evaluation_number2),
                    generated: Caliper.entities.evaluation_attempt(assignment, evaluation_number2, tracking, false),
                })

                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.assignment(assignment),
                    generated: Caliper.entities.assignment_attempt(assignment, tracking, false),
                })
            }
        };

        this.exited_comparison_question = function(assignment, tracking) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.exited,
                    object: xAPI.object.assignment_attempt(assignment, tracking, true),
                    context: xAPI.context.assignment_attempt(assignment, {
                        registration: tracking.getUUID()
                    }),
                    result: xAPI.result.basic_attempt(tracking, true, {
                        success: false
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_EVENT'],
                    action: Caliper.actions['PAUSED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.assignment(assignment),
                    generated: Caliper.entities.assignment_attempt(assignment, tracking, true),
                })
            }
        };

        // verb_self_evaluation_question
        this.initialize_self_evaluation_question = function(assignment, tracking) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.self_evaluation_attempt(assignment, tracking, false),
                    context: xAPI.context.self_evaluation_attempt(assignment, {
                        registration: tracking.getUUID()
                    })
                });

                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.initialized,
                    object: xAPI.object.assignment_attempt(assignment, tracking, false),
                    context: xAPI.context.assignment_attempt(assignment, {
                        registration: tracking.getUUID()
                    })
                });
            }
            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_ITEM_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.self_evaluation_question(assignment),
                    generated: Caliper.entities.self_evaluation_attempt(assignment, tracking, false),
                })

                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_EVENT'],
                    action: Caliper.actions['STARTED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.assignment(assignment),
                    generated: Caliper.entities.assignment_attempt(assignment, tracking, false),
                })
            }
        };

        this.exited_self_evaluation_question = function(assignment, tracking) {
            // skip if not yet loaded
            if (!assignment.id) { return; }

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(assignment.course_id, {
                    verb: xAPI.verb.exited,
                    object: xAPI.object.assignment_attempt(assignment, tracking, true),
                    context: xAPI.context.assignment_attempt(assignment, {
                        registration: tracking.getUUID()
                    }),
                    result: xAPI.result.basic_attempt(tracking, true, {
                        success: false
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(assignment.course_id, {
                    type: Caliper.events['ASSESSMENT_EVENT'],
                    action: Caliper.actions['PAUSED'],
                    profile: Caliper.profiles['ASSESSMENT'],
                    object: Caliper.entities.assignment(assignment),
                    generated: Caliper.entities.assignment_attempt(assignment, tracking, true),
                })
            }
        };


        // verb_page
        this.viewed_page = function() {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.viewed,
                    object: xAPI.object.page(relativePath),
                    context: xAPI.context.page(absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['NAVIGATION_EVENT'],
                    action: Caliper.actions['NAVIGATED_TO'],
                    profile: Caliper.profiles['READING'],
                    object: Caliper.entities.page(relativePath),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.filtered_page = function(filterParams) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.filtered,
                    object: xAPI.object.page(relativePath),
                    context: xAPI.context.page(absoluteUrl, {
                        filters: filterParams
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['SEARCH_EVENT'],
                    action: Caliper.actions['SEARCHED'],
                    profile: Caliper.profiles['SEARCH'],
                    object: Caliper.entities.page(relativePath),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl),
                        filters: filterParams
                    }
                })
            }
        };

        this.sorted_page = function(sortOrder) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.sorted,
                    object: xAPI.object.page(relativePath),
                    context: xAPI.context.page(absoluteUrl, {
                        sortOrder: sortOrder
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['SEARCH_EVENT'],
                    action: Caliper.actions['SEARCHED'],
                    profile: Caliper.profiles['SEARCH'],
                    object: Caliper.entities.page(relativePath),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl),
                        sortOrder: sortOrder
                    }
                })
            }
        };



        // verb_page_section
        this.opened_page_section = function(sectionName) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.opened,
                    object: xAPI.object.page_section(relativePath, sectionName),
                    context: xAPI.context.page_section(relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['SHOWED'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, sectionName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.closed_page_section = function(sectionName) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.closed,
                    object: xAPI.object.page_section(relativePath, sectionName),
                    context: xAPI.context.page_section(relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['HID'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, sectionName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.filtered_page_section = function(sectionName, filterParams) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.filtered,
                    object: xAPI.object.page_section(relativePath, sectionName),
                    context: xAPI.context.page_section(relativePath, absoluteUrl, {
                        filters: filterParams
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['SEARCH_EVENT'],
                    action: Caliper.actions['SEARCHED'],
                    profile: Caliper.profiles['SEARCH'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, sectionName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl),
                        filters: filterParams
                    }
                })
            }
        };

        this.sorted_page_section = function(sectionName, sortOrder) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.sorted,
                    object: xAPI.object.page_section(relativePath, sectionName),
                    context: xAPI.context.page_section(relativePath, absoluteUrl, {
                        sortOrder: sortOrder
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['SEARCH_EVENT'],
                    action: Caliper.actions['SEARCHED'],
                    profile: Caliper.profiles['SEARCH'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, sectionName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl),
                        sortOrder: sortOrder
                    }
                })
            }
        };


        // verb_modal
        this.opened_modal = function(modalName) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.opened,
                    object: xAPI.object.modal(relativePath, modalName),
                    context: xAPI.context.modal(relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['SHOWED'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, modalName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.closed_modal = function(modalName) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.closed,
                    object: xAPI.object.modal(relativePath, modalName),
                    context: xAPI.context.modal(relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['HID'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, modalName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.filtered_modal = function(modalName, filterParams) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.filtered,
                    object: xAPI.object.modal(relativePath, modalName),
                    context: xAPI.context.modal(relativePath, absoluteUrl, {
                        filters: filterParams
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['SEARCH_EVENT'],
                    action: Caliper.actions['SEARCHED'],
                    profile: Caliper.profiles['SEARCH'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, modalName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl),
                        filters: filterParams
                    }
                })
            }
        };

        this.sorted_modal = function(modalName, sortOrder) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.sorted,
                    object: xAPI.object.modal(relativePath, modalName),
                    context: xAPI.context.modal(relativePath, absoluteUrl, {
                        sortOrder: sortOrder
                    })
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['SEARCH_EVENT'],
                    action: Caliper.actions['SEARCHED'],
                    profile: Caliper.profiles['SEARCH'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, modalName),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl),
                        sortOrder: sortOrder
                    }
                })
            }
        };


        // verb_inline_kaltura_media
        this.opened_inline_kaltura_media = function(attachment_name) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.opened,
                    object: xAPI.object.page_section(relativePath, attachment_name),
                    context: xAPI.context.attachment_inline(attachment_name, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['SHOWED'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, attachment_name),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.closed_inline_kaltura_media = function(attachment_name) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.closed,
                    object: xAPI.object.page_section(relativePath, attachment_name),
                    context: xAPI.context.attachment_inline(attachment_name, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['HID'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, attachment_name),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        // verb_attachment_modal
        this.opened_attachment_modal = function(attachment_name) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.opened,
                    object: xAPI.object.modal(relativePath, attachment_name),
                    context: xAPI.context.attachment_modal(attachment_name, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['SHOWED'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, attachment_name),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.closed_attachment_modal = function(attachment_name) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.closed,
                    object: xAPI.object.modal(relativePath, attachment_name),
                    context: xAPI.context.attachment_modal(attachment_name, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['HID'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, attachment_name),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };



        // verb_embeddable_content_modal
        this.opened_embeddable_content_modal = function(contentUrl) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.opened,
                    object: xAPI.object.modal(relativePath, contentUrl),
                    context: xAPI.context.embeddable_content_modal(contentUrl, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['SHOWED'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, contentUrl),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.closed_embeddable_content_modal = function(contentUrl) {
            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.closed,
                    object: xAPI.object.modal(relativePath, contentUrl),
                    context: xAPI.context.embeddable_content_modal(contentUrl, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['HID'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.modal(relativePath, contentUrl),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };



        // verb_answer_replies_section
        this.opened_answer_replies_section = function(answer) {
            if (!answer.id) { return; }

            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.opened,
                    object: xAPI.object.page_section(relativePath, "answer/"+answer.id+"/replies"),
                    context: xAPI.context.answer_page_section(answer, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['SHOWED'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, "answer/"+answer.id+"/replies"),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };

        this.closed_answer_replies_section = function(answer) {
            if (!answer.id) { return; }

            var relativePath = $location.path();
            var absoluteUrl = $location.absUrl();
            var course_id = $routeParams.courseId;

            if (LearningRecordSettings.xapi_enabled) {
                xAPI.generateStatement(course_id, {
                    verb: xAPI.verb.closed,
                    object: xAPI.object.page_section(relativePath, "answer/"+answer.id+"/replies"),
                    context: xAPI.context.answer_page_section(answer, relativePath, absoluteUrl)
                });
            }

            if (LearningRecordSettings.caliper_enabled) {
                Caliper.generateEvent(course_id, {
                    type: Caliper.events['EVENT'],
                    action: Caliper.actions['HID'],
                    profile: Caliper.profiles['GENERAL'],
                    object: Caliper.entities.page(relativePath),
                    target: Caliper.entities.page_section(relativePath, "answer/"+answer.id+"/replies"),
                    extensions: {
                        absoluteUrl: LearningRecord.urlSafeEncode(absoluteUrl)
                    }
                })
            }
        };
    }]
);

module.run(
    ['$rootScope', 'LearningRecordStatementHelper',
    function ($rootScope, LearningRecordStatementHelper) {

    $rootScope.$on('$routeChangeSuccess', function() {
        LearningRecordStatementHelper.viewed_page();
    });
}]);

// End anonymous function
})();
