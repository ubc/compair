var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var CourseFactory = require('../../factories/course_factory.js');
var courseFactory = new CourseFactory();

var QuestionFactory = require('../../factories/question_factory.js');
var questionFactory = new QuestionFactory();

var CriteriaFactory = require('../../factories/criteria_factory.js');
var criteriaFactory = new CriteriaFactory();

var AnswerFactory = require('../../factories/answer_factory.js');
var answerFactory = new AnswerFactory();


var storage = {
    session: {},
    users: [],
    courses: [],
    course_criteria: {},
    users_and_courses: [],
    questions: [],
    course_questions: {},
    question_criteria: {},
    answers: [],
    course_answers: {},
    question_answers: {},
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

var student = userFactory.generateUser(3, "Student", {
    username: "student1",
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    email: "first.student@exmple.com"
});
storage.users.push(student);

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
storage.users_and_courses[instructor.id] = [
    { courseId: course.id, role: 2 }
];
storage.users_and_courses[student.id] = [
    { courseId: course.id, role: 4 }
];

// course_criteria
storage.course_criteria[course.id] = [1,2];

storage.course_questions[course.id] = [];
storage.course_answers[course.id] = [];

var question_finished = questionFactory.generateQuestion(1, instructor, {
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

var question_finished_answer = answerFactory.generateAnswer(1, question_finished.id, student, {
    "content": "<p>I finished this question</p>"
})
storage.answers.push(question_finished_answer);
storage.course_answers[course.id].push(question_finished_answer.id);
storage.question_answers[question_finished.id] = [question_finished_answer.id];


var question_being_judged = questionFactory.generateQuestion(2, instructor, {
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

var question_being_judged_answer = answerFactory.generateAnswer(2, question_being_judged.id, student, {
    "content": "<p>I finished this question</p>"
})
storage.answers.push(question_being_judged_answer);
storage.course_answers[course.id].push(question_being_judged_answer.id);
storage.question_answers[question_being_judged.id] = [question_being_judged_answer.id];


var question_being_answered = questionFactory.generateQuestion(3, instructor, {
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

// Note: the server never shows students upcoming questions

storage.loginDetails = { id: student.id, username: student.username, password: "password" };
var session = sessionFactory.generateSession(student.id, student.system_role, {	
    "Courses": {
        "delete": {'1': false},
        "edit": {'1': false},
        "manage": {'1': false},
        "read": {'1': true}
    },
    "PostsForQuestions": {
        "create": {'1': false, '2': false, '3': false, '4': false},
        "delete": {'1': false, '2': false, '3': false, '4': false},
        "edit": {'1': false, '2': false, '3': false, '4': false},
        "manage": {'1': false, '2': false, '3': false, '4': false},
        "read": {'1': true, '2': true, '3': true, '4': true}
    },
});
storage.session = session;

module.exports = storage;