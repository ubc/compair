// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editUserStepDefinitionsWrapper = function () {
    this.Then("I should see the system role in the Account Details section", function() {
        // Account Details
        return expect(element(by.model('user.system_role')).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should not see the system role in the Account Details section", function() {
        // Account Details
        return expect(element(by.model('user.system_role')).isPresent()).to.eventually.equal(false);
    });

    this.Then("I should see the student number in the Account Details section", function() {
        // Account Details
        return expect(element(by.model('user.student_number')).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should not see the student number in the Account Details section", function() {
        // Account Details
        return expect(element(by.model('user.student_number')).isPresent()).to.eventually.equal(false);
    });

    this.Then("I should see email fields in the Account Details section", function() {
        // Account Details
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(true);
        return expect(element(by.model('user.email_notification_method')).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should not see email fields in the Account Details section", function() {
        // Account Details
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(false);
        return expect(element(by.model('user.email_notification_method')).isPresent()).to.eventually.equal(false);
    });

    this.Then("I should see the rest of the Account Details section fields", function() {
        // Account Details
        expect(element(by.model('user.displayname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.firstname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.lastname')).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should see the Account Login section", function() {
        // Account Login
        return expect(element(by.model('user.username')).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should not see the Account Login section", function() {
        // Account Login
        return expect(element(by.model('user.username')).isPresent()).to.eventually.equal(false);
    });
};
module.exports = editUserStepDefinitionsWrapper;