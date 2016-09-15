var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var AssignmentFactory = require('../../factories/assignment_factory.js');
var assignmentFactory = new AssignmentFactory();

var CriterionFactory = require('../../factories/criterion_factory.js');
var criterionFactory = new CriterionFactory();

var AnswerFactory = require('../../factories/answer_factory.js');
var answerFactory = new AnswerFactory();


var storage = {
    session: {},
    users: {},
    courses: {},
    user_courses: {},
    assignments: {},
    course_assignments: {},
    answers: {},
    course_answers: {},
    assignment_answers: {},
    criteria: {}
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

var course = courseFactory.generateCourse("1abcABC123-abcABC123_Z", {
    name: "CHEM 111",
    year: 2015,
    term: "Winter",
    description: "<p>CHEM 111 description<p>",
});
storage.courses[course.id] = course;


var defaultCriterion = criterionFactory.getDefaultCriterion();
storage.criteria[defaultCriterion.id] = defaultCriterion;

var criterion2 = criterionFactory.generateCriterion("2abcABC123-abcABC123_Z", instructor.id, {
    "name": "Which sounds better?",
    "description": "<p>Choose the response that you think sounds more accurate of the two.</p>",
    "default": true,
});
storage.criteria[criterion2.id] = criterion2;

var criterion3 = criterionFactory.generateCriterion("3abcABC123-abcABC123_Z", instructor.id, {
    "name": "Which looks better?",
    "description": "<p>Choose the response that you think looks more accurate of the two.</p>",
    "default": false,
    "compared": true
});
storage.criteria[criterion3.id] = criterion3;


// user_courses
storage.user_courses[instructor.id] = [
    { courseId: course.id, courseRole: "Instructor", groupName: null }
];
storage.user_courses[student.id] = [
    { courseId: course.id, courseRole: "Student", groupName: null }
];

storage.course_assignments[course.id] = [];
storage.course_answers[course.id] = [];

var assignment_finished = assignmentFactory.generateAssignment("1abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment Finished",
    "students_can_reply": true,
    "available": true,
    "compared": true,
    "compare_period": false,
    "after_comparing": true,
    "answer_period": false,
    "content": "<p>This assignment should already be completed</p>"
});
storage.assignments[assignment_finished.id] = assignment_finished;
storage.course_assignments[course.id].push(assignment_finished.id);

var assignment_finished_answer = answerFactory.generateAnswer("1abcABC123-abcABC123_Z", assignment_finished.id, student, {
    "content": "<p>I finished this assignment</p>"
})
storage.answers[assignment_finished_answer.id] = assignment_finished_answer;
storage.course_answers[course.id].push(assignment_finished_answer.id);
storage.assignment_answers[assignment_finished.id] = [assignment_finished_answer.id];


var assignment_being_compared = assignmentFactory.generateAssignment("2abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment Being Compared",
    "students_can_reply": true,
    "available": true,
    "compared": true,
    "compare_period": true,
    "after_comparing": false,
    "answer_period": false,
    "content": "<p>This assignment should be compared right now</p>"
});
storage.assignments[assignment_being_compared.id] = assignment_being_compared;
storage.course_assignments[course.id].push(assignment_being_compared.id);

var assignment_being_compared_answer = answerFactory.generateAnswer("2abcABC123-abcABC123_Z", assignment_being_compared.id, student, {
    "content": "<p>I finished this assignment</p>"
})
storage.answers[assignment_being_compared_answer.id] = assignment_being_compared_answer;
storage.course_answers[course.id].push(assignment_being_compared_answer.id);
storage.assignment_answers[assignment_being_compared.id] = [assignment_being_compared_answer.id];


var assignment_being_answered = assignmentFactory.generateAssignment("3abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment Being Answered",
    "students_can_reply": true,
    "available": true,
    "compared": false,
    "compare_period": false,
    "after_comparing": false,
    "answer_period": true,
    "content": "<p>This assignment should be answered right now</p>"
});
storage.assignments[assignment_being_answered.id] = assignment_being_answered;
storage.course_assignments[course.id].push(assignment_being_answered.id);

// Note: the server never shows students upcoming assignments

storage.loginDetails = { id: student.id, username: student.username, password: "password" };
var session = sessionFactory.generateSession(student.id, student.system_role, {
    "Course": {
        "delete": {'1abcABC123-abcABC123_Z': false},
        "edit": {'1abcABC123-abcABC123_Z': false},
        "manage": {'1abcABC123-abcABC123_Z': false},
        "read": {'1abcABC123-abcABC123_Z': true}
    },
    "Assignment": {
        "create": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false, '3abcABC123-abcABC123_Z': false, '4abcABC123-abcABC123_Z': false},
        "delete": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false, '3abcABC123-abcABC123_Z': false, '4abcABC123-abcABC123_Z': false},
        "edit": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false, '3abcABC123-abcABC123_Z': false, '4abcABC123-abcABC123_Z': false},
        "manage": {'1abcABC123-abcABC123_Z': false, '2abcABC123-abcABC123_Z': false, '3abcABC123-abcABC123_Z': false, '4abcABC123-abcABC123_Z': false},
        "read": {'1abcABC123-abcABC123_Z': true, '2abcABC123-abcABC123_Z': true, '3abcABC123-abcABC123_Z': true, '4abcABC123-abcABC123_Z': true}
    },
});
storage.session = session;

module.exports = storage;