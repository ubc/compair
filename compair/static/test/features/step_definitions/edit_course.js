// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editCourseStepDefinitionsWrapper = function () {
};
module.exports = editCourseStepDefinitionsWrapper;