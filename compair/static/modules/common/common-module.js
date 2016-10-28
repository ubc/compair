(function() {

var module =angular.module('ubc.ctlt.compair.common', []);

module.filter("emptyToEnd", function () {
    return function (array, key, reversed) {
        if(!angular.isArray(array)) return;
        reversed = reversed || false;
        var present = array.filter(function (item) {
            return item[key];
        });
        var empty = array.filter(function (item) {
            return !item[key]
        });
        return reversed ? empty.concat(present) : present.concat(empty);
    };
});

})();
