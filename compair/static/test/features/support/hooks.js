var hooks = function () {
    this.BeforeStep(function (step, callback) {
        browser.waitForAngular().then(() => callback());
    });

    this.Before(function (scenario, callback) {
        // https://github.com/angular/protractor/issues/2643
        browser.waitForAngularEnabled(true).then(() => callback());
    });

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

        // ensure cookies and local storage are cleared
        browser.manage().deleteAllCookies();
        browser.executeScript('window.sessionStorage.clear();');
        browser.executeScript('window.localStorage.clear();');

        // print any js errors
        browser.getCapabilities().then(function (cap) {
            // not supported by Firefox
            // https://github.com/seleniumhq/selenium/issues/1161
            if (cap && 'firefox' !== cap.get('browserName')) {
                browser.manage().logs().get('browser').then( function(browserLog) {
                    var browserErrorLogs = [];
                    browserLog.forEach(function (log) {
                        // error severity is high and not a ckeditor or pdf.js error
                        // (ckeditor doesn't always clean it self up fast enough with the tests current speed)
                        // (pdf.js also sometimes have problems with page load errors at this speed for some reason)
                        if (log.level.value > 900 &&
                                !log.message.match(/ckeditor\.js/g) &&
                                !log.message.match(/CWL_login_button\.gif/g) &&
                                log.message.indexOf("Uncaught TypeError: Cannot read property 'on' of undefined") == -1 &&
                                log.message.indexOf("Uncaught TypeError: Cannot read property 'unselectable' of null") == -1 &&
                                log.message.indexOf("Uncaught TypeError: Cannot read property 'getSelection' of undefined") == -1 &&
                                log.message.indexOf("TypeError: a is undefined") == -1 &&
                                log.message.indexOf("window.parent is null") == -1) {
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
            } else {
                console.error("Skipped browser log error check. Not supported.");
                callback();
            }
        });
    });
};

module.exports = hooks;