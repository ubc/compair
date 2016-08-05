var CoursePage = function() {
    this.getLocation = function(courseId) {
        return 'course/' + courseId;
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Add Assignment":
                return element(by.css('#add-assignment-btn')).click();
            case "Edit Course":
                return element(by.css('#edit-course-btn')).click();
            case "Manage Users":
                return element(by.css('#manage-users-btn')).click();
        }
    }
};

module.exports = CoursePage;
