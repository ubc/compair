// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewCourseStepDefinitionsWrapper = function () {
	this.When(/^I select the course named "([^"]*)"$/, function (courseName, done) {
		return element(by.cssContainingText(".course-list a h3", courseName)).click();
	});
    
	this.Then(/^I should see my questions with names:$/, function (data, done) {
		var list = data.hashes().map(function(item) {
            // add the " »" that is displayed on the page
            return item.name + " »";
        });
        
        expect(element.all(by.css(".media-body a h3")).getText()).to.eventually.eql(list).and.notify(done);
	});
    
	this.When(/^I filter course page questions by "([^"]*)"$/, function (filter, done) {
		// Firefox soemtimes has trouble with selects 
		if (browser.browserName == "firefox") {
			element(by.css("form.searchCourse select")).click();
		}
        element(by.css("form.searchCourse select")).sendKeys(filter);
		
		// force blur
		element(by.css("h2")).click();
		
		var loadingText = by.cssContainingText('h2', filter);
		browser.wait(function() {
			return browser.isElementPresent(loadingText);
		}, 1000);
	
	    expect(element(loadingText).isPresent()).to.eventually.equal(true).and.notify(done);
	});
    
	this.Then(/^I should see "([^"]*)" questions$/, function (numberString, done) {
        var count = parseInt(numberString);
        
        expect(element.all(by.css(".media-body a h3")).count()).to.eventually.equal(count).and.notify(done);
	});
};

module.exports = viewCourseStepDefinitionsWrapper;