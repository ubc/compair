var objectAssign = require('object-assign');

var answerTemplate = {
    "id": null,
    "questions_id": null,
    "posts_id": null,
    "user_id": null,
    "user_displayname": null,
    "user_avatar": "8ddf878039b70767c4a5bcf4f0c4f65e",
    "content": null,
    "comments_count": 0,
    "private_comments_count": 0,
    "public_comments_count": 0,
    "files": [],
    "scores": [],
    "flagged": false,
    "created": "Fri, 22 Apr 2016 18:33:34 -0000",
}

function AnswerFactory() {};

AnswerFactory.prototype.generateAnswer = function (id, question_id, user, parameters) {
    var newAnswer = objectAssign({}, answerTemplate, parameters);
    newAnswer.id = id;
    newAnswer.questions_id = question_id;
    newAnswer.user_id = user.id;
    newAnswer.user_displayname = user.displayname;
    newAnswer.user_avatar = user.avatar;

    return newAnswer;
};

module.exports = AnswerFactory;
