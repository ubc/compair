// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewUserStepDefinitionsWrapper = function () {

    this.When("I toggle the user notification settings option", function() {
        return element(by.model("user.email_notification_method")).click()
    });

    this.Then("I should see the notification settings set to off", function() {
        return expect(element(by.model("user.email_notification_method")).isSelected()).to.eventually.equal(false);
    });

    this.Then("I should see the edit profile button", function () {
        return expect(element(by.css("#edit-profile-btn")).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should not see the edit profile button", function () {
        return expect(element(by.css("#edit-profile-btn")).isPresent()).to.eventually.equal(false);
    });

    this.Then("I should see the edit notification settings option", function () {
        return expect(element(by.css("#user_email_notification_method")).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should not see the edit notification settings option", function () {
        return expect(element(by.css("#user_email_notification_method")).isPresent()).to.eventually.equal(false);
    });

    this.Then("I should see root's profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("#user_student_number")).isPresent()).to.eventually.equal(false);

        expect(element(by.css("h1")).getText()).to.eventually.equal("root's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("System Administrator");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("root");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("JaNy bwsV");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("root");
        return expect(element(by.css("#user_email")).getText()).to.eventually.equal("admin@exmple.com");
    });

    this.Then("I should see First Instructor's profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("#user_student_number")).isPresent()).to.eventually.equal(false);

        expect(element(by.css("h1")).getText()).to.eventually.equal("First Instructor's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Instructor");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("instructor1");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Instructor");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Instructor");
        return expect(element(by.css("#user_email")).getText()).to.eventually.equal("first.instructor@exmple.com");
    });

    this.Then("I should see First Instructor's CAS profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("#user_username")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_student_number")).isPresent()).to.eventually.equal(false);

        expect(element(by.css("h1")).getText()).to.eventually.equal("First Instructor's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Instructor");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Instructor");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Instructor");
        return expect(element(by.css("#user_email")).getText()).to.eventually.equal("first.instructor@exmple.com");
    });

    this.Then("I should see the student view of First Instructor's profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("#user_system_role")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_username")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_student_number")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_fullname")).isPresent()).to.eventually.equal(false);
        expect(element(by.css("#user_email")).isPresent()).to.eventually.equal(false);

        expect(element(by.css("h1")).getText()).to.eventually.equal("First Instructor's Profile");
        return expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Instructor");
    });

    this.Then("I should see First Student's profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("h1")).getText()).to.eventually.equal("First Student's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Student");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("student1");
        expect(element(by.css("#user_student_number")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Student");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Student");
        return expect(element(by.css("#user_email")).getText()).to.eventually.equal("first.student@exmple.com");
    });

    this.Then("I should see instructor view of First Student's profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("h1")).getText()).to.eventually.equal("First Student's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Student");
        expect(element(by.css("#user_username")).getText()).to.eventually.equal("student1");
        expect(element(by.css("#user_student_number")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Student");
        return expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Student");
    });

    this.Then("I should see First Student's CAS profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("#user_username")).isPresent()).to.eventually.equal(false);

        expect(element(by.css("h1")).getText()).to.eventually.equal("First Student's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Student");
        expect(element(by.css("#user_student_number")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Student");
        expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Student");
        return expect(element(by.css("#user_email")).getText()).to.eventually.equal("first.student@exmple.com");
    });

    this.Then("I should see instructor view of First Student's CAS profile", {timeout: 10 * 1000}, function () {
        expect(element(by.css("#user_username")).isPresent()).to.eventually.equal(false);

        expect(element(by.css("h1")).getText()).to.eventually.equal("First Student's Profile");
        expect(element(by.css("#user_system_role")).getText()).to.eventually.equal("Student");
        expect(element(by.css("#user_student_number")).getText()).to.eventually.equal("");
        expect(element(by.css("#user_fullname")).getText()).to.eventually.equal("First Student");
        return expect(element(by.css("#user_displayname")).getText()).to.eventually.equal("First Student");
    });
};

module.exports = viewUserStepDefinitionsWrapper;