var objectAssign = require('object-assign');
var deepcopy = require('deepcopy');

var comparisonExampleTemplate = {
    "id": null,
    "answer1": null,
    "answer1_id": null,
    "answer2": null,
    "answer2_id": null,
    "assignment_id": null,
    "course_id": null,
    "created": "Wed, 17 Aug 2016 16:38:27 -0000",
    "modified": "Wed, 17 Aug 2016 16:38:27 -0000"
}

function ComparisonExampleFactory() {};

ComparisonExampleFactory.prototype.generateComparisonExample = function (id, course_id, assignment_id, answer1, answer2, parameters) {
    var newComparisonExample = objectAssign({}, comparisonExampleTemplate, parameters);
    newComparisonExample.id = id;
    newComparisonExample.course_id = course_id;
    newComparisonExample.assignment_id = assignment_id;
    newComparisonExample.answer1_id = answer1.id;
    newComparisonExample.answer1 = deepcopy(answer1);
    newComparisonExample.answer2_id = answer2.id;
    newComparisonExample.answer2 = deepcopy(answer2);

    return newComparisonExample;
};

module.exports = ComparisonExampleFactory;
