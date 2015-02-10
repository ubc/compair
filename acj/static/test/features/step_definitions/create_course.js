// Use the external Chai As Promised to deal with resolving promises in
// expectations.
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

// Chai expect().to.exist syntax makes default jshint unhappy.
// jshint expr:true

var PageFactory  = require('../../factories/page_factory.js');

var createCourseStepDefinitionsWrapper = function () {
	var pageFactory = new PageFactory();
	var page;

	this.Given(/^I'm on "([^"]*)" page$/, function (pageName, done) {
		page = pageFactory.createPage(pageName);
		page.get().then(function() {
			done();
		});
	});

	this.When(/^I select 'Add Course' button$/, function (done) {
		page.addCourse().then(function() {
			done();
		});
	});

	this.When(/^I click on "([^"]*)" button$/, function (button, done) {
		element(by.css('input[value='+button+']')).click().then(function() {
			done();
		})
	});

	this.When(/^I should be on "([^"]*)" page$/, function (page, done) {
		var page_regex = {
			'course': /.*\/course\/\d+/
		};
		expect(browser.getCurrentUrl()).to.eventually.match(page_regex[page]).and.notify(done);
	});

	this.Then(/^I should see "([^"]*)" in "([^"]*)" on the page$/, function (text, locator, done) {
		expect(element(by.css(locator)).getText()).to.eventually.equal(text).and.notify(done);
	});
};
module.exports = createCourseStepDefinitionsWrapper;