var UserPage = function() {
    this.getLocation = function(userId) {
        return 'user/' + userId;
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Edit":
                return element(by.css('#edit-profile-btn')).click();
        }
    }
};

module.exports = UserPage;
