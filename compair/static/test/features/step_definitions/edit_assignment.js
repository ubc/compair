// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editAssignmentStepDefinitionsWrapper = function () {
    this.Given("I fill in the criterion description with '$text'", function(text) {
        //load the ckeditor iframe
        browser.sleep(1000);
        browser.wait(browser.isElementPresent(element(by.css("#cke_criterionDescription iframe"))), 1000);
        browser.driver.switchTo().frame(element(by.css("#cke_criterionDescription iframe")).getWebElement());
        // clear the content
        browser.driver.executeScript("document.body.innerHTML = '';")
        browser.driver.findElement(by.css("body")).sendKeys(text);
        browser.driver.switchTo().defaultContent();
        return element(by.css("body")).click();
    });

    this.When("I edit the second criterion", function() {
        element.all(by.repeater("(key, criterion) in assignment.criteria")).get(1)
            .element(by.cssContainingText('a', 'Edit')).click();

        browser.wait(browser.isElementPresent(element(by.css(".modal.in"))), 1000);
        return element(by.css(".modal.in")).click();
    });

    this.When("I add a new criterion", function() {
        element(by.id("add-new-criteria")).click();

        browser.wait(browser.isElementPresent(element(by.css(".modal.in"))), 1000);
        return element(by.css(".modal.in")).click();
    });


    this.When("I drop the first criterion", function() {
        element.all(by.repeater("(key, criterion) in assignment.criteria")).get(0)
            .element(by.cssContainingText('a', 'Drop')).click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        return element(by.css("body")).click();
    });

    this.When("I add my default criterion", function() {
        element(by.id("select-default-criteria")).sendKeys("Which sounds better?");
        return element(by.id("add-default-criteria")).click();
    });

    this.Then("I should see the assignment with the new name", function() {
        var item = element.all(by.exactRepeater("assignment in assignments")).get(2)

        return expect(item.element(by.css(".media-heading")).getText()).to.eventually.equal("New Name »");
    });

    this.Then("I should see a warning message in the edit criterion modal", function() {
        return expect(element(by.css('.modal .intro-text.text-warning')).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should not be able to remove criteria", function() {
        return element.all(by.repeater("(key, criterion) in assignment.criteria")).then(function(elements) {
            return elements.map(function(item) {
                return expect(item.element(by.cssContainingText('a', 'Drop')).isPresent()).to.eventually.equal(false);
            });
        });
    });

    this.Then("I should not be able to add criteria", function() {
        expect(element(by.css("#add-new-criteria")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#select-default-criteria")).isPresent()).to.eventually.equal(false);
        return expect(element(by.css("#add-default-criteria")).isPresent()).to.eventually.equal(false);
    });
};
module.exports = editAssignmentStepDefinitionsWrapper;
