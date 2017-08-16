var EditCoursePage = function() {
    this.getLocation = function(courseId) {
        return 'course/' + courseId + '/edit';
    };
};

module.exports = EditCoursePage;
