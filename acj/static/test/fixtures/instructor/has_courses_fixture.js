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
storage.users_and_courses[instructor.id] = [
    { courseId: course1.id, role: 2 },
    { courseId: course2.id, role: 2 }
];

// course_criteria
storage.course_criteria[course1.id] = [1];
storage.course_criteria[course2.id] = [1];

storage.loginDetails = { id: instructor.id, username: instructor.username, password: "password" };
var session = sessionFactory.generateSession(instructor.id, instructor.system_role, {		
    "Courses": {
        "delete": {'1': false, '2': false},
        "edit": {'1': true, '2': true},
        "manage": {'1': false, '2': false},
        "read": {'1': true, '2': true}
    },
    "PostsForQuestions": {
        "create": {'1': true, '2': true},
        "delete": {'1': true, '2': true},
        "edit": {'1': true, '2': true},
        "manage": {'1': true, '2': true},
        "read": {'1': true, '2': true}
    },
});
storage.session = session;

module.exports = storage;