var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory  = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var storage = {
    session: {},
    users: {},
    courses: {},
    user_courses: {}
}

var admin = userFactory.generateUser("1abcABC123-abcABC123_Z", "System Administrator", {
    username: "root",
    displayname: "root",
    firstname: "JaNy",
    lastname: "bwsV",
    fullname: "JaNy bwsV",
});
storage.users[admin.id] = admin;

var instructor = userFactory.generateUser("2abcABC123-abcABC123_Z", "Instructor", {
    username: "instructor1",
    displayname: "First Instructor",
    firstname: "First",
    lastname: "Instructor",
    fullname: "First Instructor",
    email: "first.instructor@exmple.com"
});
storage.users[instructor.id] = instructor;


var course1 = courseFactory.generateCourse("1abcABC123-abcABC123_Z", {
    name: "CHEM 111",
    year: 2015,
    term: "Winter",
    description: "<p>CHEM 111 description<p>",
});
storage.courses[course1.id] = course1;

var course2 = courseFactory.generateCourse("2abcABC123-abcABC123_Z", {
    name: "PHYS 101",
    year: 2015,
    term: "Winter",
    description: "<p>PHYS 101  description<p>",
});
storage.courses[course2.id] = course2;

// user_courses
storage.user_courses[instructor.id] = [
    { courseId: course1.id, courseRole: "Instructor", groupName: null },
    { courseId: course2.id, courseRole: "Instructor", groupName: null }
];

storage.loginDetails = { id: instructor.id, username: instructor.username, password: "password" };
storage.session = sessionFactory.generateSession(instructor.id, instructor.system_role, {
    "Course": {
        "delete": {'1abcABC123-abcABC123_Z': false, '2': false},
        "edit": {'1abcABC123-abcABC123_Z': true, '2': true},
        "manage": {'1abcABC123-abcABC123_Z': false, '2': false},
        "read": {'1abcABC123-abcABC123_Z': true, '2': true}
    },
    "Assignment": {
        "create": {'1abcABC123-abcABC123_Z': true},
        "delete": {'1abcABC123-abcABC123_Z': true},
        "edit": {'1abcABC123-abcABC123_Z': true},
        "manage": {'1abcABC123-abcABC123_Z': true},
        "read": {'1abcABC123-abcABC123_Z': true}
    },
});

module.exports = storage;