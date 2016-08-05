// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var PageFactory  = require('../../factories/page_factory.js');
var backEndMocks = require('../../factories/http_backend_mocks.js');

var setupStudentStepDefinitionsWrapper = function () {
    var pageFactory = new PageFactory();
    var loginDialog = pageFactory.createPage('login');

    this.Given("I'm a Student", {timeout: 20 * 1000}, function () {
        var fixtureName = 'student/default_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.login(backEndMocks.getLoginDetails(fixtureName));
    });

    this.Given("I'm a Student with courses", {timeout: 20 * 1000}, function () {
        var fixtureName = 'student/has_courses_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.login(backEndMocks.getLoginDetails(fixtureName));
    });

    this.Given("I'm a Student with assignments", {timeout: 20 * 1000}, function () {
        var fixtureName = 'student/has_assignments_fixture';
        backEndMocks.setStorageFixture(browser, fixtureName);
        return loginDialog.login(backEndMocks.getLoginDetails(fixtureName));
    });

};

module.exports = setupStudentStepDefinitionsWrapper;