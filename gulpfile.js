var gulp = require('gulp');
var bower = require('bower');
var bower = require('gulp-bower');
var wiredep = require('wiredep').stream;
var less = require('gulp-less');
var path = require('path');
var _ = require('lodash');
var karma = require('karma').server;

var karmaCommonConf = require('./acj/static/test/config/karma.conf.js');

// download Bower packages and copy them to the lib directory
gulp.task('bowerInstall', function() {
	var stream = bower()
		.pipe(gulp.dest('./acj/static/lib'));
	return stream;
});

// insert tags into index.html to include the libs downloaded by bower
gulp.task('bowerWiredep', ['bowerInstall'], function () {
	var stream = gulp.src('./acj/static/index.html')
		.pipe(wiredep({
			directory: './acj/static/lib'
		}))
		.pipe(gulp.dest('./acj/static/'));
	return stream;
});

// compile css
gulp.task('less', function () {
  gulp.src('./acj/static/*.less')
    .pipe(less({
      paths: [ path.join(__dirname, 'less', 'includes') ]
    }))
    .pipe(gulp.dest('./acj/static'));
});

/**
*  * Run test once and exit
*   */
gulp.task('test', function (done) {
      karma.start(_.assign({}, karmaCommonConf, {singleRun: true}), done);
});

/**
*  * Watch for file changes and re-run tests on each change
*   */
gulp.task('tdd', function (done) {
      karma.start(karmaCommonConf, done);
});

gulp.task("default", ['bowerInstall', 'bowerWiredep', 'less'], function(){});

