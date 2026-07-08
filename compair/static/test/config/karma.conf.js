process.env.CHROME_BIN = require('puppeteer').executablePath()

var appWebpackConfig = require('../../../../webpack.config.js');

module.exports = function (config) {
    config.set({
        basePath: '../../',

        preprocessors: {
            'modules/**/*.html': ['ng-html2js'],
            'test/config/karma-entry.js': ['webpack']
        },

        files: [
            'lib/tincan/build/tincan.js',
            'test/config/karma-entry.js',
            'modules/**/*.html'
        ],

        webpack: {
            mode: appWebpackConfig.mode,
            module: appWebpackConfig.module,
            plugins: appWebpackConfig.plugins
        },

        frameworks: ['jasmine'],

        autoWatch: true,

        browsers: ['ChromeHeadless'],

        customLaunchers: {
            ChromeHeadless: {
                base: 'Chrome',
                flags: [
                    '--headless',
                    '--no-sandbox',
                    '--disable-gpu',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--remote-debugging-port=9222'
                ]
            }
        },

        junitReporter: {
            outputFile: 'test_out/unit.xml',
            suite: 'unit'
        }
    });
};
