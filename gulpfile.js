var gulp = require('gulp'),
	bower = require('gulp-bower'),
	wiredep = require('wiredep').stream,
	less = require('gulp-less'),
	concat = require('gulp-concat'),
	uglify = require('gulp-uglify'),
	htmlReplace = require('gulp-html-replace'),
	inject = require('gulp-inject'),
	mainBowerFiles = require('main-bower-files'),
	minifyCss = require('gulp-minify-css'),
	karma = require('karma').server,
	protractor = require('gulp-protractor').protractor,
	webdriver_standalone = require('gulp-protractor').webdriver_standalone,
	webdriver_update = require('gulp-protractor').webdriver_update,
	exec = require('child_process').exec,
	connect = require('gulp-connect');

var cssFilename = 'acj.css',
	jsLibsFilename = 'bowerJsLibs.js',
	karmaCommonConf = 'acj/static/test/config/karma.conf.js';

// download Bower packages and copy them to the lib directory
gulp.task('bowerInstall', function() {
	return bower()
		.pipe(gulp.dest('./acj/static/lib'));
});

// insert tags into index.html to include the libs downloaded by bower
gulp.task('bowerWiredep', ['bowerInstall'], function () {
	return gulp.src('./acj/static/index.html')
		.pipe(wiredep({directory: './acj/static/lib'}))
		.pipe(gulp.dest('./acj/static/'));
});

// compile css
gulp.task('less', function () {
  gulp.src('./acj/static/less/acj.less')
    .pipe(less())
	.pipe(minifyCss())
    .pipe(gulp.dest('./acj/static'));
});

gulp.task('prod_compile_minify_css', ['less'], function() {
	gulp.src('./acj/static/' + cssFilename)
		.pipe(minifyCss())
		.pipe(gulp.dest('./acj/static/'));
});
gulp.task('prod_minify_js_libs', function() {
	gulp.src(mainBowerFiles({"filter": /.*\.js/}))
		.pipe(concat(jsLibsFilename))
		.pipe(uglify())
		.pipe(gulp.dest('./acj/static/'));
});
gulp.task('prod', ['prod_minify_js_libs', 'prod_compile_minify_css'], function(){
	// modify includes to use the minified files
	gulp.src('./acj/static/index.html')
		.pipe(htmlReplace(
			{
				prod_minify_js_libs: jsLibsFilename,
				prod_compile_minify_css: cssFilename
			},
			{keepBlockTags: true}))
		.pipe(gulp.dest('./acj/static/'));
});

gulp.task('tracking', function() {
   gulp.src('./acj/static/index.html')
       .pipe(inject(gulp.src(['./acj/static/tracking.js']), {read: false, relative: true}))
       .pipe(gulp.dest('./acj/static/'));
});

/**
 * Watch for file changes and re-run tests on each change
 */
gulp.task('tdd', function (done) {
	karma.start({
		configFile: __dirname + '/' + karmaCommonConf
	}, done);
});

/**
 * Behavior driven development. This task run acceptance tests
 */
gulp.task('bdd', function (done) {
	gulp.src(["acj/static/test/features/*.feature"])
		.pipe(protractor({
			configFile: "acj/static/test/config/protractor_cucumber.js",
			args: ['--baseUrl', 'http://127.0.0.1:8080']
		}))
		.on('error', function (e) {
			throw e
		})
		.on('end', done);
});

/**
 * Run test once and exit
 */
gulp.task('test:unit', function (done) {
	karma.start({
		configFile: __dirname + '/' + karmaCommonConf,
		singleRun: true
	}, done);
});


/**
 * Run acceptance tests
 */
gulp.task('test:acceptance', ['webdriver_update', 'server:frontend', 'bdd'], function() {
	connect.serverClose();
});

/**
 * Run tests on ci
 */
gulp.task('test:ci', ['server:frontend'], function (done) {
	gulp.src(["acj/static/test/features/*.feature"])
		.pipe(protractor({
			configFile: "acj/static/test/config/protractor_saucelab.js",
			args: ['--baseUrl', 'http://127.0.0.1:8000']
		}))
		.on('error', function (e) {
			throw e
		})
		.on('end', function() {
			connect.serverClose();
			done();
		});
});


/**
 * Run backend server
 */
gulp.task('server:backend', function() {
	var proc = exec('PYTHONUNBUFFERED=1 python manage.py runserver -h 0.0.0.0');
	proc.stderr.on('data', function (data) {
		process.stderr.write(data);
	});
	proc.stdout.on('data', function (data) {
		process.stdio.write(data);
	});
});

/**
 * Run frontend server
 */
gulp.task('server:frontend', function() {
	connect.server({
		root: 'acj/static',
		livereload: false, // set to false, otherwise gulp will not exit
		middleware: function(connect, o) {
			return [ (function() {  // proxy api calls
				var url = require('url');
				var proxy = require('proxy-middleware');
				var options = url.parse('http://localhost:8081/api');
				options.route = '/api';
				return proxy(options);
			})(),
			(function() { // proxy CAS login
				var url = require('url');
				var proxy = require('proxy-middleware');
				var options = url.parse('http://localhost:8081/login');
				options.route = '/login';
				return proxy(options);
			})(),
			(function() { // proxy CAS logout
				var url = require('url');
				var proxy = require('proxy-middleware');
				var options = url.parse('http://localhost:8081/logout');
				options.route = '/logout';
				return proxy(options);
			})()];
		}
	});
});


/**
 * Downloads the selenium webdriver
 */
gulp.task('webdriver_update', webdriver_update);

/**
 * Start the standalone selenium server
 * NOTE: This is not needed if you reference the
 * seleniumServerJar in your protractor.conf.js
 */
gulp.task('webdriver_standalone', webdriver_standalone);


gulp.task("default", ['bowerInstall', 'bowerWiredep'], function(){});
