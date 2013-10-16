module.exports = function (config) {
  config.set({
    basePath: '../../',

    files: [
		'http://ajax.googleapis.com/ajax/libs/angularjs/1.2.0-rc.2/angular.js',      
		'http://ajax.googleapis.com/ajax/libs/jquery/1.10.1/jquery.min.js',
		'https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
		'http://ajax.googleapis.com/ajax/libs/angularjs/1.2.0-rc.2/angular.js',
		'http://netdna.bootstrapcdn.com/bootstrap/3.0.0/js/bootstrap.min.js',
		'http://cdnjs.cloudflare.com/ajax/libs/angular-strap/0.7.4/angular-strap.min.js',
		'https://ajax.googleapis.com/ajax/libs/angularjs/1.2.0-rc.2/angular-route.min.js',
		'http://ajax.googleapis.com/ajax/libs/angularjs/1.2.0-rc.2/angular-resource.min.js',
		'http://ajax.googleapis.com/ajax/libs/angularjs/1.2.0-rc.2/angular-cookies.min.js',
		//'http://code.angularjs.org/1.2.0-rc.2/angular-scenario.js',
		'http://code.angularjs.org/1.2.0-rc.2/angular-mocks.js',
		'http://rangy.googlecode.com/svn/trunk/currentrelease/rangy-core.js',
		'http://cdn.jsdelivr.net/intro.js/0.5.0/intro.min.js',		
		'lib/*.js',
		'ngtable/*.js',
		{pattern: 'ngtable/*.map', watched: false, included: false, served: true},
		'*.js',
		'test/unit/**/*.js'
    ],

    frameworks: ['jasmine'],

    autoWatch: true,

    browsers: ['Firefox'],

    junitReporter: {
      outputFile: 'test_out/unit.xml',
      suite: 'unit'
    }
  });
};