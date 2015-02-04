var env = require('../env.js');

var CoursePage = function() {
	var addQuestionButton = element(by.css('#add-question-btn'));

	this.get = function(courseId) {
		return browser.get(env.baseUrl + '#/course/' + courseId);
	};

	this.addQuestion = function() {
		return addQuestionButton.click();
	};
};

module.exports = CoursePage;