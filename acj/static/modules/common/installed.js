// A service to check to see if the application has been installed
// An example of how to create functionally isolated modules in Angular for
// organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

// Create the module with a unique name
// The module needs a unique name that prevents conflicts with 3rd party modules
// We're using "ubc.ctlt.acj" as the project's prefix, followed by the module 
// name.
var module = angular.module('ubc.ctlt.acj.common.installed', ['ngResource']);

/***** Providers *****/
module.factory('isInstalled', function($resource) {
	return $resource( '/isinstalled' );
});

/***** Controllers *****/
// TODO declare controllers here, e.g.:
// module.controller(...)

// End anonymous function
})();
