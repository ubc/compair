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
    users_and_courses: [],
    userTypes: [
        { "id": 1, "name": "Student" }, 
        { "id": 2, "name": "Instructor" }, 
        { "id": 3, "name": "System Administrator"  }
    ]
}

var admin = userFactory.generateUser(1, "System Administrator", {
    username: "root",
    displayname: "root",
    firstname: "JaNy",
    lastname: "bwsV",
    fullname: "JaNy bwsV",
});
storage.users.push(admin);

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
storage.users_and_courses[admin.id] = [
    { courseId: course1.id, role: 2 },
    { courseId: course2.id, role: 2 }
];

// course_criteria
storage.course_criteria[course1.id] = [1];
storage.course_criteria[course2.id] = [1];


storage.loginDetails = { id: admin.id, username: admin.username, password: "password" };
storage.session = sessionFactory.generateSession(admin.id, admin.system_role, {});

module.exports = storage;