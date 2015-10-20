exports.config = {
    //seleniumAddress: 'http://localhost:4444/wd/hub',
	seleniumServerJar: '../../../../node_modules/protractor/selenium/selenium-server-standalone-2.47.1.jar',
    specs: ['../features/**/*.feature'],
    framework: 'cucumber',
    cucumberOpts: {
        format: 'pretty'
    },
    multiCapabilities: [ {
        'browserName': 'firefox',
        'tunnel-identifier': process.env.TRAVIS_JOB_NUMBER,
        'build': process.env.TRAVIS_BUILD_NUMBER,
        'name': 'acj suite tests',
        'version': '34',
        'selenium-version': '2.44.0'
    }],
};