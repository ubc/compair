var objectAssign = require('object-assign');

var ltiContextTemplate = {
    "id": null,
    "compair_course_id": null,
    "compair_course_name": null,
    "oauth_consumer_key": null,
    "context_id": null,
    "context_title": null,
    'modified': "Mon, 18 Apr 2016 17:38:23 -0000",
    'created': "Mon, 18 Apr 2016 17:38:23 -0000"
}

function LTIContextFactory() {};

LTIContextFactory.prototype.generateContext = function (id, lti_consumer, course, parameters) {
    var newContext = objectAssign({}, ltiContextTemplate, parameters);
    newContext.id = id;
    newContext.compair_course_id = course.id;
    newContext.compair_course_name = course.name;
    newContext.oauth_consumer_key = lti_consumer.oauth_consumer_key;

    return newContext;
};

module.exports = LTIContextFactory;
