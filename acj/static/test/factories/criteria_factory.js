var objectAssign = require('object-assign');

var criteriaTemplate = {
    "id": null, 
    "users_id": null,
    "name": null, 
    "description": null,
    "default": true, 
    "judged": false,  
    "created": "Mon, 18 Apr 2016 17:38:23 -0000", 
    "modified": "Mon, 18 Apr 2016 17:38:23 -0000", 
}

function CriteriaFactory() {};

CriteriaFactory.prototype.generateCriteria = function (id, user_id, parameters) {
    var newCriteria = objectAssign({}, criteriaTemplate, parameters);
    newCriteria.id = id;
    newCriteria.users_id = user_id;
    
    return newCriteria;
};

CriteriaFactory.prototype.getDefaultCriteria = function () {
    return {
        "id": 1,
        "users_id": 1,
        "name": "Which is better?",
        "description": "<p>Choose the response that you think is the better of the two.</p>",
        "default": true,
        "judged": false,
        "created": "Mon, 18 Apr 2016 17:38:23 -0000", 
        "modified": "Mon, 18 Apr 2016 17:38:23 -0000", 
    };
};

module.exports = CriteriaFactory;
