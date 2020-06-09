// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var createAssignmentStepDefinitionsWrapper = function () {
    this.Given("I fill in the assignment description with '$text'", function(text) {
        //load the ckeditor iframe
        browser.sleep(2000);
        browser.wait(browser.isElementPresent(element(by.css("#cke_assignmentDescription iframe"))), 1000);
        browser.driver.switchTo().frame(element(by.css("#cke_assignmentDescription iframe")).getWebElement());
        // clear the content
        browser.driver.executeScript("document.body.innerHTML = '';")
        browser.driver.findElement(by.css("body")).click();
        browser.driver.findElement(by.css("body")).sendKeys(text);
        browser.driver.switchTo().defaultContent();
        browser.sleep(2000);
        return;
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        //return element(by.css("body")).click();
    });
};
module.exports = createAssignmentStepDefinitionsWrapper;