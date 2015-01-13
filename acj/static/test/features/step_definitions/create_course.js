// Use the external Chai As Promised to deal with resolving promises in
// expectations.
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

// Chai expect().to.exist syntax makes default jshint unhappy.
// jshint expr:true

var PageFactory  = require('../../factories/page_factory.js');
var UserFactory  = require('../../factories/user_factory.js');
var backEndMocks = require('../../factories/http_backend_mocks.js');

var myStepDefinitionsWrapper = function () {
    var pageFactory = new PageFactory();
    var userFactory = new UserFactory();
    var page;

    this.Given(/^I'm "([^"]*)"$/, function (username, done) {
        backEndMocks.build(browser,[backEndMocks.session, backEndMocks.user, backEndMocks.course]);
        var loginDialog = pageFactory.createPage('login');
        loginDialog.get('/');
        loginDialog.login(userFactory.getUser(username)).then(function() {
            // wait for displayname is populated before we reload the page
            element(by.binding('loggedInUser.displayname')).then(function() {
                done();
            })
        });
    });

    this.Given(/^I'm on "([^"]*)" page$/, function (pageName, done) {
        page = pageFactory.createPage(pageName);
        page.get().then(function() {
            done();
        });
    });

    this.When(/^I select "([^"]*)" button$/, function (arg1, done) {
        page.addCourse().then(function() {
            done();
        });
    });

    this.Then(/^"([^"]*)" page should load$/, function (content_title, done) {
        expect($("#view-title").getText()).to.eventually.equal(content_title).and.notify(done);
    });

    this.Given(/^I fill in:$/, function (data, done) {
        var list = data.hashes();
        for (var i = 0; i < list.length; i++) {
            element(by.model(list[i].element)).sendKeys(list[i].content);
        }
        done();
    });

    this.When(/^I click on "([^"]*)" button$/, function (button, done) {
        element(by.css('input[value='+button+']')).click().then(function() {
            done();
        })
    });

    this.When(/^I should be on "([^"]*)" page$/, function (page, done) {
        var page_regex = {
            'course': /.*\/course\/\d+/
        };
        expect(browser.getCurrentUrl()).to.eventually.match(page_regex[page]).and.notify(done);
    });

    this.Then(/^I should see "([^"]*)" in "([^"]*)" on the page$/, function (text, locator, done) {
        expect(element(by.css(locator)).getText()).to.eventually.equal(text).and.notify(done);
    });
};
module.exports = myStepDefinitionsWrapper;