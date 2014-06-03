var gulp = require('gulp');
var bower = require('bower');
var bower = require('gulp-bower');
var wiredep = require('wiredep').stream;

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


gulp.task("default", ['bowerInstall', 'bowerWiredep'], function(){});

