// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewCourseStepDefinitionsWrapper = function () {
    this.When("I select the course named '$courseName'", function (courseName) {
        element(by.cssContainingText(".course-list a h3", courseName)).click();
    });

    this.Then("I should see my assignments with names:", function (data) {
        var list = data.hashes().map(function(item) {
            // add the " »" that is displayed on the page
            return item.name + " »";
        });

        return expect(element.all(by.css(".media-body a h3")).getText()).to.eventually.eql(list);
    });

    this.When("I filter course page assignments by '$filter'", function (filter) {
        // Firefox soemtimes has trouble with selects
        if (browser.browserName == "firefox") {
            element(by.css("form.searchCourse select")).click();
        }
        element(by.css("form.searchCourse select")).sendKeys(filter);

        // force blur
        element(by.css("h2")).click();
        browser.wait(browser.isElementPresent(element(by.cssContainingText('h2', filter))), 1000);

        return expect(element(by.cssContainingText('h2', filter)).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should see '$numberString' assignments", function (numberString) {
        var count = parseInt(numberString);

        return expect(element.all(by.css(".media-body a h3")).count()).to.eventually.equal(count);
    });
};

module.exports = viewCourseStepDefinitionsWrapper;