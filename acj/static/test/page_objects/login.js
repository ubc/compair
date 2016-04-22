var env = require('../env.js');

var LoginDialog = function() {
};

LoginDialog.prototype.get = function() {
    return browser.get(env.baseUrl);
};

LoginDialog.prototype.login = function(user) {
    var internalLoginTextElm = element(by.id('app-login-toggle'));
    var usernameElm =  element(by.model('username'));
    var passwordElm =  element(by.model('password'));
    var loginButtonElm = element(by.css('input[value="Log In"]'));

    browser.wait(internalLoginTextElm.isPresent(), 1000);
    internalLoginTextElm.click();
    usernameElm.sendKeys(user.username);
    passwordElm.sendKeys(user.password);
    
    loginButtonElm.click();

    return browser.wait(browser.isElementPresent(element(by.binding('loggedInUser.displayname'))), 5000);
};

LoginDialog.prototype.logout = function() {
    var displayNameElm = element(by.binding('loggedInUser.displayname'));
    var logoutButtonElm = element(by.css('li[ng-controller=LogoutController] a'));

    displayNameElm.click();

    return logoutButtonElm.click();
};

module.exports = LoginDialog;