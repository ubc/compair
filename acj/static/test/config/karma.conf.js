module.exports = function (config) {
  config.set({
    basePath: '../../',

    files: [
        'lib/angular/angular.js',
        'lib/jquery/dist/jquery.min.js',
        'lib/bootstrap/dist/js/bootstrap.min.js',
        'lib/angular-strap/dist/angular-strap.min.js',
		'lib/angular-route/angular-route.min.js',
		'lib/angular-resource/angular-resource.min.js',
		'lib/angular-cookies/angular-cookies.min.js',
        'lib/angular-mocks/angular-mocks.js',
		'lib/*.js',
		'modules/**/*.js',
    ],

    frameworks: ['jasmine'],

    autoWatch: true,

    browsers: ['Chrome'],

    junitReporter: {
      outputFile: 'test_out/unit.xml',
      suite: 'unit'
    }
  });
};