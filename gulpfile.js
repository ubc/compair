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
    cleanCss = require('gulp-clean-css'),
    rev = require('gulp-rev'),
    exec = require('child_process').exec,
    sort = require('gulp-sort'), // gulp.src with wildcard doesn't give us a stable file order
    streamqueue = require('streamqueue'), // queued streams one by one
    templateCache = require('gulp-angular-templatecache');

    var cssFilenames = [
        './node_modules/bootstrap/dist/css/bootstrap.css',
        './node_modules/highlightjs/styles/foundation.css',
        './node_modules/angular-loading-bar/build/loading-bar.css',
        './node_modules/angularjs-toaster/toaster.css',
        './node_modules/chosen-js/chosen.css',
        './node_modules/chosen-bootstrap-theme/dist/chosen-bootstrap-theme.min.css',
        './compair/static/build/compair.css'
    ],
    targetCssFilename = 'compair.css',
    targetEmailCssFilename = 'email.css',
    jsLibsFilename = 'bowerJsLibs.js',
    jsFilename = 'compair.js',
    karmaCommonConf = 'compair/static/test/config/karma.conf.js';

// download Bower packages and copy them to the lib directory
gulp.task('bowerInstall', function() {
    return bower()
        .pipe(gulp.dest('./compair/static/lib'));
});

// insert tags into index.html to include the libs downloaded by bower
gulp.task('bowerWiredep', gulp.series('bowerInstall', function () {
    return gulp.src('./compair/static/index.html', {allowEmpty: true})
        .pipe(wiredep({directory: './compair/static/lib'}))
        .pipe(gulp.dest('./compair/static/'));
}));

gulp.task('copy_pdf_viewer_html_template', function() {
    return gulp.src(['./node_modules/pdf.js-viewer/viewer.html'])
        .pipe(gulp.dest('./compair/templates/static'));
});

// pdf.js-viewer isn't bundled by webpack (it's a standalone viewer, not part
// of the Angular app), so its runtime assets need to be copied to the exact
// path compair/api/__init__.py's route_pdf_viewer() expects in dev mode:
// url_for('static', filename='lib/pdf.js-viewer'). Bower used to populate
// this same path as a side effect of bowerInstall; this replaces that.
gulp.task('copy_pdf_viewer_dev_assets', function() {
    return gulp.src([
            './node_modules/pdf.js-viewer/pdf.js',
            './node_modules/pdf.js-viewer/pdf.worker.js',
            './node_modules/pdf.js-viewer/viewer.css',
            './node_modules/pdf.js-viewer/images/*',
            './node_modules/pdf.js-viewer/cmaps/*',
            './node_modules/pdf.js-viewer/locale/*',
        ], {base: './node_modules/pdf.js-viewer/'})
        .pipe(gulp.dest('./compair/static/lib/pdf.js-viewer'));
});

// tincanjs can't be webpack-bundled either (see webpack-entry.js for why),
// so it needs its own file for a plain <script> tag, like pdf.js-viewer.
// Copied to Bower's old path, not lib_extension/ (that's for hand-authored
// content with no package-manager source, which this isn't).
gulp.task('copy_tincan', function() {
    return gulp.src(['./node_modules/tincanjs/build/tincan.js'], {base: './node_modules/tincanjs/'})
        .pipe(gulp.dest('./compair/static/lib/tincan'));
});

// compile css
gulp.task('less', function () {
    return gulp.src('./compair/static/less/compair.less')
        .pipe(less())
        .pipe(gulp.dest('./compair/static/build'));
});
gulp.task('prod_compile_minify_css', gulp.series('less', function() {
    return gulp.src(cssFilenames)
        .pipe(cleanCss())
        .pipe(concat(targetCssFilename))
        .pipe(gulp.dest('./compair/static/build'));
}));

/*!
 * Bootstrap v3.3.7 (http://getbootstrap.com)
 * Copyright 2011-2016 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 */

