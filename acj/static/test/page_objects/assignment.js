var AssignmentPage = function() {
    this.getLocation = function(courseId, assignmentId) {
        return 'course/' + courseId + '/assignment/' + assignmentId;
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Edit Assignment":
                return element(by.cssContainingText(".standalone-assignment a", "Edit")).click();
        }
    }
};

module.exports = AssignmentPage;
