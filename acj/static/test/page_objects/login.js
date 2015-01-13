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

    internalLoginTextElm.click();
    usernameElm.sendKeys(user.username);
    passwordElm.sendKeys(user.password);

    return loginButtonElm.click();
};

LoginDialog.prototype.logout = function() {
    var displayNameElm = element(by.binding('loggedInUser.displayname'));
    var logoutButtonElm = element(by.css('li[ng-controller=LogoutController] a'));

    displayNameElm.click();

    return logoutButtonElm.click();
};

module.exports = LoginDialog;