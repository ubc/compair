// Extends AngularJS-Toaster with default behaviours for info, success,
// warning, and error messages. The default AngularJS-Toaster is 'toaster', the
// customized version in this module is 'Toaster'. E.g. I want error messages
// to stay on the screen instead of fading away, so I add a error() method with
// 0 ms fade (0 disables it), and it can now be called with Toaster.error()

(function() {

var module = angular.module('ubc.ctlt.acj.toaster', 
	[
		'toaster'
	]
);

/***** Providers *****/
module.factory('Toaster', function($log, toaster) {
	// should be short, so don't need that much time
	toaster.success = function(title, msg) {
		this.pop("success", title, msg, 5000);
	};
	// give users more time to read these
	toaster.info = function(title, msg) {
		this.pop("info", title, msg, 10000);
	};
	toaster.warning = function(title, msg) {
		this.pop("warning", title, msg, 10000);
	};
	// Error messages will not automatically fade, will instead stay in place
	// until clicked to dismiss
	toaster.error = function(title, msg) {
		this.pop("error", title, msg, 0);
	};
	// Not sure what the best way to do this would be yet, but we can have 
	// preset error messages for certain errors. This is for any ajax requests
	// that fails.
	toaster.reqerror = function(title) {
		$log.error(title);
		// TODO Tell them what support to contact
		this.error(title, "Unable to connect to the server, this might be a server issue or your internet connection might be down. Please contact support if it looks to be a server issue.");
	};
	return toaster;
});

/***** Controllers *****/

// End anonymous function
})();
