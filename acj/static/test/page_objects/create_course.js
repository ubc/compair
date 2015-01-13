var env = require('../env.js');


var CreateCoursePage = function() {
    var addCourseButton = element(by.css('#create-course-btn')),
        downloadReportButton =  element(by.css('#download-report-btn')),
        createUserButton =  element(by.css('#create-user-btn'));

    this.get = function() {
        return browser.get(env.baseUrl + '#/course/new');
    };

    this.addCourse = function() {
        return addCourseButton.click();
    };
};

module.exports = CreateCoursePage;
