// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewNavbarStepDefinitionsWrapper = function () {
    this.Then("I should see the brand home link", function () {
        return expect(element(by.css(".navbar-header a.navbar-brand img")).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should see the admin navigation items", function () {
        return expect(element.all(by.css("#logged-in-nav-options li a")).getText()).to.eventually.eql(["Download Reports", "Add Course", "Add User", "Manage All Users", "Manage LTI"]);
    });

    this.Then("I should see the instructor navigation items", function () {
        return expect(element.all(by.css("#logged-in-nav-options li a")).getText()).to.eventually.eql(["Download Reports", "Add Course"]);
    });

    this.Then("I should see the student navigation items", function () {
        return expect(element.all(by.css("#logged-in-nav-options li a")).getText()).to.eventually.eql([]);
    });

    this.Then("I should see the profile and logout links", function () {
        expect(element(by.css("#menu-dropdown")).isPresent()).to.eventually.equal(true);

        element(by.css("#menu-dropdown")).click();

        expect(element(by.css("#own-profile-link")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#logout-link")).isPresent()).to.eventually.equal(true);
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });
};

module.exports = viewNavbarStepDefinitionsWrapper;