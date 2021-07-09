// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewLTIConsumersStepDefinitionsWrapper = function () {

    this.When("I click the first consumer's key", function () {
        return element.all(by.repeater("consumer in consumers"))
            .get(0)
            .element(by.cssContainingText('a', 'consumer_key_1'))
            .click();
    });

    this.Then("I should see consumer_key_1's information", function () {
        expect(element(by.css("#consumer_launch_url")).isPresent()).to.eventually.equal(true);

        expect(element(by.css("#consumer_oauth_consumer_key")).getText()).to.eventually.equal("consumer_key_1");
        expect(element(by.css("#consumer_oauth_consumer_secret")).getText()).to.eventually.equal("consumer_secret_1");
        expect(element(by.css("#consumer_global_unique_identifier_param")).getText()).to.eventually.equal("consumer_global_unique_identifier_param");
        expect(element(by.css("#consumer_student_number_param")).getText()).to.eventually.equal("consumer_consumer_student_number_param");
        expect(element(by.css("#consumer_custom_param_regex_sanitizer")).getText()).to.eventually.equal("consumer_custom_param_regex_sanitizer");
        expect(element(by.model("consumer.active")).isSelected()).to.eventually.equal(true);

        expect(element(by.css("#consumer_created")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#consumer_modified")).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should see consumer_key_3's information", function () {
        expect(element(by.css("#consumer_launch_url")).isPresent()).to.eventually.equal(true);

        expect(element(by.css("#consumer_oauth_consumer_key")).getText()).to.eventually.equal("consumer_key_3");
        expect(element(by.css("#consumer_oauth_consumer_secret")).getText()).to.eventually.equal("consumer_secret_3");
        expect(element(by.css("#consumer_global_unique_identifier_param")).getText()).to.eventually.equal("");
        expect(element(by.css("#consumer_student_number_param")).getText()).to.eventually.equal("");
        expect(element(by.css("#consumer_custom_param_regex_sanitizer")).getText()).to.eventually.equal("");
        expect(element(by.model("consumer.active")).isSelected()).to.eventually.equal(false);

        expect(element(by.css("#consumer_created")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#consumer_modified")).isPresent()).to.eventually.equal(true);
    });

};

module.exports = viewLTIConsumersStepDefinitionsWrapper;