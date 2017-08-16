var AssignmentPage = function() {
    this.getLocation = function(courseId, assignmentId) {
        return 'course/' + courseId + '/assignment/' + assignmentId;
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Edit Assignment":
                return element(by.cssContainingText(".assignment-screen a", "Edit Assignment")).click();
        }
    }
};

module.exports = AssignmentPage;
