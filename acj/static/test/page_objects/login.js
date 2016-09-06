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

    this.skipLogin = function() {
        return browser.setLocation('/').then(function() {
            return browser.executeScript(function(fixtureName) {
                var injector = angular.element(document).injector()

                var storageFixture = injector.get('storageFixture');
                var AuthenticationService = injector.get('AuthenticationService');
                var $route = injector.get('$route');

                storageFixture.storage().authenticated = true;
                AuthenticationService.login();
                $route.reload();
            });
        });
    };

    this.logout = function() {
        element(by.binding('loggedInUser.displayname')).click();
        return element(by.css('li[ng-controller=LogoutController] a')).click();
    };
};

module.exports = LoginDialog;
