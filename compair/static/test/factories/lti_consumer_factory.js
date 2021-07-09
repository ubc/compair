var objectAssign = require('object-assign');

var ltiConsumerTemplate = {
    "id": null,
    "oauth_consumer_key": null,
    "oauth_consumer_secret": null,
    "active": true,
    "global_unique_identifier_param": null,
    "custom_param_regex_sanitizer": null,
    "student_number_param": null,
    "created": "Mon, 18 Apr 2016 17:38:23 -0000",
    "modified": "Mon, 18 Apr 2016 17:38:23 -0000"
}

function LTIConsumerFactory() {};

LTIConsumerFactory.prototype.generateConsumer = function (id, oauth_consumer_key, oauth_consumer_secret, parameters) {
    var newConsumer = objectAssign({}, ltiConsumerTemplate, parameters);
    newConsumer.id = id;
    newConsumer.oauth_consumer_key = oauth_consumer_key;
    newConsumer.oauth_consumer_secret = oauth_consumer_secret;

    return newConsumer;
};

module.exports = LTIConsumerFactory;
