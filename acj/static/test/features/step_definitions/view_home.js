// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewHomeStepDefinitionsWrapper = function () {
    this.Then(/^I should see my courses with names:$/, function (data, done) {
        var list = data.hashes().map(function(item) {
            return item.name + " ("+item.year+" "+item.term+")";
        });

        expect(element.all(by.css(".course-list a h3")).getText()).to.eventually.eql(list).and.notify(done);
    });

    this.When(/^I filter home page courses by "([^"]*)"$/, function (filter, done) {
        element(by.css("form.search-courses input")).sendKeys(filter);
        // force blur
        element(by.css("body")).click();

        done();
    });

    this.Then(/^I should see "([^"]*)" courses$/, function (numberString, done) {
        var count = parseInt(numberString);

        expect(element.all(by.css(".course-list a h3")).count()).to.eventually.equal(count).and.notify(done);
    });

};

module.exports = viewHomeStepDefinitionsWrapper;