gulp.task('email_less', function () {
    return gulp.src([
            './compair/static/less/email.less'
        ])
        .pipe(less())
        .pipe(gulp.dest('./compair/static/build'));
});
gulp.task('prod_compile_email_css', gulp.series('email_less', function() {
    return gulp.src('./compair/static/build/email.css')
        .pipe(cleanCss())
        .pipe(concat(targetEmailCssFilename))
        .pipe(gulp.dest('./compair/templates/static'));
}));
// No tool auto-discovers npm's resolved dependency tree the way Bower's did,
// so this is an explicit, ordered list instead - mirroring webpack-entry.js's
// require order. Uses each package's actual browser-ready file, not its
// declared "main" field: several (angular, angular-ui-bootstrap, etc.) point
// at a require()-based wrapper that throws in a plain concatenated script
// with no module system.
gulp.task('prod_minify_js_libs', function() {
    return gulp.src([
            './node_modules/jquery/dist/jquery.js',
            './node_modules/angular/angular.js',
            './node_modules/angular-animate/angular-animate.js',
            './node_modules/angular-resource/angular-resource.js',
            './node_modules/angular-route/angular-route.js',
            './node_modules/angular-sanitize/angular-sanitize.js',
            './node_modules/angular-http-auth/src/http-auth-interceptor.js',
            './node_modules/highlightjs/highlight.pack.js',
            './node_modules/angular-ckeditor-legacy/angular-ckeditor.js',
            './compair/static/lib_extension/ng-breadcrumbs/ng-breadcrumbs.js',
            './node_modules/angular-loading-bar/build/loading-bar.js',
            './node_modules/angularjs-toaster/toaster.js',
            './node_modules/chosen-js/chosen.jquery.js',
            './node_modules/angular-chosen-localytics/dist/angular-chosen.js',
            './node_modules/moment/moment.js',
            './node_modules/angular-moment/angular-moment.js',
            './node_modules/angular-file-upload/dist/angular-file-upload.js',
            './node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js',
            './node_modules/humanize-duration/humanize-duration.js',
            './node_modules/angular-timer/dist/angular-timer.js',
            './node_modules/lodash/lodash.js',
            './node_modules/ng-file-saver/dist/angular-file-saver.bundle.js',
            './node_modules/clipboard/lib/clipboard.js',
            './node_modules/ngclipboard/dist/ngclipboard.js',
            './node_modules/tincanjs/build/tincan.js',
            './node_modules/angular-uuid/angular-uuid.js',
            './node_modules/angular-local-storage/dist/angular-local-storage.js',
            './node_modules/angular-promise-extras/angular-promise-extras.js',
            './node_modules/ng-kaltura-player/index.js',
        ])
        .pipe(concat(jsLibsFilename))
        .pipe(uglify())
        .pipe(gulp.dest('./compair/static/build'));
});
gulp.task('prod_templatecache', function () {
    return gulp.src('./compair/static/modules/**/*.html')
        // we need a stable order to get the stable hash
        .pipe(sort())
        .pipe(templateCache({
            root: 'modules/'
        }))
        .pipe(gulp.dest('./compair/static/build'));
});
gulp.task('prod_copy_fonts', function () {
    // bootstrap fonts is loaded by bootstrap.css and default location is
    // ../fonts/
    return gulp.src('node_modules/bootstrap/fonts/*.*')
        .pipe(gulp.dest('compair/static/fonts/'));
});
gulp.task('prod_copy_images', function () {
    // chosen image is loaded by chosen.css and default location is
    // ./
    return gulp.src(['node_modules/chosen-js/*.png', './compair/static/img/*.png', './compair/static/img/*.ico'])
        .pipe(gulp.dest('compair/static/dist/'));
});
gulp.task('prod_minify_js', gulp.series('prod_templatecache', function() {
    var libs = gulp.src([
        './compair/static/compair-config.js',
        './compair/static/build/templates.js',
        // ckeditor plugins
        //'./bower_components/ckeditor/plugins/codesnippet/plugin.js',
        //'./bower_components/ckeditor/plugins/codesnippet/dialogs/codesnippet.js',
        //'./bower_components/ckeditor/plugins/codesnippet/lang/en.js',
        './compair/static/lib_extension/ckeditor/plugins/combinedmath/plugin.js',
        './compair/static/lib_extension/ckeditor/plugins/combinedmath/dialogs/combinedmath.js',
        //'./bower_components/ckeditor/plugins/widget/plugin.js',
        //'./bower_components/ckeditor/plugins/widget/lang/en.js',
        //'./bower_components/ckeditor/plugins/lineutils/plugin.js'
        './compair/static/lib_extension/ng-breadcrumbs/ng-breadcrumbs.js'
    ]);
    // we need to sort to generate a stable order so that we have a stable hash
    var modules = gulp.src('./compair/static/modules/**/*-module.js');
    var directives = gulp.src('./compair/static/modules/**/*-directive.js');
    var services = gulp.src('./compair/static/modules/**/*-service.js');

    return streamqueue(
        { objectMode: true },
        libs,
        modules.pipe(sort()),
        directives.pipe(sort()),
        services.pipe(sort())
    )
        .pipe(concat(jsFilename))
        .pipe(uglify())
        .pipe(gulp.dest('./compair/static/build'));
}));
gulp.task('prod_pdf_viewer_files', function() {
    return gulp.src([
            './node_modules/pdf.js-viewer/pdf.js',
            './node_modules/pdf.js-viewer/pdf.worker.js',
            './node_modules/pdf.js-viewer/viewer.css',
            './node_modules/pdf.js-viewer/images/*',
            './node_modules/pdf.js-viewer/cmaps/*',
            './node_modules/pdf.js-viewer/locale/*',
        ], {base: './node_modules/pdf.js-viewer/'})
        .pipe(gulp.dest('./compair/static/dist/pdf.js-viewer'));
});
gulp.task('prod', gulp.series('prod_minify_js_libs', 'prod_compile_minify_css', 'prod_compile_email_css',
        'prod_minify_js', 'prod_copy_fonts', 'prod_copy_images', 'prod_pdf_viewer_files', function() {
    return gulp.src([
            './compair/static/build/*.css',
            './compair/static/build/*.js',
            '!compair/static/build/templates.js',
        ], {base: './compair/static/build'})
        .pipe(rev())
        .pipe(gulp.dest('./compair/static/dist'))
        .pipe(rev.manifest())
        .pipe(gulp.dest('./compair/static/build'));
}));

