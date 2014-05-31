// Karma configuration
// Generated on Tue Mar 11 2014 15:26:49 GMT-0400 (EDT)

module.exports = function(config) {

  var testFiles = [
    'public/js/requirejs-config.js',
    'test/unit/test-main.js',
    { pattern: 'dist/**/*.js', included: false },
    { pattern: 'public/js/**/*.js', included: false },
    { pattern: 'public/lib/**/*.js', included: false }
  ];

  if (process.argv[4]) { // TODO this should be more robust by checking the actual argument name
    testFiles.push({ pattern: 'test/unit/' + process.argv[4], included: false });
  } else {
    testFiles.push({ pattern: 'test/unit/**/*.js', included: false });
  }

  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['requirejs', 'mocha', 'chai'],


    // list of files / patterns to load in the browser
    files: testFiles,


    exclude: [

    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
    
    },


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],
    //browsers: ['Chrome'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    captureTimeout: 60000
  });
};
