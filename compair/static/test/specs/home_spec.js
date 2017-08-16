var env = require('../env.js');
var loginDialog = require('../page_objects/login.js');

describe('home', function() {
    beforeEach(function() {
        loginDialog.login();
    });

    afterEach(function() {
        loginDialog.logout();
    });

    it('should show the home page ', function() {
        expect(element(by.css('div.home-screen h2')).getText()).toMatch('Select a course');

    });

    it('should not list course when no course available', function() {
        expect(element(by.css('div.home-screen div p')).getText()).toMatch('No courses currently available.');
        addCourseButton = element(by.css('#create-course-btn'));
    });
});