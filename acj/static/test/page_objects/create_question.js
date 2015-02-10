var env = require('../env.js');

var CreateQuestionPage = function() {
	this.get = function(courseId) {
		return browser.get(env.baseUrl + '#/course/' + courseId + '/question/create')
	};
};

module.exports = CreateQuestionPage;