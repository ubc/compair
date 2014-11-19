var gulp = require('gulp'),
	bower = require('gulp-bower'),
	wiredep = require('wiredep').stream,
	less = require('gulp-less'),
	concat = require('gulp-concat'),
	uglify = require('gulp-uglify'),
	htmlReplace = require('gulp-html-replace'),
	mainBowerFiles = require('main-bower-files'),
	minifyCss = require('gulp-minify-css'),
	_ = require('lodash'),
	karma = require('karma').server,
	karmaCommonConf = require('./acj/static/test/config/karma.conf.js');

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

var cssFilename = 'acj.css';
var jsLibsFilename = 'bowerJsLibs.js';
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

gulp.task("default", ['bowerInstall', 'bowerWiredep'], function(){});

