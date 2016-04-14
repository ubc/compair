// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var createQuestionStepDefinitionsWrapper = function () {
	this.Given(/^I select the first criteria$/, function() {
		return element.all(by.repeater("courseCriterion in courseCriteria")).get(0)
			.element(by.css('input')).click();
	});
};
module.exports = createQuestionStepDefinitionsWrapper;