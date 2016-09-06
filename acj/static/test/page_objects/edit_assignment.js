var EditAssignmentPage = function() {
    this.getLocation = function(courseId, assignmentId) {
        return 'course/' + courseId + '/assignment/' + assignmentId + '/edit';
    };
};

module.exports = EditAssignmentPage;
