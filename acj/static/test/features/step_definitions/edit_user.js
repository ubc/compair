// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editUserStepDefinitionsWrapper = function () {
    this.Then(/^I should see the full Account Details and Account Login sections of the Edit User form for students$/, function(done) {
        // Account Login
        expect(element(by.model('user.username')).isPresent()).to.eventually.equal(true);

        // Account Details
        expect(element(by.model('user.system_role')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.displayname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.firstname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.lastname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.student_number')).isPresent()).to.eventually.equal(true);

        done();
    });
    this.Then(/^I should see the full Account Details and Account Login sections of the Edit User form for non-students$/, function(done) {
        // Account Login
        expect(element(by.model('user.username')).isPresent()).to.eventually.equal(true);

        // Account Details
        expect(element(by.model('user.system_role')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.displayname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.firstname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.lastname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.student_number')).isPresent()).to.eventually.equal(false);

        done();
    });
    this.Then(/^I should see the incomplete Account Details section of the Edit User form for students$/, function(done) {
        // Account Login
        expect(element(by.model('user.username')).isPresent()).to.eventually.equal(true);

        // Account Details
        expect(element(by.model('user.system_role')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('user.displayname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.firstname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.lastname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.student_number')).isPresent()).to.eventually.equal(true);

        done();
    });
    this.Then(/^I should see the incomplete Account Details section of the Edit User form for non-students$/, function(done) {
        // Account Login
        expect(element(by.model('user.username')).isPresent()).to.eventually.equal(true);

        // Account Details
        expect(element(by.model('user.system_role')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('user.displayname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.firstname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.lastname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.student_number')).isPresent()).to.eventually.equal(false);

        done();
    });

    this.Then(/^I should see the Password section of the Edit User form$/, function(done) {
        expect(element(by.model('password.oldpassword')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('password.newpassword')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('password.verifypassword')).isPresent()).to.eventually.equal(true);
        done();
    });

    this.Then(/^I should see the Password section of the Edit User form without old password$/, function(done) {
        expect(element(by.model('password.oldpassword')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('password.newpassword')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('password.verifypassword')).isPresent()).to.eventually.equal(true);
        done();
    });

    this.Then(/^I should not see the Password section of the Edit User form$/, function(done) {
        expect(element(by.model('password.oldpassword')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('password.newpassword')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('password.verifypassword')).isPresent()).to.eventually.equal(false);
        done();
    });

};
module.exports = editUserStepDefinitionsWrapper;