/**
 * Note:
 *   gulp prod: is trying to build a minimal number of assets and they can
 *              be uploaded to a CDN. If a resource (css/js) has any dependencies,
 *              they should be uploaded to CDN as well. E.g. bootstrap is loading
 *              a font, which needs to be uploaded.
 */
var gulp = require('gulp'),
    bower = require('gulp-bower'),
    wiredep = require('wiredep').stream,
    less = require('gulp-less'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify'),
    htmlReplace = require('gulp-html-replace'),
    inject = require('gulp-inject'),
    mainBowerFiles = require('main-bower-files'),
    cleanCss = require('gulp-clean-css'),
    rev = require('gulp-rev'),
    Server = require('karma').Server,
    protractor = require('gulp-protractor').protractor,
    webdriver_standalone = require('gulp-protractor').webdriver_standalone,
    webdriver_update = require('gulp-protractor').webdriver_update,
    exec = require('child_process').exec,
    connect = require('gulp-connect'),
    sauceConnectLauncher = require('sauce-connect-launcher'),
    del = require('del').sync, // use sync method, gulp doesn't seem to wait for async del
    sort = require('gulp-sort'), // gulp.src with wildcard doesn't give us a stable file order
    templateCache = require('gulp-angular-templatecache');

var cssFilenames = [
        './acj/static/lib/bootstrap/dist/css/bootstrap.css',
        './acj/static/lib/fontawesome/css/font-awesome.css',
        './acj/static/lib/highlightjs/styles/foundation.css',
        './acj/static/lib/angular-loading-bar/build/loading-bar.css',
        './acj/static/lib/AngularJS-Toaster/toaster.css',
        './acj/static/build/acj.css'
    ],
    targetCssFilename = 'acj.css',
    jsLibsFilename = 'bowerJsLibs.js',
    jsFilename = 'acj.js',
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
    return gulp.src('./acj/static/less/acj.less')
        .pipe(less())
        .pipe(gulp.dest('./acj/static/build'));
});

