// Entry point for the webpack bundle that replaces Bower + wiredep's
// individually-injected <script> tags. Requiring each library here is
// enough to register its Angular module / patch its global (see
// webpack.config.js's ProvidePlugin for the handful of libraries that
// only expose a global when there's no CommonJS `module` present).
//
// Not included here, on purpose:
// - tincanjs: its browser build assigns a bare top-level `var TinCan`
//   with no module-system detection at all. Wrapping it in a webpack
//   module would make that variable module-local instead of global,
//   silently breaking xAPI/Caliper tracking. Kept as a plain <script>
//   tag outside the bundle.
// - pdf.js-viewer: served as a standalone viewer, never bundled.
// - bootstrap / chosen-bootstrap-theme: CSS only.
// - CKEditor core: loaded from an external CDN <script> tag, unrelated
//   to this dependency migration.
// Explicit global (not just ProvidePlugin) because Angular checks
// window.jQuery itself at load time to pick jQuery vs its limited jqLite
// for angular.element - a property check ProvidePlugin can't satisfy.
window.jQuery = window.$ = require('jquery');

// CSS, in the same cascade order the old <link> tags used.
require('bootstrap/dist/css/bootstrap.css');
require('highlightjs/styles/foundation.css');
require('angular-loading-bar/build/loading-bar.css');
require('angularjs-toaster/toaster.css');
require('chosen-js/chosen.css');
require('chosen-bootstrap-theme/dist/chosen-bootstrap-theme.min.css');

require('angular');
require('angular-animate');
require('angular-resource');
require('angular-route');
require('angular-sanitize');
require('angular-http-auth');
require('highlightjs');
require('angular-ckeditor');
require('./lib_extension/ng-breadcrumbs/ng-breadcrumbs.js');
require('angular-loading-bar');
require('angularjs-toaster');
require('chosen-js');
require('angular-chosen-localytics');
require('angular-moment');
require('angular-file-upload');
require('angular-ui-bootstrap');
require('angular-timer');
// file-saver sets window.saveAs as a side effect at this version (2.0.4,
// matching what Bower resolved); ng-file-saver's own factory reads that
// global directly instead of require()'ing file-saver itself.
require('file-saver');
require('ng-file-saver');
require('ngclipboard');
require('angular-uuid');
require('angular-local-storage');
require('angular-promise-extras');
require('ng-kaltura-player');

require('./compair-config.js');

// *-module.js must load before *-directive.js/*-service.js: some of the
// latter extend an already-registered module via the angular.module('name')
// getter form (no deps array), which throws if that module doesn't exist
// yet. Folder order and order within each category don't matter otherwise.
var moduleFiles = require.context('./modules', true, /-module\.js$/);
moduleFiles.keys().forEach(moduleFiles);

var directiveAndServiceFiles = require.context('./modules', true, /-(directive|service)\.js$/);
directiveAndServiceFiles.keys().forEach(directiveAndServiceFiles);
