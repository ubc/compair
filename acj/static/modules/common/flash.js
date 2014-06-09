// Module for generating flash messages

// Isolate this module's creation by putting it in an anonymous function
(function() {

// Create the module with a unique name.
var module = angular.module('ubc.ctlt.acj.common.flash', 
	['ubc.ctlt.acj.toaster']);

/***** Providers *****/
module.factory('flashService', function(Toaster) {
	return {
		flash: function (type, msg) {
			Toaster.info(msg);
		}		
	};
});

/***** Controllers *****/
// declare controllers here, e.g.:
// module.controller(...)

// End anonymous function
})();
