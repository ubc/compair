var objectAssign = require('object-assign');

var groupTemplate = {
    "id": null,
    "course_id": null,
    "name": null,
    "created": "Mon, 18 Apr 2016 17:38:23 -0000",
    "modified": "Mon, 18 Apr 2016 17:38:23 -0000",
}

function GroupFactory() {};

GroupFactory.prototype.generateGroup = function (id, course_id, parameters) {
    var newGroup = objectAssign({}, groupTemplate, parameters);
    newGroup.id = id;
    newGroup.course_id = course_id;

    return newGroup;
};

module.exports = GroupFactory;
