// Use the external Chai As Promised to deal with resolving promises in
// expectations.
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var PageFactory  = require('../../factories/page_factory.js');

module.exports = function() {
    this.setDefaultTimeout(10 * 1000);
};

var commonStepDefinitionsWrapper = function() {
    var pageFactory = new PageFactory();
    var page;

    // fill in form
    this.When("I fill form item '$item' in with '$content'", function (item, content) {
        return element(by.model(item)).getTagName().then(function(tagName) {
            // clear inputs and textareas then send keys
            if (tagName == 'input' || tagName == 'textarea') {
                return element(by.model(item)).clear().then(function() {
                    return element(by.model(item)).sendKeys(content);
                });
            } else if (tagName == 'select') {
                if (browser.browserName == "firefox") {
                    element(by.model(item)).click();
                }
                element(by.model(item)).sendKeys(content);

                // force blur
                return element(by.css("body")).click();
            } else {
                return element(by.model(item)).sendKeys(content);
            }
        });
    });

    this.When("I toggle the '$label' checkbox", function (label) {
        return element(by.cssContainingText('label', label)).click();
    });

    this.When("I toggle the '$model' form checkbox", function (model) {
        return element(by.model(model)).click();
    });

    // generate page factory
    this.Given("I'm on '$pageName' page", function (pageName) {
        page = pageFactory.createPage(pageName);
        return browser.setLocation(page.getLocation());
    });

    this.Given("I'm on '$pageName' page for course with id '$id'", function (pageName, id) {
        page = pageFactory.createPage(pageName);
        return browser.setLocation(page.getLocation(id));
    });

    this.Given("I'm on '$pageName' page for assignment with id '$assignmentId' and course id '$courseId'", function (pageName, assignmentId, courseId) {
        page = pageFactory.createPage(pageName);
        return browser.setLocation(page.getLocation(courseId, assignmentId));
    });

    this.Given("I'm on '$pageName' page for user with id '$id'", function (pageName, id) {
        page = pageFactory.createPage(pageName);
        return browser.setLocation(page.getLocation(id));
    });

    this.Given("I'm on '$pageName' page for consumer with id '$id'", function (pageName, id) {
        page = pageFactory.createPage(pageName);
        return browser.setLocation(page.getLocation(id));
    });

    // click button on page factory
    this.When("I select the '$button' button", function (button) {
        return page.clickButton(button);
    });

    //submit form button
    this.When("I submit form with the '$button' button", function (button) {
        return element(by.css('input[type=submit][value="'+button+'"]')).click();
    });

    this.When("I should see the '$button' button", function (button) {
        expect(element(by.cssContainingText('a.btn', button)).isPresent()).to.eventually.equal(true);
    });

    this.When("I should not see the '$button' button", function (button) {
        expect(element(by.cssContainingText('a.btn', button)).isPresent()).to.eventually.equal(false);
    });

    this.When("I submit form with the first '$button' button", function (button) {
        return element.all(by.css('input[type=submit][value="'+button+'"]')).get(0).click();
    });

    this.When("I submit form with the second '$button' button", function (button) {
        return element.all(by.css('input[type=submit][value="'+button+'"]')).get(1).click();
    });

    //submit modal form button
    this.When("I submit modal form with the '$button' button", function (button) {
        return element(by.css('.modal input[type=submit][value="'+button+'"]')).click();
    });

    // page verification
    this.Then("I should be on the '$page' page", function (page) {
        var page_regex = {
            'course': /.*\/course\/[A-Za-z0-9_-]{22}$/,
            'manage users': /.*\/course\/[A-Za-z0-9_-]{22}\/user$/,
            'create assignment': /.*\/course\/[A-Za-z0-9_-]{22}\/assignment\/create$/,
            'edit assignment': /.*\/course\/[A-Za-z0-9_-]{22}\/assignment\/[A-Za-z0-9_-]{22}\/edit$/,
            'create course': /.*\/course\/create$/,
            'edit course': /.*\/course\/[A-Za-z0-9_-]{22}\/edit$/,
            'profile': /.*\/user\/[A-Za-z0-9_-]{22}$/,
            'create user': /.*\/user\/create$/,
            'edit profile': /.*\/user\/[A-Za-z0-9_-]{22}\/edit$/,
            'users': /.*\/users(\?.+)?$/,
            'user courses': /.*\/users\/[A-Za-z0-9_-]{22}\/course(\?.+)?$/,
            'manage lti': /.*\/lti\/consumer(\?.+)?$/,
            'create lti consumer': /.*\/lti\/consumer\/create$/,
            'edit lti consumer': /.*\/lti\/consumer\/[A-Za-z0-9_-]{22}\/edit$/,
            'lti consumer': /.*\/lti\/consumer\/[A-Za-z0-9_-]{22}$/
        };
        return expect(browser.getCurrentUrl()).to.eventually.match(page_regex[page]);
    });

    // verify content on page
    this.Then("I should see '$text' in '$locator' on the page", function (text, locator) {
        text = text.replace("\\n", "\n");
        return expect(element(by.css(locator)).getText()).to.eventually.equal(text);
    });

    this.Then("I should not see '$locator' on the page", function (locator) {
        return expect(element(by.css(locator)).isPresent()).to.eventually.equal(false);
    });

    this.Then("I should see a success message", function () {
        return expect(element(by.css("#toast-container .toast.toast-success")).isPresent()).to.eventually.equal(true);
    });

    this.Then("I should see a failure message", function () {
        return expect(element(by.css("#toast-container .toast.toast-error")).isPresent()).to.eventually.equal(true);
    });

    // pause test (helpful for debugging)
    this.Then("pause", function () {
        browser.pause();
    });
};
module.exports = commonStepDefinitionsWrapper;