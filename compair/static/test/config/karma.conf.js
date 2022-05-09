process.env.CHROME_BIN = require('puppeteer').executablePath()

module.exports = function (config) {
    var wiredep = require('wiredep');
    var bowerFiles = wiredep({devDependencies: true, cwd: __dirname + '/../../../..'})['js'];
    config.set({
        basePath: '../../',

        preprocessors: {
            'modules/**/*.html': ['ng-html2js']
        },

        files: bowerFiles.concat([
            'modules/**/*-module.js',
            'modules/**/*.js',
            'modules/**/*.html',
            'compair-config.js',
            'test/helpers/*.js'
        ]),

        frameworks: ['jasmine'],

        autoWatch: true,

        browsers: ['ChromeHeadless'],

        junitReporter: {
            outputFile: 'test_out/unit.xml',
            suite: 'unit'
        }
    });
};
