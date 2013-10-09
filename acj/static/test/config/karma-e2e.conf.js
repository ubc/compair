module.exports = function (config) {
  config.set({
    basePath: '../../',

    files: [
            'test/e2e/*.js'
    ],

    frameworks: ['ng-scenario', 'jasmine'],

    autoWatch: true,

    browsers: ['Firefox'],

    singleRun: false,

    proxies: {
      '/': 'http://127.0.0.1:5000/'
    },

    urlRoot: '/_karma_/',
    
    junitReporter: {
      outputFile: 'test_out/e2e.xml',
      suite: 'e2e'
    }
  });
};