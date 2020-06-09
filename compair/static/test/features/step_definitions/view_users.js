// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewUsersStepDefinitionsWrapper = function () {

    this.Then("I should see '$count' users listed", function (count) {
        return expect(element.all(by.exactRepeater("user in users"))
            .count()).to.eventually.eql(parseInt(count));
    });

    this.Then("I should users with displaynames:", function (data) {
        var list = data.hashes().map(function(item) {
            return item.displayname;
        });

        return expect(element.all(by.exactRepeater("user in users")
            .column('user.displayname')).getText()).to.eventually.eql(list);
    });

    this.When("I select the root's Courses & Accounts link", function () {
        // ignore target="_blank" for link (slows down tests to much)
        browser.executeScript("$('a').attr('target','_self');");
        return element.all(by.exactRepeater("user in users")).get(2)
            .element(by.cssContainingText('a', 'Courses & Accounts')).click();
    });

    this.When("I select student1's Courses & Accounts link", function () {
        // ignore target="_blank" for link (slows down tests to much)
        browser.executeScript("$('a').attr('target','_self');");
        return element.all(by.exactRepeater("user in users")).get(1)
            .element(by.cssContainingText('a', 'Courses & Accounts')).click();
    });

    this.When("I filter users page by '$filter'", function (filter) {
        element(by.css("form.search-users input")).sendKeys(filter);
        // force blur
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });
};

module.exports = viewUsersStepDefinitionsWrapper;