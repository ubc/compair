// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewUserManageStepDefinitionsWrapper = function () {

    this.Then("I should see '$count' courses listed", function (count) {
        return expect(element.all(by.exactRepeater("course in courses"))
            .count()).to.eventually.eql(parseInt(count));
    });

    this.Then("I should see courses with names:", function (data) {
        var list = data.hashes().map(function(item) {
            return item.name;
        });

        return expect(element.all(by.exactRepeater("course in courses")
            .column('course.name')).getText()).to.eventually.eql(list);
    });

    this.When("I filter user courses & accounts page courses by '$filter'", function (filter) {
        element(by.css("form.search-courses input")).sendKeys(filter);
        // force blur
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });

    this.When("I select drop for the first course listed", function () {
        element.all(by.exactRepeater("course in courses")).get(0)
            .element(by.cssContainingText('a', 'Drop')).click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
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
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });

    this.When("I set the first course's group to '$groupname'", function (groupname) {
        var groupSelect = element.all(by.exactRepeater("course in courses"))
            .get(0)
            .element(by.model('course.group_id'));
        if (browser.browserName == "firefox") {
            groupSelect.click();
        }

        groupSelect.sendKeys(groupname);
        // force blur
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });

    this.Then("I should see '$count' LTI connections listed", function (count) {
        return expect(element.all(by.exactRepeater("lti_user in lti_users"))
            .count()).to.eventually.eql(parseInt(count));
    });

    this.Then("I should see LTI connections with entries:", function (data) {
        var consumer_keys = data.hashes().map(function(item) {
            return item.consumer_key;
        });
        var user_ids = data.hashes().map(function(item) {
            return item.lti_user_id;
        });

        return expect(element.all(by.exactRepeater("lti_user in lti_users")
            .column('lti_user.oauth_consumer_key')).getText()).to.eventually.eql(consumer_keys) &&
                expect(element.all(by.exactRepeater("lti_user in lti_users")
            .column('lti_user.lti_user_id')).getText()).to.eventually.eql(user_ids);
    });

    this.When("I select unlink for the first LTI connection listed", function () {
        element.all(by.exactRepeater("lti_user in lti_users")).get(0)
            .element(by.css('a.delete-lti-user')).click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });

    this.Then("I should see '$count' third party connections listed", function (count) {
        return expect(element.all(by.exactRepeater("third_party_user in third_party_users"))
            .count()).to.eventually.eql(parseInt(count));
    });

    this.Then("I should see third party connections with entries:", function (data) {
        var types = data.hashes().map(function(item) {
            return item.type;
        });
        var ids = data.hashes().map(function(item) {
            return item.id;
        });

        return expect(element.all(by.exactRepeater("third_party_user in third_party_users")
            .column('third_party_user.third_party_type')).getText()).to.eventually.eql(types) &&
                expect(element.all(by.exactRepeater("third_party_user in third_party_users")
            .column('third_party_user.unique_identifier')).getText()).to.eventually.eql(ids);
    });

    this.When("I select delete for the first third party connection listed", function () {
        element.all(by.exactRepeater("third_party_user in third_party_users")).get(0)
            .element(by.css('a.delete-third-party-user')).click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });
};

module.exports = viewUserManageStepDefinitionsWrapper;