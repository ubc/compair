var objectAssign = require('object-assign');

var courseTemplate = {
    "id": null,
    "name": null,
    "year": 2015,
    "term": null,
    "sandbox": false,
    "start_time": null,
    "end_time": null,
    "available": true,
    "start_date": "Fri, 02 Jan 2015 00:00:00 -0000",
    "end_date": null,
    "assignment_count": 0,
    "student_assignment_count": 0,
    "student_count": 0,
    "modified": "Sun, 11 Jan 2015 08:44:46 -0000",
    "created": "Sun, 11 Jan 2015 08:44:46 -0000",
}

function CourseFactory() {};

CourseFactory.prototype.generateCourse = function (id, parameters) {
    var newCourse = objectAssign({}, courseTemplate, parameters);
    newCourse.id = id;

    return newCourse;
};

module.exports = CourseFactory;
