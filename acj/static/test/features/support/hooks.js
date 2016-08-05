var hooks = function () {
    this.After(function (scenario, callback) {
        // logout (directly uses controller to skip potential UI click issues)
        browser.executeScript(function(fixtureName) {
            var LogoutController = angular.element($("[ng-controller='LogoutController']"));
            if (LogoutController && LogoutController.scope()) {
                LogoutController.scope().logout();
            }
        });

        // clear toasters to help clean up
        browser.executeScript(function(fixtureName) {
            var injector = angular.element(document).injector();
            var Toaster = injector.get('Toaster');
            if (Toaster) {
                Toaster.clear();
            }
        });

        // ensure cookies are cleared
        browser.manage().deleteAllCookies().then(function () {
            callback();
        });
    });
};

module.exports = hooks;