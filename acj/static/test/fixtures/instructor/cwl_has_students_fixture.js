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
    user_courses: {},
    groups: [],
    user_search_results: {}
}

var admin = userFactory.generateUser("1abcABC123-abcABC123_Z", "System Administrator", {
    displayname: "root",
    firstname: "JaNy",
    lastname: "bwsV",
    fullname: "JaNy bwsV",
    uses_acj_login: false
});
storage.users[admin.id] = admin;

var instructor = userFactory.generateUser("2abcABC123-abcABC123_Z", "Instructor", {
    displayname: "First Instructor",
    firstname: "First",
    lastname: "Instructor",
    fullname: "First Instructor",
    email: "first.instructor@exmple.com",
    uses_acj_login: false
});
storage.users[instructor.id] = instructor;

var student1 = userFactory.generateUser("3abcABC123-abcABC123_Z", "Student", {
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    email: "first.student@exmple.com",
    uses_acj_login: false
});
storage.users[student1.id] = student1;

var student2 = userFactory.generateUser("4abcABC123-abcABC123_Z", "Student", {
    displayname: "Second Student",
    firstname: "Second",
    lastname: "Student",
    fullname: "Second Student",
    email: "second.student@exmple.com",
    uses_acj_login: false
});
storage.users[student2.id] = student2;


var course = courseFactory.generateCourse("1abcABC123-abcABC123_Z", {
    name: "CHEM 111",
    year: 2015,
    term: "Winter",
    description: "<p>CHEM 111 description<p>",
});
storage.courses[course.id] = course;

var group1 = "First Group";
storage.groups.push(group1);
var group2 = "Second Group";
storage.groups.push(group2);
var group3 = "Third Group";
storage.groups.push(group3);


// user_courses
storage.user_courses[instructor.id] = [
    { courseId: course.id, courseRole: "Instructor", groupName: null }
];

storage.user_courses[student1.id] = [
    { courseId: course.id, courseRole: "Student", groupName: group1 }
];

// user_search_results
storage.user_search_results.objects = [student2];
storage.user_search_results.total = 1;


storage.loginDetails = { id: instructor.id };
storage.session = sessionFactory.generateSession(instructor.id, instructor.system_role, {
    "Course": {
        "delete": {'1abcABC123-abcABC123_Z': false},
        "edit": {'1abcABC123-abcABC123_Z': true},
        "manage": {'1abcABC123-abcABC123_Z': false},
        "read": {'1abcABC123-abcABC123_Z': true}
    }
});


module.exports = storage;