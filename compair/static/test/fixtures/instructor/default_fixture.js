var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory  = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var AssignmentFactory  = require('../../factories/assignment_factory.js');
var assignmentFactory = new AssignmentFactory();

var AssignmentStatusFactory = require('../../factories/assignment_status_factory.js');
var assignmentStatusFactory = new AssignmentStatusFactory();

var CriterionFactory  = require('../../factories/criterion_factory.js');
var criterionFactory = new CriterionFactory();

var GroupFactory = require('../../factories/group_factory.js');
var groupFactory = new GroupFactory();

var storage = {
    session: {},
    users: {},
    courses: {},
    user_courses: {},
    groups: {},
    assignments: {},
    assignment_status: {},
    course_assignments: {},
    criteria: {}
}

var admin = userFactory.generateUser("1abcABC123-abcABC123_Z", "System Administrator", {
    username: "root",
    displayname: "root",
    firstname: "JaNy",
    lastname: "bwsV",
    fullname: "JaNy bwsV",
    fullname_sortable: "bwsV, JaNy",
    email: "admin@exmple.com"
});
storage.users[admin.id] = admin;

var instructor = userFactory.generateUser("2abcABC123-abcABC123_Z", "Instructor", {
    username: "instructor1",
    displayname: "First Instructor",
    firstname: "First",
    lastname: "Instructor",
    fullname: "First Instructor",
    fullname_sortable: "Instructor, First",
    email: "first.instructor@exmple.com"
});
storage.users[instructor.id] = instructor;

var student1 = userFactory.generateUser("3abcABC123-abcABC123_Z", "Student", {
    username: "student1",
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    fullname_sortable: "Student, First (12345678)",
    student_number: "12345678",
    email: "first.student@exmple.com"
});
storage.users[student1.id] = student1;

var student2 = userFactory.generateUser("4abcABC123-abcABC123_Z", "Student", {
    username: "student2",
    displayname: "Second Student",
    firstname: "Second",
    lastname: "Student",
    fullname: "Second Student",
    fullname_sortable: "Student, Second (123456789)",
    student_number: "123456789",
    email: "second.student@exmple.com"
});
storage.users[student2.id] = student2;

var course = courseFactory.generateCourse("1abcABC123-abcABC123_Z", {
    name: "CHEM 111",
    year: 2015,
    term: "Winter",
    start_date: "2015-01-02T23:00:00"
});
storage.courses[course.id] = course;

var course2 = courseFactory.generateCourse("2abcABC123-abcABC123_Z", {
    name: "PHYS 101",
    year: 2015,
    term: "Winter",
    start_date: "2015-01-02T23:00:00"
});
storage.courses[course2.id] = course2;

var group1 = groupFactory.generateGroup("1abcABC123-abcABC123_Z", course.id, {
    name: "First Group",
});
storage.groups[group1.id] = group1;

var group2 = groupFactory.generateGroup("2abcABC123-abcABC123_Z", course.id, {
    name: "Second Group",
});
storage.groups[group2.id] = group2;

var group3 = groupFactory.generateGroup("3abcABC123-abcABC123_Z", course.id, {
    name: "Second Group",
});
storage.groups[group3.id] = group2;

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
    { courseId: course.id, courseRole: "Instructor", group_id: null },
    { courseId: course2.id, courseRole: "Instructor", group_id: null }
];

storage.user_courses[student1.id] = [
    { courseId: course.id, courseRole: "Student", group_id: group1.id }
];

storage.course_assignments[course.id] = [];

var todayPlusDays = function(days) {
    var todayDate = new Date();
    todayDate.setDate(todayDate.getDate() + days);
    return todayDate.toUTCString();
}

var assignment_with_feedback = assignmentFactory.generateAssignment("1abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment With Feedback",
    "students_can_reply": true,
    "available": true,
    "compared": true,
    "compare_period": false,
    "after_comparing": true,
    "answer_period": false,
    "answer_start": todayPlusDays(-10),
    "answer_end": todayPlusDays(-5),
    "content": "<p>This assignment should already be completed and have feedback</p>"
});
storage.assignments[assignment_with_feedback.id] = assignment_with_feedback;
storage.course_assignments[course.id].push(assignment_with_feedback.id);

var assignment_with_feedback_status = assignmentStatusFactory.generateAssignmentStatus(assignment_with_feedback.id, student1, {
    "answers": {
        "answered": true,
        "feedback": true,
    }
});
storage.assignment_status[assignment_with_feedback.id] = assignment_with_feedback_status;

