// Extends AngularJS-Toaster with default behaviours for info, success,
// warning, and error messages. The default AngularJS-Toaster is 'toaster', the
// customized version in this module is 'Toaster'. E.g. I want error messages
// to stay on the screen instead of fading away, so I add a error() method with
// 0 ms fade (0 disables it), and it can now be called with Toaster.error()

(function() {

var module = angular.module('ubc.ctlt.compair.toaster',
    [
        'toaster'
    ]
);

/***** Providers *****/
module.factory('Toaster', [ "$log", "toaster", function($log, toaster) {
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
    toaster.error = function(title, msg) {
        this.pop("error", title, msg, 10000);
    };
    // Not sure what the best way to do this would be yet, but we can have
    // preset error messages for certain errors. This is for any ajax requests
    // that fails.
    toaster.reqerror = function(title, response) {
        $log.warn("This method is deprecated. Default error handling should handle this.");
        $log.error(title);
        switch (response.status) {
            case 400:
                this.warning(title, response.data.error);
                break;
            case 401:
                this.warning(title, "Please log in again.");
                break;
            case 403:
                this.error(title, "Sorry, you don't have permission for this action.");
                break;
            default:
            // TODO Tell them what support to contact
                this.error(title, "Unable to connect. This might be a server issue or your connection might be down. Please contact support if the problem continues.");
        }
    };
    return toaster;
}]);

/***** Controllers *****/

// End anonymous function
})();
