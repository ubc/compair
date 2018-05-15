var objectAssign = require('object-assign');
var deepcopy = require('deepcopy');

var assignmentTemplate = {
    "id": null,
    "name": null,
    "criteria": [],
    "students_can_reply": true,
    "available": false,
    "compared": false,
    "compare_period": false,
    "after_comparing": false,
    "enable_self_evaluation": false,
    "enable_group_answers": false,
    "pairing_algorithm": "random",
    "educators_can_compare": false,
    "rank_display_limit": 10,
    "evaluation_count": 0,
    "answer_count": 0,
    "self_evaluation_count": 0,
    "answer_grade_weight": 1,
    "comparison_grade_weight": 1,
    "self_evaluation_grade_weight": 1,
    "answer_period": false,
    "answer_end": "Thu, 28 Apr 2016 06:59:00 -0000",
    "answer_start": "Wed, 20 Apr 2016 07:00:00 -0000",
    "number_of_comparisons": 3,
    "total_comparisons_required": 3,
    "total_steps_required": 3,
    "compare_end": null,
    "compare_start": null,
    "self_eval_end": null,
    "self_eval_start": null,
    "peer_feedback_prompt": null,
    "self_eval_start": null,
    "self_eval_end": null,
    "self_eval_instructions": null,
    "created": "Tue, 19 Apr 2016 20:06:43 -0000",
    "modified": "Tue, 19 Apr 2016 20:06:43 -0000",
    "user": {
        "id": null,
        "avatar": "8ddf878039b70767c4a5bcf4f0c4f65e",
        "displayname": null
    }
}

function AssignmentFactory() {};

AssignmentFactory.prototype.generateAssignment = function (id, user, criteria, parameters) {
    var newAssignment = objectAssign({}, assignmentTemplate, parameters);
    newAssignment.id = id;
    newAssignment.user_id = user.id
    newAssignment.user = {
        "id": user.id,
        "avatar": user.avatar,
        "displayname": user.displayname
    }
    newAssignment.criteria = [];

    for(var index = 0; index < criteria.length; index++) {
        newAssignment.criteria.push(deepcopy(criteria[index]));
    }

    return newAssignment;
};

module.exports = AssignmentFactory;
