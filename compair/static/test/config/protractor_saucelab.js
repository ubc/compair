var env = require('../env.js');
var backEndMocks = require('../factories/http_backend_mocks.js');

exports.config = {
    sauceUser: process.env.SAUCE_USERNAME,
    sauceKey: process.env.SAUCE_ACCESS_KEY,
    sauceBuild: process.env.TRAVIS_BUILD_NUMBER,
    specs: ['../features/**/*.feature'],
    framework: 'custom',
    frameworkPath: require.resolve('protractor-cucumber-framework'),
    cucumberOpts: {
        require: ['../features/**/*.js']
    },
    capabilities: {
        'name': 'ComPAIR suite tests',
        'platform': process.env.TEST_BROWSER_PLATFORM,
        'browserName': process.env.TEST_BROWSER_NAME,
        'version': process.env.TEST_BROWSER_VERSION,
        'tunnel-identifier': process.env.TRAVIS_JOB_NUMBER,
        'maxDuration': 3600, // 1 hour
        'loggingPrefs': {"browser": "SEVERE"},
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
        return browser.get(env.baseUrl, 20000);
    },
    baseUrl: env.baseUrl,
    allScriptsTimeout: 20000,
    getPageTimeout: 15000
};
