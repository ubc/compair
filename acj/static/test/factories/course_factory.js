var objectAssign = require('object-assign');

var courseTemplate = {
    "id": null,
    "name": null,
    "year": 2015,
    "term": null,
    "fullname": null,
    "description": null,
    "start_time": null,
    "end_time": null,
    "available": true,
    "modified": "Sun, 11 Jan 2015 08:44:46 -0000",
    "created": "Sun, 11 Jan 2015 08:44:46 -0000"
}

function CourseFactory() {};

CourseFactory.prototype.generateCourse = function (id, parameters) {
    var newCourse = objectAssign({}, courseTemplate, parameters);
    newCourse.id = id;

    return newCourse;
};

module.exports = CourseFactory;
