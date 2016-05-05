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

var student1 = userFactory.generateUser(3, "Student", {
    username: "student1",
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    email: "first.student@exmple.com"
});
storage.users.push(student1);

var student2 = userFactory.generateUser(4, "Student", {
    username: "student2",
    displayname: "Second Student",
    firstname: "Second",
    lastname: "Student",
    fullname: "Second Student",
    email: "second.student@exmple.com"
});
storage.users.push(student2);


var course = courseFactory.generateCourse(1, {
    name: "CHEM 111",
    description: "<p>CHEM 111 description<p>",
});
storage.courses.push(course);

// users_and_courses
storage.users_and_courses[instructor.id] = [
    { courseId: course.id, role: 2 }
];

storage.users_and_courses[student1.id] = [
    { courseId: course.id, role: 4 }
];


storage.loginDetails = { id: instructor.id, username: instructor.username, password: "password" };
var session = sessionFactory.generateSession(instructor.id, instructor.system_role, {
    "Courses": {
        "delete": {'1': false},
        "edit": {'1': true},
        "manage": {'1': false},
        "read": {'1': true}
    }
});
storage.session = session;


module.exports = storage;