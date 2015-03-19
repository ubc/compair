var env = require('../env.js');

var CoursePage = function() {
	var addAssignmentButton = element(by.css('#add-question-btn'));

	this.get = function(courseId) {
		return browser.get(env.baseUrl + '#/course/' + courseId);
	};

	this.addAssignment = function() {
		return addAssignmentButton.click();
	};
};

module.exports = CoursePage;
