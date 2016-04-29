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
    
	this.Given("I'm a System Administrator", function (done) {
        var fixture  = require('../../fixtures/admin/default_fixture.js');
		backEndMocks.build(browser, fixture);
        
		var loginDialog = pageFactory.createPage('login');
		loginDialog.get('/');
		loginDialog.login(fixture.loginDetails).then(function() {
			// wait for displayname is populated before we reload the page
			browser.wait(browser.isElementPresent(element(by.binding('loggedInUser.displayname'))), 5000);
			done();
		});
	});
    
	this.Given("I'm a System Administrator with courses", function (done) {
        var fixture  = require('../../fixtures/admin/has_courses_fixture.js');
		backEndMocks.build(browser, fixture);
        
		var loginDialog = pageFactory.createPage('login');
		loginDialog.get('/');
		loginDialog.login(fixture.loginDetails).then(function() {
			// wait for displayname is populated before we reload the page
			browser.wait(browser.isElementPresent(element(by.binding('loggedInUser.displayname'))), 5000);
			done();
		});
	});
    
};

module.exports = setupAdminStepDefinitionsWrapper;