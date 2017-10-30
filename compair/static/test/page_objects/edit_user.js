var EditUserPage = function() {
    this.getLocation = function(userId) {
        return 'user/' + userId + '/edit';
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Edit Password":
                return element(by.css('#change-password-btn')).click();
        }
    }
};

module.exports = EditUserPage;