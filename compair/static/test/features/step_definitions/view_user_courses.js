// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewUserCoursesStepDefinitionsWrapper = function () {

    this.Then("I should see '$count' courses listed", function (count) {
        browser.waitForAngular();
        return expect(element.all(by.exactRepeater("course in courses"))
            .count()).to.eventually.eql(parseInt(count));
    });

    this.Then("I should see courses with names:", function (data) {
        browser.waitForAngular();
        var list = data.hashes().map(function(item) {
            return item.name;
        });

        return expect(element.all(by.exactRepeater("course in courses")
            .column('course.name')).getText()).to.eventually.eql(list);
    });

    this.When("I filter user courses page by '$filter'", function (filter) {
        element(by.css("form.search-courses input")).sendKeys(filter);
        // force blur
        return element(by.css("body")).click();
    });

    this.When("I select drop for the first course listed", function () {
        element.all(by.exactRepeater("course in courses")).get(0)
            .element(by.cssContainingText('a', 'Drop')).click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        return element(by.css("body")).click();
    });

    this.When("I select the Student role for the first course", function () {
        var roleSelect = element.all(by.exactRepeater("course in courses"))
            .get(0)
            .element(by.model('course.course_role'));
        if (browser.browserName == "firefox") {
            roleSelect.click();
        }

        roleSelect.sendKeys('Student');
        // force blur
        return element(by.css("body")).click();
    });

    this.When("I set the first course's group to '$groupname'", function (groupname) {
        var groupSelect = element.all(by.exactRepeater("course in courses"))
            .get(0)
            .element(by.model('course.group_name'));
        if (browser.browserName == "firefox") {
            groupSelect.click();
        }

        groupSelect.sendKeys(groupname);
        // force blur
        return element(by.css("body")).click();
    });
};

module.exports = viewUserCoursesStepDefinitionsWrapper;