var objectAssign = require('object-assign');

var questionTemplate = {
    "id": null, 
    "title": null,
    "criteria": [], 
    "can_reply": true, 
    "available": false, 
    "judged": false, 
    "judging_period": false, 
    "after_judging": false, 
    "selfevaltype_id": 0, 
    "comments_count": 0, 
    "evaluation_count": 0, 
    "answers_count": 0,
    "answer_period": false, 
    "answer_end": "Thu, 28 Apr 2016 06:59:00 -0000", 
    "answer_start": "Wed, 20 Apr 2016 07:00:00 -0000", 
    "num_judgement_req": 3, 
    "judge_end": null, 
    "judge_start": null, 
    "modified": "Tue, 19 Apr 2016 20:06:43 -0000", 
    "post": {}, 
}

var postTempalte = {
    'id': null,
    "content": "",
    "files": [],
    'user': {},
    "created": "Fri, 06 Feb 2015 22:12:59 -0000",
    'modified': "Fri, 06 Feb 2015 22:12:59 -0000",
}

var userTempalte = {
    "id": null,
    "displayname": null,
    "avatar": "b47d5e296b954b96c12fe3b5ced166b4",
    "created": "Sun, 11 Jan 2015 07:59:17 -0000",
    "lastonline": "Sun, 11 Jan 2015 08:25:08 -0000",
}

function QuestionFactory() {};

QuestionFactory.prototype.generateQuestion = function (id, user, parameters) {
    var newQuestion = objectAssign({}, questionTemplate, parameters);
    newQuestion.id = id;
    
    newQuestion.post = objectAssign({}, postTempalte, parameters.post);
    newQuestion.post.user = objectAssign({}, user);
    
    return newQuestion;
};

module.exports = QuestionFactory;
