// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editCourseUserStepDefinitionsWrapper = function () {

    this.Then(/^I should see "([^"]*)" users listed for the course$/, function (count, done) {
        count = parseInt(count);
        expect(element.all(by.repeater('user in classlist | orderBy:predicate:reverse'))
            .count()).to.eventually.eql(count).and.notify(done);
    });

    this.Then("I should see course users with displaynames:", function (data, done) {
        var list = data.hashes().map(function(item) {
            // add the " »" that is displayed on the page
            return item.displayname;
        });

        expect(element.all(by.repeater('user in classlist | orderBy:predicate:reverse')
            .column('user.displayname')).getText()).to.eventually.eql(list).and.notify(done);
    });

    this.When("I select the first user search result", function () {
        return element(by.repeater('match in matches track by $index').row(0)).click();
    });


    this.When("I select the Student role for the user", function (done) {
        var fillElement = element(by.css("#enrol-select-course-role"));

        if (browser.browserName == "firefox") {
            fillElement.click();
        }
        fillElement.sendKeys("Student");

        // force blur
        element(by.css("body")).click();

        done();
    });

    this.When("I sort by displayname in decending order", function () {
        return element(by.cssContainingText("table th a", "Display Name")).click().click();
    });

    this.When(/^I set the second user's group to "([^"]*)"$/, function (groupname, done) {
        var groupSelect = element.all(by.repeater("user in classlist | orderBy:predicate:reverse"))
            .get(1).element(by.model('user.group_name'));
        if (browser.browserName == "firefox") {
            groupSelect.click();
        }

        groupSelect.sendKeys(groupname);
        // force blur
        element(by.css("h1")).click();

        done();
    });

    this.Given("I drop the second user from the course", function (done) {
        element.all(by.repeater("user in classlist | orderBy:predicate:reverse")).get(1)
            .element(by.cssContainingText('a', 'Drop')).click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        done();
    });
};

module.exports = editCourseUserStepDefinitionsWrapper;