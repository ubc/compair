var env = require('../env.js');

var UserPage = function() {
    var editUserButton = element(by.css('#edit-profile-btn'));

	this.get = function(userId) {
		return browser.get(env.baseUrl + '#/user/' + userId);
	};

    this.clickButton = function(button) {
        switch (button) {
            case "Edit":
                return editUserButton.click();
        }
    }
};

module.exports = UserPage;