var assignment_finished = assignmentFactory.generateAssignment("2abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment Finished",
    "students_can_reply": true,
    "available": true,
    "compared": true,
    "compare_period": false,
    "after_comparing": true,
    "answer_period": false,
    "answer_start": todayPlusDays(-9),
    "answer_end": todayPlusDays(11),
    "compare_start": todayPlusDays(-5),
    "compare_end": todayPlusDays(15),
    "content": "<p>This assignment should already be completed</p>"
});
storage.assignments[assignment_finished.id] = assignment_finished;
storage.course_assignments[course.id].push(assignment_finished.id);
storage.assignment_status[assignment_finished.id] = assignmentStatusFactory.generateAssignmentStatus(assignment_finished.id, instructor, {});

var assignment_being_compared = assignmentFactory.generateAssignment("3abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment Being Compared",
    "students_can_reply": true,
    "available": true,
    "compared": true,
    "compare_period": true,
    "after_comparing": false,
    "answer_period": false,
    "answer_start": todayPlusDays(-8),
    "answer_end": todayPlusDays(12),
    "compare_start": todayPlusDays(-5),
    "compare_end": todayPlusDays(16),
    "content": "<p>This assignment should be compared right now</p>"
});
storage.assignments[assignment_being_compared.id] = assignment_being_compared;
storage.course_assignments[course.id].push(assignment_being_compared.id);
storage.assignment_status[assignment_being_compared.id] = assignmentStatusFactory.generateAssignmentStatus(assignment_being_compared.id, instructor, {});

var assignment_with_draft_answer = assignmentFactory.generateAssignment("4abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment With Draft Answer",
    "students_can_reply": true,
    "available": true,
    "compared": false,
    "compare_period": false,
    "after_comparing": false,
    "answer_period": true,
    "answer_start": todayPlusDays(-7),
    "answer_end": todayPlusDays(14),
    "content": "<p>This assignment should be answered right now and has a draft saved</p>"
});
storage.assignments[assignment_with_draft_answer.id] = assignment_with_draft_answer;
storage.course_assignments[course.id].push(assignment_with_draft_answer.id);

var assignment_with_draft_answer_status = assignmentStatusFactory.generateAssignmentStatus(assignment_with_draft_answer.id, student1, {
    "answers": {
        "has_draft": true,
        "draft_ids": [0]
    }
});
storage.assignment_status[assignment_with_draft_answer.id] = assignment_with_draft_answer_status;

var assignment_being_answered = assignmentFactory.generateAssignment("5abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment Being Answered",
    "students_can_reply": true,
    "available": true,
    "compared": false,
    "compare_period": false,
    "after_comparing": false,
    "answer_period": true,
    "answer_start": todayPlusDays(-6),
    "answer_end": todayPlusDays(13),
    "compare_start": todayPlusDays(-5),
    "compare_end": todayPlusDays(17),
    "content": "<p>This assignment should be answered right now</p>"
});
storage.assignments[assignment_being_answered.id] = assignment_being_answered;
storage.course_assignments[course.id].push(assignment_being_answered.id);
storage.assignment_status[assignment_being_answered.id] = assignmentStatusFactory.generateAssignmentStatus(assignment_being_answered.id, instructor, {});

var assignment_upcoming = assignmentFactory.generateAssignment("6abcABC123-abcABC123_Z", instructor, [defaultCriterion, criterion3], {
    "name": "Assignment Upcoming",
    "students_can_reply": true,
    "available": false,
    "compared": false,
    "compare_period": false,
    "after_comparing": false,
    "answer_period": false,
    "answer_start": todayPlusDays(10),
    "answer_end": todayPlusDays(20),
    "content": "<p>This assignment should be coming in the future</p>"
});
storage.assignments[assignment_upcoming.id] = assignment_upcoming;
storage.course_assignments[course.id].push(assignment_upcoming.id);
storage.assignment_status[assignment_upcoming.id] = assignmentStatusFactory.generateAssignmentStatus(assignment_upcoming.id, instructor, {});

storage.loginDetails = { id: instructor.id, username: instructor.username, password: "password" };
var session = sessionFactory.generateSession(instructor, {
    "Course": {
        "1abcABC123-abcABC123_Z": [
            "delete",
            "edit",
            "read"
        ],
        "2abcABC123-abcABC123_Z": [
            "delete",
            "edit",
            "read"
        ]
    },
    "Assignment": {
        "1abcABC123-abcABC123_Z": [
            "create",
            "delete",
            "edit",
            "manage",
            "read"
        ],
        "2abcABC123-abcABC123_Z": [
            "create",
            "delete",
            "edit",
            "manage",
            "read"
        ]
    }
});
storage.session = session;

module.exports = storage;