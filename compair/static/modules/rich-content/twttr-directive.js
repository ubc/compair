// Directives to integrate highlight js into AngularJS
(function() {

var module = angular.module('ubc.ctlt.compair.rich.content.twttr', []);

/***** Directives *****/
module.directive('twttr',
    ["$timeout",
    function($timeout)
    {
        return function(scope, el, attrs, ctrl) {
            scope.load = function() {
                $timeout(function () {
                    twttr.widgets.load();
                }, 1);
            }

            scope.$watch(attrs.twttr, function() {
                scope.load();
            });
            scope.load();
        };
    }
]);

// End anonymous function
})();
