var env = require('../env.js');

exports.config = {
    //seleniumAddress: 'http://localhost:4444/wd/hub',
	//seleniumServerJar: '../../../../node_modules/protractor/selenium/selenium-server-standalone-2.44.0.jar',
	sauceUser: process.env.SAUCE_USERNAME,
	sauceKey: process.env.SAUCE_ACCESS_KEY,
    specs: ['../features/**/*.feature'],
	framework: 'cucumber',
	multiCapabilities: [{
		'browserName': 'chrome',
		'tunnel-identifier': process.env.TRAVIS_JOB_NUMBER,
		'build': process.env.TRAVIS_BUILD_NUMBER,
		'name': 'acj suite tests',
		'version': '39',
		'selenium-version': '2.44.0'
	}, {
		'browserName': 'firefox',
		'tunnel-identifier': process.env.TRAVIS_JOB_NUMBER,
		'build': process.env.TRAVIS_BUILD_NUMBER,
		'name': 'acj suite tests',
		'version': '34',
		'selenium-version': '2.44.0'
	}],
    cucumberOpts: {
        format: 'pretty'
    },

	baseUrl: env.baseUrl
};