var env = require('../env.js');

describe('homepage before user authenticate', function () {
    beforeEach(function() {
        browser.get(env.baseUrl);
    });

    it('should have a title and login text', function () {
        expect(browser.getTitle()).toEqual('Peer Answer Comparison Tool');
        expect(element(by.id('login-btn')).getText()).toMatch('Log In');
    });

    it('should have internal login form hidden and be able to authenticate user', function() {
        var internalLoginText = element(by.css('form[name=loginForm] fieldset a p'));
        var username =  element(by.model('username'));
        var password =  element(by.model('password'));
        var loginButton = element(by.css('input[value="Log In"]'));

        expect(internalLoginText.getText()).toMatch('Use application\'s login instead?');
        expect(username.isDisplayed()).toBeFalsy();
        expect(password.isDisplayed()).toBeFalsy();

        internalLoginText.click();

        expect(username.isDisplayed()).toBeTruthy();
        expect(password.isDisplayed()).toBeTruthy();

        username.sendKeys('root');
        password.sendKeys('password');

        expect(loginButton.isEnabled()).toBeTruthy();

        loginButton.click();

        var displayName = element(by.binding('loggedInUser.displayname'));
        expect(displayName.getText()).toBe('root');
        expect(internalLoginText.isPresent()).toBeFalsy();

        var logoutButton = element(by.css('#logout-link'));

        displayName.click();
        logoutButton.click();

        expect(internalLoginText.isDisplayed()).toBeTruthy();
    });
});