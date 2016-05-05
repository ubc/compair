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
    course_criteria: {},
    users_and_courses: [],
    criteria: []
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


var defaultCriteria = criteriaFactory.getDefaultCriteria();
storage.criteria.push(defaultCriteria);

var criteria2 = criteriaFactory.generateCriteria(2, 2, {
    "name": "Which sounds better?", 
    "description": "<p>Choose the response that you think sounds more accurate of the two.</p>",
    "default": true, 
});
storage.criteria.push(criteria2);

var criteria3 = criteriaFactory.generateCriteria(3, 2, {
    "name": "Which looks better?", 
    "description": "<p>Choose the response that you think looks more accurate of the two.</p>",
    "default": false, 
    "judged": false
});
storage.criteria.push(criteria3);

// users_and_courses
storage.users_and_courses[instructor.id] = [
    { courseId: course1.id, role: 2 },
    { courseId: course2.id, role: 2 }
];

// course_criteria
storage.course_criteria[course1.id] = [1,3];
storage.course_criteria[course2.id] = [1];

storage.loginDetails = { id: instructor.id, username: instructor.username, password: "password" };
storage.session = sessionFactory.generateSession(instructor.id, instructor.system_role, {		
    "Courses": {
        "delete": {'1': false, '2': false},
        "edit": {'1': true, '2': true},
        "manage": {'1': false, '2': false},
        "read": {'1': true, '2': true}
    },
    "PostsForQuestions": {
        "create": {'1': true},
        "delete": {'1': true},
        "edit": {'1': true},
        "manage": {'1': true},
        "read": {'1': true}
    },
});

module.exports = storage;