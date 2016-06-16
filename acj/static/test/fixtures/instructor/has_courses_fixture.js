var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory  = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var CriteriaFactory  = require('../../factories/criteria_factory.js');
var criteriaFactory = new CriteriaFactory();

var storage = {
    session: {},
    users: [],
    courses: [],
    user_courses: []
}

var admin = userFactory.generateUser(1, "System Administrator", {
    username: "root",
    displayname: "root",
    firstname: "JaNy",
    lastname: "bwsV",
    fullname: "JaNy bwsV",
});
storage.users.push(admin);

var instructor = userFactory.generateUser(2, "Instructor", {
    username: "instructor1",
    displayname: "First Instructor",
    firstname: "First",
    lastname: "Instructor",
    fullname: "First Instructor",
    email: "first.instructor@exmple.com"
});
storage.users.push(instructor);


var course1 = courseFactory.generateCourse(1, {
    name: "CHEM 111",
    description: "<p>CHEM 111 description<p>",
});
storage.courses.push(course1);

var course2 = courseFactory.generateCourse(2, {
    name: "PHYS 101",
    description: "<p>PHYS 101  description<p>",
});
storage.courses.push(course2);

// user_courses
storage.user_courses[instructor.id] = [
    { courseId: course1.id, courseRole: "Instructor", groupName: null },
    { courseId: course2.id, courseRole: "Instructor", groupName: null }
];

storage.loginDetails = { id: instructor.id, username: instructor.username, password: "password" };
storage.session = sessionFactory.generateSession(instructor.id, instructor.system_role, {
    "Course": {
        "delete": {'1': false, '2': false},
        "edit": {'1': true, '2': true},
        "manage": {'1': false, '2': false},
        "read": {'1': true, '2': true}
    },
    "Assignment": {
        "create": {'1': true},
        "delete": {'1': true},
        "edit": {'1': true},
        "manage": {'1': true},
        "read": {'1': true}
    },
});

module.exports = storage;