// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var viewHomeStepDefinitionsWrapper = function () {
    this.Then("I should see my courses with names:", function (data) {
        var list = data.hashes().map(function(item) {
            return item.name + " »";
        });

        return expect(element.all(by.css(".course-list a h3")).getText()).to.eventually.eql(list);
    });

    this.When("I filter home page courses by '$filter'", function (filter) {
        element(by.css("form.search-courses input")).sendKeys(filter);
        // force blur
        //return element(by.css("body")).click();
        // dont click on the body.  it may accidentially click on any button (depending on the browser window size)
        return;
    });

    this.Then("I should see '$numberString' courses", function (numberString) {
        var count = parseInt(numberString);
        return expect(element.all(by.css(".course-list a h3")).count()).to.eventually.equal(count);
    });

};

module.exports = viewHomeStepDefinitionsWrapper;