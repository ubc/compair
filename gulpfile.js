var gulp = require('gulp');
var bower = require('bower');
var bower = require('gulp-bower');
var wiredep = require('wiredep').stream;

// download Bower packages and copy them to the lib directory
gulp.task('bowerInstall', function() {
	bower().pipe(gulp.dest('./acj/static/lib'))
});

// insert tags into index.html to include the libs downloaded by bower
gulp.task('bowerWiredep', function () {
  gulp.src('./acj/static/index.html')
    .pipe(wiredep({
		directory: './acj/static/lib'
	}))
    .pipe(gulp.dest('./acj/static/'));
});


gulp.task("default", ['bowerInstall', 'bowerWiredep'], function(){
});

