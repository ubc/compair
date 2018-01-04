var objectAssign = require('object-assign');
var deepcopy = require('deepcopy');

var assignmentStatusTemplate = {
    "answers": {
        "has_draft": false,
        "draft_ids": [],
        "answered": false,
        "feedback": false,
        "count": 0
    },
    "comparisons": {
        "available": true,
        "has_draft": false,
        "count": 0,
        "left": 3,
        "self_evaluation_draft": false
    }
}

function AssignmentStatusFactory() {};

AssignmentStatusFactory.prototype.generateAssignmentStatus = function (assignmentId, user, parameters) {
    var newAssignmentStatus = {
        "answers": objectAssign({}, assignmentStatusTemplate.answers, parameters.answers),
        "comparisons": objectAssign({}, assignmentStatusTemplate.comparisons, parameters.comparisons)
    };
    newAssignmentStatus.assignment_id = assignmentId;
    newAssignmentStatus.user_id = user.id
    newAssignmentStatus.user = {
        "id": user.id,
        "avatar": user.avatar,
        "displayname": user.displayname
    }

    return newAssignmentStatus;
};

module.exports = AssignmentStatusFactory;
