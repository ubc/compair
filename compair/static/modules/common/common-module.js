(function() {

var module = angular.module('ubc.ctlt.compair.common', []);

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

// based on https://gist.github.com/yrezgui/5653591
module.filter('filesize', function () {
    var units = [
        'bytes',
        'KB',
        'MB',
        'GB',
        'TB',
        'PB'
    ];

    return function( bytes, precision ) {
        precision = precision || 0;

        if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) {
            return;
        }

        var unit = 0;
        while (bytes >= 1024 && unit < units.length) {
             bytes /= 1024;
             unit++;
        }
        return bytes.toFixed(precision) + units[unit];
    };
});

module.filter('encodeURIComponent', function () {
    return window.encodeURIComponent;
});

})();
