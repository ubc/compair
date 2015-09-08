// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var PageFactory = require('../../factories/page_factory.js');

var createQuestionStepDefinitionsWrapper = function () {
	var pageFactory = new PageFactory();
	var page;

	this.Given(/^I'm on "([^"]*)" page for course with id "([^"]*)"$/, function (pageName, courseId) {
		page = pageFactory.createPage(pageName);
		return page.get(courseId);
	});

	this.When(/^I select "([^"]*)" button$/, function (linkText) {
		return element(by.linkText(linkText)).click();
	});

	this.Given(/^I select the first criteria$/, function() {
		return element.all(by.repeater("courseCriterion in courseCriteria")).get(0)
			.element(by.css('input')).click();
	});
};
module.exports = createQuestionStepDefinitionsWrapper;