gulp.task('prod_compile_minify_css', ['less'], function() {
    return gulp.src(cssFilenames)
        .pipe(cleanCss())
        .pipe(concat(targetCssFilename))
        .pipe(gulp.dest('./acj/static/build'));
});
gulp.task('prod_minify_js_libs', function() {
    return gulp.src(mainBowerFiles({"filter": /.*\.js/}))
        .pipe(sort())
        .pipe(concat(jsLibsFilename))
        .pipe(uglify())
        .pipe(gulp.dest('./acj/static/build'));
});
gulp.task('prod_templatecache', function () {
    return gulp.src('./acj/static/modules/**/*.html')
        // we need a stable order to get the stable hash
        .pipe(sort())
        .pipe(templateCache({
            root: 'modules/'
        }))
        .pipe(gulp.dest('./acj/static/build'));
});
gulp.task('prod_copy_fonts', function () {
	// bootstrap fonts is loaded by bootstrap.css and default location is
    // ../fonts/
    return gulp.src('bower_components/bootstrap/fonts/*.*')
        .pipe(gulp.dest('acj/static/fonts/'));
});
gulp.task('prod_minify_js', ['prod_templatecache'], function() {
    return gulp.src([
        './acj/static/acj-config.js',
        './acj/static/modules/**/*-module.js',
        './acj/static/modules/**/*-directive.js',
        './acj/static/modules/**/*-directives.js',
        './acj/static/modules/**/*-service.js',
        './acj/static/modules/common/pdf.js',
        './acj/static/build/templates.js',
        // ckeditor plugins
        './bower_components/ckeditor/plugins/codesnippet/plugin.js',
        './bower_components/ckeditor/plugins/codesnippet/dialogs/codesnippet.js',
        './bower_components/ckeditor/plugins/codesnippet/lang/en.js',
        './acj/static/lib_extension/ckeditor/plugins/combinedmath/plugin.js',
        './acj/static/lib_extension/ckeditor/plugins/combinedmath/dialogs/combinedmath.js',
        './bower_components/ckeditor/plugins/widget/plugin.js',
        './bower_components/ckeditor/plugins/widget/lang/en.js',
        './bower_components/ckeditor/plugins/lineutils/plugin.js'
    ])
        // we need to sort to generate a stable order so that we have a stable hash
        .pipe(sort())
        .pipe(concat(jsFilename))
        .pipe(uglify())
        .pipe(gulp.dest('./acj/static/build'));
});
gulp.task('revision', ['prod_minify_js_libs', 'prod_compile_minify_css', 'prod_minify_js', 'prod_copy_fonts'], function() {
    return gulp.src(['./acj/static/build/*.css', './acj/static/build/*.js', '!acj/static/build/templates.js'])
        .pipe(rev())
        .pipe(gulp.dest('./acj/static/dist'))
        .pipe(rev.manifest())
        .pipe(gulp.dest('./acj/static/build'));
});
gulp.task('prod', ['revision'], function(){
    var manifest = require("./acj/static/build/rev-manifest.json");
    // modify includes to use the minified files
    return gulp.src('./acj/static/index.html')
        .pipe(htmlReplace(
            {
                prod_minify_js_libs: 'dist/' + manifest[jsLibsFilename],
                prod_minify_js: 'dist/' + manifest[jsFilename],
                prod_compile_minify_css: 'dist/' + manifest[targetCssFilename]
            },
            {keepBlockTags: true}))
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
 * Behavior driven development. This task runs acceptance tests
 */
gulp.task('bdd', ['webdriver_update'], function (done) {
    gulp.src(["acj/static/test/features/*.feature"])
        .pipe(protractor({
            configFile: "acj/static/test/config/protractor_cucumber.js"
            // baseUrl is set through environment variable
            //args: ['--baseUrl', 'http://127.0.0.1:8080/app']
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
    new Server({
        configFile: __dirname + '/' + karmaCommonConf,
        singleRun: true
    }, done).start();
});

/**
 * Generate index.html
 */
gulp.task('generate_index', function() {
    var proc = exec('PYTHONUNBUFFERED=1 python manage.py util generate_index');
    proc.stderr.on('data', function (data) {
        process.stderr.write(data);
    });
    proc.stdout.on('data', function (data) {
        process.stdout.write(data);
    });
});

/**
 * Delete generated index.html
 */
gulp.task('delete_index', function() {
    return del([
        './acj/static/index.html'
    ]);
});

/**
 * Run acceptance tests
 */
gulp.task('test:acceptance', ['server:frontend', 'bdd'], function() {
    connect.serverClose();
});

/**
 * Run tests on ci
 */
gulp.task('test:ci', ['server:frontend'], function (done) {
    gulp.src(["acj/static/test/features/*.feature"])
        .pipe(protractor({
            configFile: "acj/static/test/config/protractor_saucelab.js"
            // baseUrl is set through environment variable
            //args: ['--baseUrl', 'http://127.0.0.1:8000']
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
 * Run acceptance tests
 */
gulp.task('test:acceptance:sauce', ['server:frontend', 'sauce:connect'], function(done) {
    gulp.src(["acj/static/test/features/*.feature"])
        .pipe(protractor({
            configFile: "acj/static/test/config/protractor_saucelab_local.js",
            args: ['--baseUrl', 'http://127.0.0.1:8000']
        }))
        .on('error', function (e) {
            throw e
        })
        .on('end', function() {
            connect.serverClose();
            sauceConnectLauncher.clean();
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
        process.stdout.write(data);
    });
});

/**
 * Run frontend server
 */
gulp.task('server:frontend', ['generate_index'], function(done) {
    app = connect.server({
        root: 'acj/static',
        livereload: false, // set to false, otherwise gulp will not exit
        middleware: function(connect, o) {
            var url = require('url');
            var proxy = require('proxy-middleware');
            return [ (function() {  // rewrite all requests against /app to /
                // because generated index.html has a base /app
                var options = url.parse('http://localhost:8080/');
                options.route = '/app';
                return proxy(options);
            })(),
            (function() {  // proxy api calls
                var options = url.parse('http://localhost:8081/api');
                options.route = '/api';
                return proxy(options);
            })(),
            (function() { // proxy CAS login
                var options = url.parse('http://localhost:8081/login');
                options.route = '/login';
                return proxy(options);
            })(),
            (function() { // proxy CAS logout
                var options = url.parse('http://localhost:8081/logout');
                options.route = '/logout';
                return proxy(options);
            })()];
        }
    });
	// clean up after server close
    app.server.on('close', function() {
        gulp.start('delete_index');
        done();
    });
});

/**
 * Run sauce connect
 */
gulp.task('sauce:connect', function(done) {
    // auto kills on process end
    sauceConnectLauncher({
        username: process.env.SAUCE_USERNAME,
        accessKey: process.env.SAUCE_ACCESS_KEY,
        verbose: true
    }, function (err, sauceConnectProcess) {
        if (err) {
            console.error(err.message);
            return;
        }
        done();
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
