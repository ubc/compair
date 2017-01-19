var UserCoursesPage = function() {
    this.getLocation = function(userId) {
        return 'users/' + userId + '/course';
    };
};

module.exports = UserCoursesPage;
