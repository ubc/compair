var env = require('../env.js');

var EditUserPage = function() {
	this.get = function(userId) {
		return browser.get(env.baseUrl + '#/user/' + userId + '/edit');
	};
};

module.exports = EditUserPage;