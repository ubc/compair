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

var student = userFactory.generateUser("3abcABC123-abcABC123_Z", "Student", {
    username: "student1",
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    email: "first.student@exmple.com"
});
storage.users[student.id] = student;


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
storage.user_courses[student.id] = [
    { courseId: course1.id, courseRole: "Student", groupName: null },
    { courseId: course2.id, courseRole: "Student", groupName: null }
];

storage.loginDetails = { id: student.id, username: student.username, password: "password" };
storage.session = sessionFactory.generateSession(student.id, student.system_role, {
    "Course": {
        "delete": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false},
        "edit": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false},
        "manage": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false},
        "read": {'1abcABC123-abcABC123_Z': true, '2abcABC123-abcABC123_Z': true}
    },
    "Assignment": {
        "create": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false},
        "delete": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false},
        "edit": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false},
        "manage": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false},
        "read": {'1abcABC123-abcABC123_Z': true, '2abcABC123-abcABC123_Z': true}
    },
});

module.exports = storage;