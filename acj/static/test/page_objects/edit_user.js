var EditUserPage = function() {
    this.getLocation = function(userId) {
        return 'user/' + userId + '/edit';
    };
};

module.exports = EditUserPage;