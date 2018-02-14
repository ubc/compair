var UserManagePage = function() {
    this.getLocation = function(userId) {
        return 'users/' + userId + '/manage';
    };
};

module.exports = UserManagePage;
