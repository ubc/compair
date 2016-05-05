var env = require('../env.js');

var EditCoursePage = function() {
    this.get = function(courseId) {
        return browser.get(env.baseUrl + '#/course/' + courseId + '/configure');
    };
};

module.exports = EditCoursePage;
