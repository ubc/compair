var LoginDialog = function() {
    this.login = function(user) {
        return browser.setLocation('/').then(function() {
            browser.wait(browser.isElementPresent(element(by.id('app-login-toggle'))), 2000);
            element(by.id('app-login-toggle')).click();
            element(by.model('username')).sendKeys(user.username);
            element(by.model('password')).sendKeys(user.password);

            browser.wait(browser.isElementPresent(element(by.css('input[value="Log In"]'))), 2000);
            element(by.css('input[value="Log In"]')).click();

            // wait until login window is hidden
            browser.wait(browser.isElementPresent(element(by.binding('loggedInUser.displayname'))), 2000);
            return element(by.css('body')).click();
        });
    };

    this.logout = function() {
        element(by.binding('loggedInUser.displayname')).click();
        return element(by.css('li[ng-controller=LogoutController] a')).click();
    };
};

module.exports = LoginDialog;
