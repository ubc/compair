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
require('ng-file-saver');
require('ngclipboard');
require('angular-uuid');
require('angular-local-storage');
require('angular-promise-extras');
require('ng-kaltura-player');

require('./compair-config.js');

// App modules/directives/services. Folder order and order *within* each
// category don't matter (dev's hand-written list and prod's gulpfile.js
// glob already use two different orders there, and both work) - but
// *-module.js must load before *-directive.js/*-service.js, since some
// directives/services extend an already-registered module via the
// angular.module('name') getter form (no deps array), which throws
// immediately if that module hasn't been created yet.
var moduleFiles = require.context('./modules', true, /-module\.js$/);
moduleFiles.keys().forEach(moduleFiles);

var directiveAndServiceFiles = require.context('./modules', true, /-(directive|service)\.js$/);
directiveAndServiceFiles.keys().forEach(directiveAndServiceFiles);
