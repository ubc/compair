// Use the external Chai As Promised to deal with resolving promises in
// expectations.
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var PageFactory  = require('../../factories/page_factory.js');

var commonStepDefinitionsWrapper = function() {
	var pageFactory = new PageFactory();
    var page;

	// check title of page
	this.Then(/^"([^"]*)" page should load$/, function (content_title, done) {
		expect($("#view-title").getText()).to.eventually.equal(content_title).and.notify(done);
	});

	// fill in form
	this.Given(/^I fill in:$/, function (data, done) {
		var list = data.hashes();

        var allPromises = list.map(function(item){
            var fillElement = element(by.model(item.element));

            return fillElement.getTagName().then(function(tagName) {
                // clear inputs and textareas then send keys
                if (tagName == 'input' || tagName == 'textarea') {
                    return fillElement.clear().then(function() {
                        return fillElement.sendKeys(item.content);
                    });
                } else if (tagName == 'select') {
					if (browser.browserName == "firefox") {
						fillElement.click();
					}
					fillElement.sendKeys(item.content);

					// force blur
                    return element(by.css("body")).click();
                } else {
                    return fillElement.sendKeys(item.content);
				}
            });
        });

        protractor.promise.all(allPromises).then(function(){
            done();
        });
	});

	this.Given(/^I toggle the "([^"]*)" checkbox$/, function (label, done) {
		return element(by.cssContainingText('label', label)).click();
	});

	// verify the form
	this.Given(/^I should see form fields:$/, function (data, done) {
		var list = data.hashes();

        list.forEach(function(item){
            expect(element(by.model(item.element)).isPresent()).to.eventually.equal(true);
        });

        done();
	});

	this.Given(/^I should not see form fields:$/, function (data, done) {
		var list = data.hashes();

        list.forEach(function(item){
            expect(element(by.model(item.element)).isPresent()).to.eventually.equal(false);
        });

        done();
	});

    // generate page factory
	this.Given(/^I'm on "([^"]*)" page$/, function (pageName) {
		page = pageFactory.createPage(pageName);
		return page.get();
	});

	this.Given(/^I'm on "([^"]*)" page for course with id "([^"]*)"$/, function (pageName, id) {
		page = pageFactory.createPage(pageName);
		return page.get(id);
	});

	this.Given(/^I'm on "([^"]*)" page for assignment with id "([^"]*)" and course id "([^"]*)"$/, function (pageName, assignmentId, courseId) {
		page = pageFactory.createPage(pageName);
		return page.get(courseId, assignmentId);
	});

	this.Given(/^I'm on "([^"]*)" page for user with id "([^"]*)"$/, function (pageName, id) {
		page = pageFactory.createPage(pageName);
		return page.get(id);
	});

    // click button on page factory
	this.When(/^I select "([^"]*)" button$/, function (button) {
		return page.clickButton(button);
	});

    //submit form button
	this.When(/^I submit form with "([^"]*)" button$/, function (button) {
		return element(by.css('input[type=submit][value="'+button+'"]')).click();
	});

    //submit modal form button
	this.When(/^I submit modal form with "([^"]*)" button$/, function (button) {
		return element(by.css('.modal input[type=button][value="'+button+'"]')).click();
	});

    // page verification
	this.When(/^I should be on the "([^"]*)" page$/, function (page, done) {
		var page_regex = {
			'course': /.*\/course\/\d+$/,
			'manage users': /.*\/course\/\d+\/user$/,
            'edit assignment': /.*\/course\/\d+\/assignment\/\d+\/edit$/,
            'edit course': /.*\/course\/\d+\/configure$/,
			'profile': /.*\/user\/\d+$/,
            'create user': /.*\/user\/create$/,
			'edit profile': /.*\/user\/\d+\/edit$/
		};
		expect(browser.getCurrentUrl()).to.eventually.match(page_regex[page]).and.notify(done);
	});

    // verify content on page
	this.Then(/^I should see "([^"]*)" in "([^"]*)" on the page$/, function (text, locator, done) {
		expect(element(by.css(locator)).getText()).to.eventually.equal(text).and.notify(done);
	});

	this.Then(/^I should see "([^"]*)" on the page$/, function (locator, done) {
        expect(element(by.css(locator)).isPresent()).to.eventually.equal(true).and.notify(done);
	});

	this.Then(/^I should not see "([^"]*)" on the page$/, function (locator, done) {
        expect(element(by.css(locator)).isPresent()).to.eventually.equal(false).and.notify(done);
	});

	this.Then("I should see a success message", function (done) {
		expect(element(by.css("#toast-container .toast.toast-success")).isPresent()).to.eventually.equal(true).and.notify(done);
	});

	this.Then("I should see a failure message", function (done) {
		expect(element(by.css("#toast-container .toast.toast-error")).isPresent()).to.eventually.equal(true).and.notify(done);
	});

    // pause test (helpful for debugging)
	this.Then('pause', function (page, done) {
		browser.pause();
	});
};
module.exports = commonStepDefinitionsWrapper;