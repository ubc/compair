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

	this.Given(/^I'm on "([^"]*)" page for course with id "([^"]*)"$/, function (pageName, courseId, done) {
		page = pageFactory.createPage(pageName);
		page.get(courseId).then(function() {
			done();
		});
	});

	this.When(/^I select 'Add Question' button$/, function (done) {
		page.addQuestion().then(function() {
			done()
		});
	});
	this.Given(/^I select the first criteria$/, function(done) {
		element.all(by.repeater("courseCriterion in courseCriteria")).get(0)
			.element(by.css('input')).click().then(function(){
				done();
		});
	});
};
module.exports = createQuestionStepDefinitionsWrapper;