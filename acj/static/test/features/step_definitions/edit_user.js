// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editUserStepDefinitionsWrapper = function () {
    var userDetailsFormFields = ['user.displayname', 'user.firstname', 'user.lastname', 'user.email'];
    
    
	this.Then(/^I should see the User Login section of the Edit User form$/, function(done) {
        expect(element(by.model('user.usertypesforsystem_id')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.username')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.student_no')).isPresent()).to.eventually.equal(true);
        done();
	});
    
	this.Then(/^I should not see the User Login section of the Edit User form$/, function(done) {
        expect(element(by.model('user.usertypesforsystem_id')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('user.username')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('user.student_no')).isPresent()).to.eventually.equal(false);
        done();
	});
    
	this.Then(/^I should see the User Details section of the Edit User form$/, function(done) {
        expect(element(by.model('user.displayname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.firstname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.lastname')).isPresent()).to.eventually.equal(true);
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(true);
        done();
	});
    
	this.Then(/^I should not see the User Details section of the Edit User form$/, function(done) {
        expect(element(by.model('user.displayname')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('user.firstname')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('user.lastname')).isPresent()).to.eventually.equal(false);
        expect(element(by.model('user.email')).isPresent()).to.eventually.equal(false);
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