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
module.factory('Toaster', ["toaster", function(toaster) {
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
    return toaster;
}]);

/***** Controllers *****/

// End anonymous function
})();
