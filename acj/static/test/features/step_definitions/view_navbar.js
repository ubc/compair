// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewNavbarStepDefinitionsWrapper = function () {
    this.Then("I should see the brand home link", function (done) {
        expect(element(by.cssContainingText(".navbar-header a.navbar-brand", "ComPAIR")).isPresent())
            .to.eventually.equal(true).and.notify(done);
    });

    this.Then("I should see the admin navigation items", function (done) {
        expect(element.all(by.css("#logged-in-nav-options li a")).getText())
            .to.eventually.eql(["Download Reports", "Add Course", "Create Account"]).and.notify(done);
    });

    this.Then("I should see the instructor navigation items", function (done) {
        expect(element.all(by.css("#logged-in-nav-options li a")).getText())
            .to.eventually.eql(["Download Reports", "Add Course"]).and.notify(done);
    });

    this.Then("I should see the student navigation items", function (done) {
        expect(element.all(by.css("#logged-in-nav-options li a")).getText())
            .to.eventually.eql([]).and.notify(done);
    });

    this.Then("I should see the profile and logout links", function (done) {
        expect(element(by.css("#menu-dropdown")).isPresent()).to.eventually.equal(true);

        element(by.css("#menu-dropdown")).click();

        expect(element(by.css("#own-profile-link")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#logout-link")).isPresent()).to.eventually.equal(true);

        done();
    });
};

module.exports = viewNavbarStepDefinitionsWrapper;