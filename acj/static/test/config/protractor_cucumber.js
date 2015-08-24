exports.config = {
    //seleniumAddress: 'http://localhost:4444/wd/hub',
	seleniumServerJar: '../../../../node_modules/protractor/selenium/selenium-server-standalone-2.45.0.jar',
    specs: ['../features/**/*.feature'],
    framework: 'cucumber',
    cucumberOpts: {
        format: 'pretty'
    }
};