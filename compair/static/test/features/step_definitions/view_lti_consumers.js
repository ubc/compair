// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewLTIConsumersStepDefinitionsWrapper = function () {

    this.Then("I should see '$count' consumers listed", function (count) {
        return expect(element.all(by.exactRepeater("consumer in consumers"))
            .count()).to.eventually.eql(parseInt(count));
    });

    this.Then("I should see '$count' contexts listed", function (count) {
        return expect(element.all(by.exactRepeater("context in contexts"))
            .count()).to.eventually.eql(parseInt(count));
    });

    this.Then("I should see consumers with consumer keys:", function (data) {
        var list = data.hashes().map(function(item) {
            return item.oauth_consumer_key;
        });

        return expect(element.all(by.exactRepeater("consumer in consumers")
            .column('consumer.oauth_consumer_key')).getText()).to.eventually.eql(list);
    });

    this.When("I sort by oauth_consumer_key in ascending order", function () {
        return element.all(by.cssContainingText("table th a", "Consumer Key")).first().click();
    });

    this.Then("I should see contexts with titles:", function (data) {
        var list = data.hashes().map(function(item) {
            return item.context_title;
        });

        return expect(element.all(by.exactRepeater("context in contexts")
            .column('context.context_title')).getText()).to.eventually.eql(list);
    });

    this.When("I set the first consumer's active status to '$active'", function (active) {
        var activeSelect = element.all(by.exactRepeater("consumer in consumers"))
            .get(0)
            .element(by.model('consumer.active'));
        if (browser.browserName == "firefox") {
            activeSelect.click();
        }

        activeSelect.sendKeys(active);
        // force blur
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });

    this.When("I set the third consumer's active status to '$active'", function (active) {
        var activeSelect = element.all(by.exactRepeater("consumer in consumers"))
            .get(2)
            .element(by.model('consumer.active'));
        if (browser.browserName == "firefox") {
            activeSelect.click();
        }

        activeSelect.sendKeys(active);
        // force blur
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });

    this.When("I click the first consumer's Edit button", function () {
        return element.all(by.exactRepeater("consumer in consumers"))
            .get(0)
            .element(by.cssContainingText('a', 'Edit'))
            .click();
    });

    this.When("I unlink the second lti context", function () {
        element.all(by.exactRepeater("context in contexts"))
            .get(1)
            .element(by.css('a'))
            .click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        return browser.driver.switchTo().defaultContent();
    });
};

module.exports = viewLTIConsumersStepDefinitionsWrapper;