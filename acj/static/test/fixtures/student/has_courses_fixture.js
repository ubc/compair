var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory  = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var storage = {
    session: {},
    users: [],
    courses: [],
    course_criteria: {},
    users_and_courses: []
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

var student = userFactory.generateUser(3, "Student", {
    username: "student1",
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    email: "first.student@exmple.com"
});
storage.users.push(student);


var course1 = courseFactory.generateCourse(1, {
    name: "CHEM 111",
    description: "<p>CHEM 111 description<p>",
});
storage.courses.push(course1);

var course2 = courseFactory.generateCourse(1, {
    name: "PHYS 101",
    description: "<p>PHYS 101  description<p>",
});
storage.courses.push(course2);

// users_and_courses
storage.users_and_courses[student.id] = [
    { courseId: course1.id, role: 4 },
    { courseId: course2.id, role: 4 }
];

// course_criteria
storage.course_criteria[course1.id] = [1];
storage.course_criteria[course2.id] = [1];

storage.loginDetails = { id: student.id, username: student.username, password: "password" };
var session = sessionFactory.generateSession(student.id, student.system_role, {
    "Courses": {
        "delete": {'1': false, '2': false},
        "edit": {'1': false, '2': false},
        "manage": {'1': false, '2': false},
        "read": {'1': true, '2': true}
    },
    "PostsForQuestions": {
        "create": {'1': false, '2': false},
        "delete": {'1': false, '2': false},
        "edit": {'1': false, '2': false},
        "manage": {'1': false, '2': false},
        "read": {'1': true, '2': true}
    },
});
storage.session = session;

module.exports = storage;