/**
 * Watch for file changes and re-run tests on each change
 */
gulp.task('tdd', function (done) {
    karma.start({
        configFile: __dirname + '/' + karmaCommonConf
    }, done);
});

/**
 * Downloads the selenium webdriver
 */
gulp.task('webdriver_update', function(done) {
    var webdriver_update = require('gulp-protractor').webdriver_update;
    webdriver_update({}, done);
});

/**
 * Behavior driven development. This task runs acceptance tests
 */
gulp.task('bdd', gulp.series('webdriver_update', function (done) {
    var protractor = require('gulp-protractor').protractor;
    var connect = require('gulp-connect');
    gulp.src(["compair/static/test/features/*.feature"])
        .pipe(protractor({
            configFile: "compair/static/test/config/protractor_cucumber.js"
            // baseUrl is set through environment variable
            //args: ['--baseUrl', 'http://127.0.0.1:8080/app']
        }))
        .on('error', function (e) {
            throw e;
        })
        .on('end', function() {
            connect.serverClose();
        });
        done();
}));

/**
 * Run test once and exit
 */
gulp.task('test:unit', function (done) {
    var Server = require('karma').Server;
    new Server({
        configFile: __dirname + '/' + karmaCommonConf,
        singleRun: true
    }, done).start();
});

/**
 * Generate index.html
 */
gulp.task('generate_index', function(done) {
    var proc = exec('PYTHONUNBUFFERED=1 FLASK_APP=manage flask util generate-index');
    proc.stderr.on('data', function (data) {
        process.stderr.write(data);
        done();
    });
    proc.stdout.on('data', function (data) {
        process.stdout.write(data);
        done();
    });
});

/**
 * Delete generated index.html
 */
gulp.task('delete_index', function() {
    var del = require('del').sync; // use sync method, gulp doesn't seem to wait for async del
    return del([
        './compair/static/index.html'
    ]);
});

/**
 * Run frontend server
 */
gulp.task('server:frontend', gulp.series('generate_index', function(done) {
    var connect = require('gulp-connect');
    app = connect.server({
        port: 8700,
        root: 'compair/static',
        livereload: false, // set to false, otherwise gulp will not exit
        middleware: function(connect, o) {
            var url = require('url');
            var proxy = require('proxy-middleware');
            return [ (function() {  // rewrite all requests against /app to /
                // because generated index.html has a base /app
                var options = url.parse('http://localhost:8700/');
                options.route = '/app';
                return proxy(options);
            })()];
        }
    });
    // clean up after server close
    app.server.on('close', function() {
        gulp.task('start', gulp.series('delete_index'));
    });
    done();
}));

/**
 * Run acceptance tests
 */
gulp.task('test:acceptance', gulp.series('server:frontend', 'bdd', function(done) {
    done();
}));

/**
 * Run tests on ci
 */
gulp.task('_test:ci', function (done) {
    var protractor = require('gulp-protractor').protractor;
    var connect = require('gulp-connect');
    gulp.src(["compair/static/test/features/*.feature"])
        .pipe(protractor({
            configFile: "compair/static/test/config/protractor_saucelab.js"
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
gulp.task('test:ci', gulp.series('server:frontend', '_test:ci'));

/**
 * Run sauce connect
 */
gulp.task('sauce:connect', function(done) {
    var sauceConnectLauncher = require('sauce-connect-launcher');
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
 * Run acceptance tests
 */
gulp.task('_test:acceptance:sauce', gulp.series('sauce:connect', function(done) {
    var protractor = require('gulp-protractor').protractor;
    var connect = require('gulp-connect');
    var sauceConnectLauncher = require('sauce-connect-launcher');
    gulp.src(["compair/static/test/features/*.feature"])
        .pipe(protractor({
            configFile: "compair/static/test/config/protractor_saucelab_local.js",
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
}));
gulp.task('test:acceptance:sauce', gulp.series('server:frontend', '_test:acceptance:sauce'));

/**
 * Run backend server
 */
gulp.task('server:backend', function() {
    var proc = exec('PYTHONUNBUFFERED=1 FLASK_APP=compair flask run --host 0.0.0.0 --port 8080');
    proc.stderr.on('data', function (data) {
        process.stderr.write(data);
        done();
    });
    proc.stdout.on('data', function (data) {
        process.stdout.write(data);
        done();
    });
});


/**
 * Start the standalone selenium server
 * NOTE: This is not needed if you reference the
 * seleniumServerJar in your protractor.conf.js
 */
gulp.task('webdriver_standalone', function(done) {
    var webdriver_standalone = require('gulp-protractor').webdriver_standalone;
    webdriver_standalone(done);
    done();
});


gulp.task("default", gulp.series('copy_tincan', 'copy_pdf_viewer_dev_assets', 'copy_pdf_viewer_html_template', function(done){
    done();
}));
