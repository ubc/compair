var env = require('../env.js');

exports.config = {
    //seleniumAddress: 'http://localhost:4444/wd/hub',
    //seleniumServerJar: '../../../../node_modules/protractor/selenium/selenium-server-standalone-2.44.0.jar',
    sauceUser: process.env.SAUCE_USERNAME,
    sauceKey: process.env.SAUCE_ACCESS_KEY,
    specs: ['../features/**/*.feature'],
    framework: 'cucumber',
    multiCapabilities: [{
        'browserName': process.env.TEST_BROWSER_NAME,
        'tunnel-identifier': process.env.TRAVIS_JOB_NUMBER,
        'build': process.env.TRAVIS_BUILD_NUMBER,
        'name': 'acj suite tests',
        'version': process.env.TEST_BROWSER_VERSION,
        'selenium-version': '2.52.0',
        'maxDuration': 3600 // 1 hour
    }],
    cucumberOpts: {
        format: 'pretty'
    },

    baseUrl: env.baseUrl
};