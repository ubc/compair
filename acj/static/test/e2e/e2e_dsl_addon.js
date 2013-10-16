/*
 * angularjs e2e dsl doesn't work on contenteditable elements
 */
angular.scenario.dsl('contenteditable', function () {
    var chain = {};
    chain.enter = function (value) {
        return this.addFutureAction("contenteditable '" + this.name + "' enter '" + value + "'", function             ($window, $document, done) {
            var contenteditable = $document.elements(this.name);
            contenteditable.text(value);
            contenteditable.trigger('change');
            done();
        });
    };
    return function (name) {
        this.name = name;
        return chain;
    };
});

/**
 * Usage: confirmOK() sets window.confirm to return true when it is called in your application
 */
angular.scenario.dsl('confirmOK', function() {
    return function() {
        return this.addFutureAction('monkey patch window.confirm to return true', function($window, $document, done) {
            $window.confirm = function() {return true;};
            done();
        });
    };
});


/**
 * Usage: confirmCancel() sets window.confirm to return false when it is called in your application
 */
angular.scenario.dsl('confirmCancel', function() {
    return function() {
        return this.addFutureAction('monkey patch window.confirm to return false', function($window, $document, done) {
            $window.confirm = function() {return false;};
            done();
        });
    };
});