var hooks = function () {
    this.After(function (scenario, callback) {
        // logout (directly uses controller to skip potential UI click issues)
        browser.executeScript(function() {
            var LogoutController = angular.element($("[ng-controller='LogoutController']"));
            if (LogoutController && LogoutController.scope()) {
                LogoutController.scope().logout();
            }
        });

        // clear toasters to help clean up
        browser.executeScript(function() {
            var injector = angular.element(document).injector();
            var Toaster = injector.get('Toaster');
            if (Toaster) {
                Toaster.clear();
            }
        });

        // ensure cookies are cleared
        browser.manage().deleteAllCookies();

        // print any js errors
        browser.manage().logs().get('browser').then( function(browserLog) {
            var browserErrorLogs = [];
            browserLog.forEach(function (log) {
                // error severity is high and not a ckeditor error
                // (ckeditor doesn't always clean it self up fast enough with the tests current speed)
                if (log.level.value > 900 && !log.message.match(/lib\/ckeditor\/ckeditor\.js/g)) {
                    browserErrorLogs.push(log)
                }
            });

            if(browserErrorLogs.length > 0) {
                console.error('browser errors:');
                browserErrorLogs.forEach(function (log) {
                    console.error(log.message);
                });
                callback(new Error("Browser Errors"));
            } else {
                callback();
            }
        });
    });
};

module.exports = hooks;