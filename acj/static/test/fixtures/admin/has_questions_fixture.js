var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory  = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var QuestionFactory  = require('../../factories/question_factory.js');
var questionFactory = new QuestionFactory();

var CriteriaFactory  = require('../../factories/criteria_factory.js');
var criteriaFactory = new CriteriaFactory();

var storage = {
    session: {},
    users: [],
    courses: [],
    course_criteria: {},
    users_and_courses: [],
    questions: [],
    course_questions: {},
    question_criteria: {},
    criteria: [],
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

var course = courseFactory.generateCourse(1, {
    name: "CHEM 111",
    description: "<p>CHEM 111 description<p>",
});
storage.courses.push(course);


var defaultCriteria = criteriaFactory.getDefaultCriteria();
storage.criteria.push(defaultCriteria);

var criteria2 = criteriaFactory.generateCriteria(2, 1, {
    "name": "Which sounds better?", 
    "description": "<p>Choose the response that you think sounds more accurate of the two.</p>",
    "default": true, 
});
storage.criteria.push(criteria2);


// users_and_courses
storage.users_and_courses[admin.id] = [
    { courseId: course.id, role: 2 }
];

// course_criteria
storage.course_criteria[course.id] = [1,2];

storage.course_questions[course.id] = [];

var question_finished = questionFactory.generateQuestion(1, admin, {
    "title": "Question Finished",
    "can_reply": true, 
    "available": true, 
    "judged": true, 
    "judging_period": false, 
    "after_judging": true, 
    "answer_period": false, 
    "post": {
        "content": "<p>This question should already be completed</p>"
    }, 
});
storage.questions.push(question_finished);
storage.question_criteria[question_finished.id] = [1,2];
storage.course_questions[course.id].push(question_finished.id);

var question_being_judged = questionFactory.generateQuestion(2, admin, {
    "title": "Question Being Judged",
    "can_reply": true, 
    "available": true, 
    "judged": true, 
    "judging_period": true, 
    "after_judging": false, 
    "answer_period": false, 
    "post": {
        "content": "<p>This question should be judged right now</p>"
    }, 
});
storage.questions.push(question_being_judged);
storage.question_criteria[question_being_judged.id] = [1];
storage.course_questions[course.id].push(question_being_judged.id);

var question_being_answered = questionFactory.generateQuestion(3, admin, {
    "title": "Question Being Answered",
    "can_reply": true, 
    "available": true, 
    "judged": false, 
    "judging_period": false, 
    "after_judging": false, 
    "answer_period": true, 
    "post": {
        "content": "<p>This question should be answered right now</p>"
    }, 
});
storage.questions.push(question_being_answered);
storage.question_criteria[question_being_answered.id] = [1];
storage.course_questions[course.id].push(question_being_answered.id);

var question_upcoming = questionFactory.generateQuestion(4, admin, {
    "title": "Question Upcoming",
    "can_reply": true, 
    "available": false, 
    "judged": false, 
    "judging_period": false, 
    "after_judging": false, 
    "answer_period": false, 
    "post": {
        "content": "<p>This question should be coming in the future</p>"
    }, 
});
storage.questions.push(question_upcoming);
storage.question_criteria[question_upcoming.id] = [1];
storage.course_questions[course.id].push(question_upcoming.id);


storage.loginDetails = { id: admin.id, username: admin.username, password: "password" };
var session = sessionFactory.generateSession(admin.id, admin.system_role, {});
storage.session = session;

module.exports = storage;