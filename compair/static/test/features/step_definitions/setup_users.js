// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var PageFactory  = require('../../factories/page_factory.js');
var backEndMocks = require('../../factories/http_backend_mocks.js');

var setupAdminStepDefinitionsWrapper = function () {
    var pageFactory = new PageFactory();
    var loginDialog = pageFactory.createPage('login');

    this.Given("I'm a System Administrator", {timeout: 20 * 1000}, function () {
        var fixtureName = 'admin/default_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.login(backEndMocks.getLoginDetails(fixtureName));
    });

    this.Given("I'm a SAML System Administrator", {timeout: 20 * 1000}, function () {
        var fixtureName = 'admin/saml_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.skipLogin();
    });

    this.Given("I'm an Instructor", {timeout: 20 * 1000}, function () {
        var fixtureName = 'instructor/default_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.login(backEndMocks.getLoginDetails(fixtureName));
    });

    this.Given("I'm a SAML Instructor", {timeout: 20 * 1000}, function () {
        var fixtureName = 'instructor/saml_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.skipLogin();
    });

    this.Given("I'm a Student", {timeout: 20 * 1000}, function () {
        var fixtureName = 'student/default_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.login(backEndMocks.getLoginDetails(fixtureName));
    });

    this.Given("I'm a SAML Student", {timeout: 20 * 1000}, function () {
        var fixtureName = 'student/saml_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.skipLogin();
    });
};

module.exports = setupAdminStepDefinitionsWrapper;