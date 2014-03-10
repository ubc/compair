// Module for generating flash messages

// Isolate this module's creation by putting it in an anonymous function
(function() {

// Create the module with a unique name.
var module = angular.module('ubc.ctlt.acj.common.flash', ['flash']);

/***** Providers *****/
module.factory('flashService', function(flash) {
	return {
		flash: function (type, msg) {
			type = 'alert alert-' + type + ' text-center';
			flash([{ level: type, text: msg}]);
		}		
	};
});

/***** Controllers *****/
// declare controllers here, e.g.:
// module.controller(...)

// End anonymous function
})();
