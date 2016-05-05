var env = require('../env.js');

var CoursePage = function() {
	var addAssignmentButton = element(by.css('#add-question-btn')),
        editCoruseButton = element(by.css('#edit-course-btn')),
        manageUsersButton = element(by.css('#manage-users-btn'));

	this.get = function(courseId) {
		return browser.get(env.baseUrl + '#/course/' + courseId);
	};
    
    this.clickButton = function(button) {
        switch (button) {
            case "Add Assignment":
                return addAssignmentButton.click();
            case "Edit Course":
                return editCoruseButton.click();
            case "Manage Users":
                return manageUsersButton.click();
        }
    }
};

module.exports = CoursePage;
