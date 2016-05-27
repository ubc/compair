var env = require('../env.js');


var HomePage = function() {
    var addCourseButton = element(by.css('#create-course-btn')),
        downloadReportButton = element(by.css('#download-report-btn')),
        createUserButton = element(by.css('#create-user-btn')),
        menuDropdownButton = element(by.css('#menu-dropdown')),
        profileButton = element(by.css('#own-profile-link'));

    this.get = function() {
        return browser.get(env.baseUrl+'#/');
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Add Course":
                return addCourseButton.click();
            case "Create User":
                return createUserButton.click();
            case "Profile":
                menuDropdownButton.click();
                return profileButton.click();
        }
    }
};

module.exports = HomePage;
