var env = require('../env.js');

var AssignmentPage = function() {
    var assignmentHeading = element(by.css(".standalone-assignment h2")),
        editAssignemntButton = element(by.cssContainingText(".standalone-assignment a", "Edit"));

    this.get = function(courseId, assignmentId) {
        return browser.get(env.baseUrl + '#/course/' + courseId + '/assignment/' + assignmentId);
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Edit Assignment":
                return editAssignemntButton.click();
        }
    }
};

module.exports = AssignmentPage;
