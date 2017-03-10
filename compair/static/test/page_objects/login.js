var LoginDialog = function() {
    this.clearToaster = function() {
        browser.executeScript(function() {
            var injector = angular.element(document).injector();
            var Toaster = injector.get('Toaster');
            if (Toaster) {
                Toaster.clear();
            }
        });
    };

    this.login = function(user) {
        this.clearToaster();
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
        this.clearToaster();
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
        return element(by.css('#logout-link')).click();
    };
};

module.exports = LoginDialog;
