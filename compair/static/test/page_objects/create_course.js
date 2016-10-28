var CreateCoursePage = function() {
    this.getLocation = function() {
        return 'course/new';
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Add Course":
                return element(by.css('#create-course-btn')).click();
            case "Download Report":
                return element(by.css('#download-report-btn')).click();
            case "Create Account":
                return element(by.css('#create-user-btn')).click();
        }
    }
};

module.exports = CreateCoursePage;
