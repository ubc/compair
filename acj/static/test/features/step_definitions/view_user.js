// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewUserStepDefinitionsWrapper = function () {
    //root's Profile 
    //student1's Profile 
    
	this.Then(/^I should see the edit profile button$/, function (done) {
        expect(element(by.css("#edit-profile-btn")).isPresent()).to.eventually.equal(true).and.notify(done);
    });
    
	this.Then(/^I should not see the edit profile button$/, function (done) {
        expect(element(by.css("#edit-profile-btn")).isPresent()).to.eventually.equal(false).and.notify(done);
    });
    
	this.Then(/^I should see root's profile$/, function (done) {
        expect(element(by.css("h1")).getText()).to.eventually.equal("root's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("System Administrator");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("root");
        expect(element(by.css("#user_student_no")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("JaNy bwsV");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("root");
        expect(element(by.css("#user_email")).getText()).to.eventually.equal("");
        
        expect(element(by.css("#user_avatar")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#user_lastonline")).isPresent()).to.eventually.equal(true);
        
        done();
	});
    
	this.Then(/^I should see First Instructor's profile$/, function (done) {
        expect(element(by.css("h1")).getText()).to.eventually.equal("First Instructor's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Instructor");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("instructor1");
        expect(element(by.css("#user_student_no")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Instructor");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Instructor");
        expect(element(by.css("#user_email")).getText()).to.eventually.equal("first.instructor@exmple.com");
        
        expect(element(by.css("#user_avatar")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#user_lastonline")).isPresent()).to.eventually.equal(true);
        
        done();
	});
    
	this.Then(/^I should see First Instructor's profile$/, function (done) {
        expect(element(by.css("h1")).getText()).to.eventually.equal("First Instructor's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Instructor");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("instructor1");
        expect(element(by.css("#user_student_no")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Instructor");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Instructor");
        expect(element(by.css("#user_email")).getText()).to.eventually.equal("first.instructor@exmple.com");
        
        expect(element(by.css("#user_avatar")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#user_lastonline")).isPresent()).to.eventually.equal(true);
        
        done();
	});
    
	this.Then(/^I should see the student view of First Instructor's profile$/, function (done) {
        expect(element(by.css("h1")).getText()).to.eventually.equal("First Instructor's Profile");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Instructor");
        
        expect(element(by.css("#user_avatar")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#user_lastonline")).isPresent()).to.eventually.equal(true);
        
        expect(element(by.css("#user_system_role")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_username")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_student_no")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_fullname")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_email")).isPresent()).to.eventually.equal(false);
        
        done();
	});
    
	this.Then(/^I should see First Student's profile$/, function (done) {
        expect(element(by.css("h1")).getText()).to.eventually.equal("First Student's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Student");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("student1");
        expect(element(by.css("#user_student_no")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Student");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Student");
        expect(element(by.css("#user_email")).getText()).to.eventually.equal("first.student@exmple.com");
        
        expect(element(by.css("#user_avatar")).isPresent()).to.eventually.equal(true);
        expect(element(by.css("#user_lastonline")).isPresent()).to.eventually.equal(true);
        
        done();
	});
};

module.exports = viewUserStepDefinitionsWrapper;