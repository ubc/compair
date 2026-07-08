/**
 * Note:
 *   gulp prod: is trying to build a minimal number of assets and they can
 *              be uploaded to a CDN. If a resource (css/js) has any dependencies,
 *              they should be uploaded to CDN as well. E.g. bootstrap is loading
 *              a font, which needs to be uploaded.
 */
var gulp = require('gulp'),
    less = require('gulp-less'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify'),
    htmlReplace = require('gulp-html-replace'),
    inject = require('gulp-inject'),
    cleanCss = require('gulp-clean-css'),
    rev = require('gulp-rev'),
    exec = require('child_process').exec,
    sort = require('gulp-sort'), // gulp.src with wildcard doesn't give us a stable file order
    templateCache = require('gulp-angular-templatecache');

var targetEmailCssFilename = 'email.css',
    jsFilename = 'compair.js',
    karmaCommonConf = 'compair/static/test/config/karma.conf.js';

gulp.task('copy_pdf_viewer_html_template', function() {
    return gulp.src(['./node_modules/pdf.js-viewer/viewer.html'])
        .pipe(gulp.dest('./compair/templates/static'));
});

// pdf.js-viewer isn't bundled by webpack (it's a standalone viewer, not part
// of the Angular app), so its runtime assets need to be copied to the exact
// path compair/api/__init__.py's route_pdf_viewer() expects in dev mode:
// url_for('static', filename='lib/pdf.js-viewer').
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
// Vendor CSS (bootstrap, highlightjs, chosen, etc.) is bundled by webpack
// (see webpack-entry.js) - this only compiles the app's own stylesheet.
gulp.task('prod_compile_minify_css', gulp.series('less', function() {
    return gulp.src('./compair/static/build/compair.css')
        .pipe(cleanCss())
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
// compair-config.js, ng-breadcrumbs.js, and every *-module/-directive/-service.js
// file are bundled by webpack (see webpack-entry.js) - this only builds the
// leftovers webpack doesn't handle: the angular $templateCache and the
// ckeditor combinedmath plugin (a CKEditor plugin, not an Angular module).
gulp.task('prod_minify_js', gulp.series('prod_templatecache', function() {
    return gulp.src([
        './compair/static/build/templates.js',
        './compair/static/lib_extension/ckeditor/plugins/combinedmath/plugin.js',
        './compair/static/lib_extension/ckeditor/plugins/combinedmath/dialogs/combinedmath.js'
    ])
        .pipe(concat(jsFilename))
        .pipe(uglify())
        .pipe(gulp.dest('./compair/static/build'));
}));
// tincanjs can't be webpack-bundled (see webpack-entry.js), so it needs its
// own delivery path. This copies the plain file into build/ so the rev()
// step at the end of prod picks it up and hashes it into dist/ -
// copy_tincan above only covers dev mode's static url, not CDN deployments
// (ASSET_LOCATION=cloud), which only upload what's in dist/.
gulp.task('prod_copy_tincan', function() {
    return gulp.src(['./node_modules/tincanjs/build/tincan.js'])
        .pipe(gulp.dest('./compair/static/build'));
});
// webpack emits font/image files referenced via url() in the vendor CSS it
// bundles (e.g. bootstrap's @font-face files, chosen's sprite pngs) into
// build/ under its own content-hashed names - webpack-bundle.css already has
// those exact names baked into its url() references. rev() below only globs
// build/*.js and build/*.css, so these never reach dist/ on their own, and
// re-hashing them through rev() would break the reference a second time
// (rev would rename them, but the CSS's url() would still point at the
// original webpack-generated name). So they're copied verbatim instead -
// same pattern as prod_copy_fonts/prod_copy_images, just for webpack's own
// build output rather than a node_modules source.
gulp.task('prod_copy_webpack_assets', function() {
    return gulp.src([
            './compair/static/build/*',
            '!./compair/static/build/*.js',
            '!./compair/static/build/*.css',
            '!./compair/static/build/*.json',
            '!./compair/static/build/*.txt',
        ])
        .pipe(gulp.dest('./compair/static/dist'));
});
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
gulp.task('prod', gulp.series('prod_compile_minify_css', 'prod_compile_email_css',
        'prod_minify_js', 'prod_copy_fonts', 'prod_copy_images', 'prod_pdf_viewer_files', 'prod_copy_tincan',
        'prod_copy_webpack_assets', function() {
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
