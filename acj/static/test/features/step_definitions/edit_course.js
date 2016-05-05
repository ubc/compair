// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editCourseStepDefinitionsWrapper = function () {

    this.Given(/^I fill in the criteria description with "([^"]*)"$/, function(text, done) {
        //load the ckeditor iframe
        browser.wait(browser.isElementPresent(element(by.css("#cke_criterionDescription iframe"))), 1000);
        browser.driver.switchTo().frame(element(by.css("#cke_criterionDescription iframe")).getWebElement());
        // clear the content
        browser.driver.executeScript("document.body.innerHTML = '';")
        browser.driver.findElement(by.css("body")).sendKeys(text);
        browser.driver.switchTo().defaultContent();
        done();
    });

    this.Given("I edit the second criteria", function(done) {
        element.all(by.repeater("(key, criterion) in course.criteria")).get(1)
            .element(by.cssContainingText('a', 'Edit')).click();
        
        browser.wait(browser.isElementPresent(element(by.css(".modal.in"))), 1000);
        done();
    });
    
    this.Given("I add a new criteria", function(done) {
        element(by.id("add-new-criteria")).click();
        
        browser.wait(browser.isElementPresent(element(by.css(".modal.in"))), 1000);
        done();
    });
    
    
    this.Given("I drop the first criteria", function(done) {
        element.all(by.repeater("(key, criterion) in course.criteria")).get(0)
            .element(by.cssContainingText('a', 'Drop')).click();
            
        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000); 
            
        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        
        done();
    });
    
    this.Given("I add my default criteria", function() {
        element(by.id("select-default-criteria")).sendKeys("Which sounds better?");
        
        return element(by.id("add-default-criteria")).click();
    });
};
module.exports = editCourseStepDefinitionsWrapper;