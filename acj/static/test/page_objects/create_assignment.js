var env = require('../env.js');

var CreateAssignmentPage = function() {
	this.get = function(courseId) {
		return browser.get(env.baseUrl + '#/course/' + courseId + '/assignment/create')
	};
};

module.exports = CreateAssignmentPage;