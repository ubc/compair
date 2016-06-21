// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editAssignmentStepDefinitionsWrapper = function () {
    this.Given(/^I fill in the criterion description with "([^"]*)"$/, function(text, done) {
        //load the ckeditor iframe
        browser.wait(browser.isElementPresent(element(by.css("#cke_criterionDescription iframe"))), 1000);
        browser.driver.switchTo().frame(element(by.css("#cke_criterionDescription iframe")).getWebElement());
        // clear the content
        browser.driver.executeScript("document.body.innerHTML = '';")
        browser.driver.findElement(by.css("body")).sendKeys(text);
        browser.driver.switchTo().defaultContent();
        done();
    });

    this.Given("I edit the second criterion", function(done) {
        element.all(by.repeater("(key, criterion) in assignment.criteria")).get(1)
            .element(by.cssContainingText('a', 'Edit')).click();

        browser.wait(browser.isElementPresent(element(by.css(".modal.in"))), 1000);
        done();
    });

    this.Given("I add a new criterion", function(done) {
        element(by.id("add-new-criteria")).click();

        browser.wait(browser.isElementPresent(element(by.css(".modal.in"))), 1000);
        done();
    });


    this.Given("I drop the first criterion", function(done) {
        element.all(by.repeater("(key, criterion) in assignment.criteria")).get(0)
            .element(by.cssContainingText('a', 'Drop')).click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();

        done();
    });

    this.Given("I add my default criterion", function(done) {
        element(by.id("select-default-criteria")).sendKeys("Which sounds better?");
        element(by.id("add-default-criteria")).click();

        done();
    });

    this.Then("I should see the assignment with the new name and description", function(done) {
        var item = element.all(by.repeater("(key, assignment) in assignments | filter:assignmentFilter(filter) as results")).get(2)

        expect(item.element(by.css(".media-heading")).getText()).to.eventually.equal("New Name »");
        expect(item.element(by.css(".assignment-desc p")).getText()).to.eventually.equal("This is the new description");

        done();
    });

    this.Then("I should not be able to modify criteria", function() {
        return element.all(by.repeater("(key, criterion) in assignment.criteria")).then(function(elements) {
            return elements.map(function(item) {
                expect(item.element(by.cssContainingText('a', 'Edit')).isPresent()).to.eventually.equal(false);
                return expect(item.element(by.cssContainingText('a', 'Drop')).isPresent()).to.eventually.equal(false);
            });
        });
    });

    this.Then("I should not be able to add criteria", function() {
        expect(element(by.css("#add-new-criteria")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#select-default-criteria")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#add-default-criteria")).isPresent()).to.eventually.equal(false);
    });
};
module.exports = editAssignmentStepDefinitionsWrapper;
