var env = require('../env.js');

var EditCourseUserPage = function() {
	this.get = function(courseId) {
		return browser.get(env.baseUrl + '#/course/' + courseId + '/user');
	};
};

module.exports = EditCourseUserPage;
