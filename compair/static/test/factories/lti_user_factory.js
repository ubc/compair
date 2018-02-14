var objectAssign = require('object-assign');

var ltiUserTemplate = {
    "id": null,
    "lti_consumer_id": null,
    "compair_user_id": null,
    "lti_user_id": null,
    "lis_person_name_full": null,
    "oauth_consumer_key": null
}

function LTIUserFactory() {};

LTIUserFactory.prototype.generateLTIUser = function (id, lti_consumer_id, compair_user_id, parameters) {
    var newLTIUser = objectAssign({}, ltiUserTemplate, parameters);
    newLTIUser.id = id;
    newLTIUser.lti_consumer_id = lti_consumer_id;
    newLTIUser.compair_user_id = compair_user_id;

    return newLTIUser;
};

module.exports = LTIUserFactory;
