var env = require('../env.js');
var backEndMocks = require('../factories/http_backend_mocks.js');

exports.config = {
    //seleniumAddress: 'http://localhost:4444/wd/hub',
    //seleniumServerJar: '../../../../node_modules/protractor/selenium/selenium-server-standalone-2.47.1.jar',
    specs: ['../features/**/*.feature'],
    directConnect: true,
    //ignoreUncaughtExceptions: true,
    framework: 'custom',
    frameworkPath: require.resolve('protractor-cucumber-framework'),
    cucumberOpts: {
        require: ['../features/**/*.js']
    },
    capabilities: {
        'name': 'ComPAIR suite tests',
        'browserName': 'chrome',
        'loggingPrefs': {"browser": "SEVERE"},
        // Headless mode for firefox and chrome. Running tests with GUI may cause problems.
        // e.g. on Linux, Firefox hangs if minimized. Chrome hangs and fails randomly even when the browser is in focus
        // Also seems to solve some timing issues and no more browser.sleep at odd places.
        'chromeOptions': { args: [ "--headless" ] },
        'moz:firefoxOptions': { args: [ "--headless" ] },
    },
    onPrepare: function() {
        // disable angular and css animations so tests run faster
        var disableNgAnimate = function() {
            angular.module('disableNgAnimate', []).run(['$animate', function($animate) {
                $animate.enabled(false);
            }]);
        };
        var disableCssAnimate = function() {
            angular.module('disableCssAnimate', []).run(function() {
                var style = document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = '* {' +
                    '-webkit-transition: none !important;' +
                    '-moz-transition: none !important' +
                    '-o-transition: none !important' +
                    '-ms-transition: none !important' +
                    'transition: none !important' +
                    '}';
                document.getElementsByTagName('head')[0].appendChild(style);
            });
        };
        browser.addMockModule('disableNgAnimate', disableNgAnimate);
        browser.addMockModule('disableCssAnimate', disableCssAnimate);
        backEndMocks.build(browser);
        return browser.get(env.baseUrl);
    },
    baseUrl: env.baseUrl
};
