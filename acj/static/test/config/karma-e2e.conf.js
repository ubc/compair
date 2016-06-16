module.exports = function (config) {
  config.set({
    basePath: '../',

    files: [
            'e2e/*.js'
    ],

    frameworks: ['ng-scenario', 'jasmine'],

    browsers: ['PhantomJS'],

    singleRun: true,

    proxies: {
      '/': 'http://127.0.0.1:5000/'
    },

    urlRoot: '/_karma_/',

    reporters: ['dots', 'junit'],

    junitReporter: {
      outputFile: 'test_out/e2e.xml',
      suite: 'e2e'
    }
  });
};