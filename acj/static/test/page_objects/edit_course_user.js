var EditCourseUserPage = function() {
    this.getLocation = function(courseId) {
        return 'course/' + courseId + '/user';
    };
};

module.exports = EditCourseUserPage;
