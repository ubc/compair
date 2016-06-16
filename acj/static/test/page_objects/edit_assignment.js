var env = require('../env.js');

var EditAssignmentPage = function() {
	this.get = function(courseId, assignmentId) {
		return browser.get(env.baseUrl + '#/course/' + courseId + '/assignment/' + assignmentId + '/edit');
	};
};

module.exports = EditAssignmentPage;
