var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory  = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var AssignmentFactory  = require('../../factories/assignment_factory.js');
var assignmentFactory = new AssignmentFactory();

var CriterionFactory  = require('../../factories/criterion_factory.js');
var criterionFactory = new CriterionFactory();

var storage = {
    session: {},
    users: [],
    courses: [],
    user_courses: [],
    assignments: [],
    course_assignments: {},
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

var course = courseFactory.generateCourse(1, {
    name: "CHEM 111",
    year: 2015,
    term: "Winter",
    fullname: "CHEM 111 Winter 2015",
    description: "<p>CHEM 111 description<p>",
});
storage.courses.push(course);


var defaultCriterion = criterionFactory.getDefaultCriterion();
storage.criteria.push(defaultCriterion);

var criterion2 = criterionFactory.generateCriterion(2, admin.id, {
    "name": "Which sounds better?",
    "description": "<p>Choose the response that you think sounds more accurate of the two.</p>",
    "default": true
});
storage.criteria.push(criterion2);

var criterion3 = criterionFactory.generateCriterion(3, admin.id, {
    "name": "Which looks better?",
    "description": "<p>Choose the response that you think looks more accurate of the two.</p>",
    "default": false,
    "compared": true
});
storage.criteria.push(criterion3);


// user_courses
storage.user_courses[admin.id] = [
    { courseId: course.id, courseRole: "Instructor", groupName: null }
];

storage.course_assignments[course.id] = [];

var assignment_finished = assignmentFactory.generateAssignment(1, admin, [defaultCriterion, criterion3], {
    "name": "Assignment Finished",
    "students_can_reply": true,
    "available": true,
    "compared": true,
    "compare_period": false,
    "after_comparing": true,
    "answer_period": false,
    "content": "<p>This assignment should already be completed</p>"
});
storage.assignments.push(assignment_finished);
storage.course_assignments[course.id].push(assignment_finished.id);

var assignment_being_compared = assignmentFactory.generateAssignment(2, admin, [defaultCriterion, criterion3], {
    "name": "Assignment Being Compared",
    "students_can_reply": true,
    "available": true,
    "compared": true,
    "compare_period": true,
    "after_comparing": false,
    "answer_period": false,
    "content": "<p>This assignment should be compared right now</p>"
});
storage.assignments.push(assignment_being_compared);
storage.course_assignments[course.id].push(assignment_being_compared.id);

var assignment_being_answered = assignmentFactory.generateAssignment(3, admin, [defaultCriterion, criterion3], {
    "name": "Assignment Being Answered",
    "students_can_reply": true,
    "available": true,
    "compared": false,
    "compare_period": false,
    "after_comparing": false,
    "answer_period": true,
    "content": "<p>This assignment should be answered right now</p>"
});
storage.assignments.push(assignment_being_answered);
storage.course_assignments[course.id].push(assignment_being_answered.id);

var assignment_upcoming = assignmentFactory.generateAssignment(4, admin, [defaultCriterion, criterion3], {
    "name": "Assignment Upcoming",
    "students_can_reply": true,
    "available": false,
    "compared": false,
    "compare_period": false,
    "after_comparing": false,
    "answer_period": false,
    "content": "<p>This assignment should be coming in the future</p>"
});
storage.assignments.push(assignment_upcoming);
storage.course_assignments[course.id].push(assignment_upcoming.id);


storage.loginDetails = { id: admin.id, username: admin.username, password: "password" };
var session = sessionFactory.generateSession(admin.id, admin.system_role, {});
storage.session = session;

module.exports = storage;