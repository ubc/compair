var CreateAssignmentPage = function() {
    this.getLocation = function(courseId) {
        return 'course/' + courseId + '/assignment/create';
    };
};

module.exports = CreateAssignmentPage;