var objectAssign = require('object-assign');

var thirdPartyUserTemplate = {
    "id": null,
    "user_id": null,
    "third_party_type": null,
    "unique_identifier": null,
    "_params": null,
    "system_role": null,
    "created": "Mon, 18 Apr 2016 17:38:23 -0000",
    "modified": "Mon, 18 Apr 2016 17:38:23 -0000"
}

function thirdPartyUserFactory() {};

thirdPartyUserFactory.prototype.generatethirdPartyUser = function (id, user_id, parameters) {
    var newThirdPartyUser = objectAssign({}, thirdPartyUserTemplate, parameters);
    newThirdPartyUser.id = id;
    newThirdPartyUser.user_id = user_id;

    return newThirdPartyUser;
};

module.exports = thirdPartyUserFactory;
