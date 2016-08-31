var EditCoursePage = function() {
    this.getLocation = function(courseId) {
        return 'course/' + courseId + '/configure';
    };
};

module.exports = EditCoursePage;
