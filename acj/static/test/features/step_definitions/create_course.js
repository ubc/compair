// Use the external Chai As Promised to deal with resolving promises in
// expectations.
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

// Chai expect().to.exist syntax makes default jshint unhappy.
// jshint expr:true

var createCourseStepDefinitionsWrapper = function () {
    
};
module.exports = createCourseStepDefinitionsWrapper;