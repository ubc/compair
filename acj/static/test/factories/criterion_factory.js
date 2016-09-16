var objectAssign = require('object-assign');

var criterionTemplate = {
    "id": null,
    "user_id": null,
    "name": null,
    "description": null,
    "default": true,
    "public": false,
    "compared": false,
    "created": "Mon, 18 Apr 2016 17:38:23 -0000",
    "modified": "Mon, 18 Apr 2016 17:38:23 -0000",
}

function CriterionFactory() {};

CriterionFactory.prototype.generateCriterion = function (id, user_id, parameters) {
    var newCriterion = objectAssign({}, criterionTemplate, parameters);
    newCriterion.id = id;
    newCriterion.user_id = user_id;

    return newCriterion;
};

CriterionFactory.prototype.getDefaultCriterion = function () {
    return {
        "id": "abcABC123-abcABC123_Z",
        "user_id": "abcABC123-abcABC123_Z",
        "name": "Which is better?",
        "description": "<p>Choose the response that you think is the better of the two.</p>",
        "default": true,
        "public": true,
        "compared": false,
        "created": "Mon, 18 Apr 2016 17:38:23 -0000",
        "modified": "Mon, 18 Apr 2016 17:38:23 -0000",
    };
};

module.exports = CriterionFactory;
