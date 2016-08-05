var HomePage = function() {
    this.getLocation = function() {
        return '/';
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Add Course":
                return element(by.css('#create-course-btn')).click();
            case "Create User":
                return element(by.css('#create-user-btn')).click();
            case "Profile":
                element(by.css('#menu-dropdown')).click();
                return element(by.css('#own-profile-link')).click();
        }
    }
};

module.exports = HomePage;
