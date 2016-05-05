var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory  = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var GroupFactory  = require('../../factories/group_factory.js');
var groupFactory = new GroupFactory();

var storage = {
    session: {},
    users: [],
    courses: [],
    users_and_courses: [],
    groups: [],
    user_group: {},
    user_search_results: {}
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

var group1 = groupFactory.generateGroup(1, "First Group");
storage.groups.push(group1);
var group2 = groupFactory.generateGroup(2, "Second Group");
storage.groups.push(group2);
var group3 = groupFactory.generateGroup(3, "Third Group");
storage.groups.push(group2);
storage.user_group[student1.id] = group1.id


// users_and_courses
storage.users_and_courses[instructor.id] = [
    { courseId: course.id, role: 2 }
];

storage.users_and_courses[student1.id] = [
    { courseId: course.id, role: 4 }
];

// user_search_results
storage.user_search_results.objects = [student2];
storage.user_search_results.total = 1;


storage.loginDetails = { id: instructor.id, username: instructor.username, password: "password" };
storage.session = sessionFactory.generateSession(instructor.id, instructor.system_role, {
    "Courses": {
        "delete": {'1': false},
        "edit": {'1': true},
        "manage": {'1': false},
        "read": {'1': true}
    }
});


module.exports = storage;