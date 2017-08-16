var HomePage = function() {
    this.getLocation = function() {
        return '/';
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Add Course":
                return element(by.css('#create-course-btn')).click();
            case "Create Account":
                return element(by.css('#create-user-btn')).click();
            case "Manage Users":
                return element(by.css('#view-users-btn')).click();
            case "Manage LTI":
                return element(by.css('#manage-lti-consumers-btn')).click();
            case "Profile":
                element(by.css('#menu-dropdown')).click();
                return element(by.css('#own-profile-link')).click();
        }
    }
};

module.exports = HomePage;
