// Use the external Chai As Promised to deal with resolving promises in
// expectations.
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var PageFactory  = require('../../factories/page_factory.js');
var UserFactory  = require('../../factories/user_factory.js');
var backEndMocks = require('../../factories/http_backend_mocks.js');

var commonStepDefinitionsWrapper = function() {
	var pageFactory = new PageFactory();
    var page;
	var userFactory = new UserFactory();
	var mocks = [
		backEndMocks.session,
		backEndMocks.user,
		backEndMocks.course,
		backEndMocks.question
	];

	// login and setup mock backend
	this.Given(/^I'm "([^"]*)"$/, function (username, done) {
		backEndMocks.build(browser, mocks);
		var loginDialog = pageFactory.createPage('login');
		loginDialog.get('/');
		loginDialog.login(userFactory.getUser(username)).then(function() {
			// wait for displayname is populated before we reload the page
			browser.wait(browser.isElementPresent(element(by.binding('loggedInUser.displayname'))), 5000);
			done();
		});
	});

	// check title of page
	this.Then(/^"([^"]*)" page should load$/, function (content_title, done) {
		expect($("#view-title").getText()).to.eventually.equal(content_title).and.notify(done);
	});

	// fill in form
	this.Given(/^I fill in:$/, function (data, done) {
		var list = data.hashes();
		for (var i = 0; i < list.length; i++) {
			element(by.model(list[i].element)).sendKeys(list[i].content);
		}
		done();
	});
    
    // generate page factory
	this.Given(/^I'm on "([^"]*)" page$/, function (pageName) {
		page = pageFactory.createPage(pageName);
		return page.get();
	});

	this.Given(/^I'm on "([^"]*)" page for course with id "([^"]*)"$/, function (pageName, id) {
		page = pageFactory.createPage(pageName);
		return page.get(id);
	});
    
    // click button on page factory
	this.When(/^I select "([^"]*)" button$/, function (button) {
		return page.clickButton(button);
	});
    
    //submit form button
	this.When(/^I submit form with "([^"]*)" button$/, function (button) {
		return element(by.css('input[type=submit][value='+button+']')).click();
	});

    // page verification
	this.When(/^I should be on "([^"]*)" page$/, function (page, done) {
		var page_regex = {
			'course': /.*\/course\/\d+/,
			'user profile': /.*\/user\/\d+/
		};
		expect(browser.getCurrentUrl()).to.eventually.match(page_regex[page]).and.notify(done);
	});

    // pause test (helpful for debugging)
	this.When(/^I should be paused$/, function (page, done) {
		browser.pause();
	});
    
    // verify content on page
	this.Then(/^I should see "([^"]*)" in "([^"]*)" on the page$/, function (text, locator, done) {
		expect(element(by.css(locator)).getText()).to.eventually.equal(text).and.notify(done);
	});
};
module.exports = commonStepDefinitionsWrapper;