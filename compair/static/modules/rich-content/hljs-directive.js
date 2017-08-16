// Directives to integrate highlight js into AngularJS
(function() {

var module = angular.module('ubc.ctlt.compair.rich.content.highlightjs', []);

/***** Directives *****/
module.directive('hljs', function() {
    return function(scope, el, attrs, ctrl) {
        scope.$watch(attrs.hljs, function() {
            $(el[0]).find('pre code').each(function(i, block) {
                hljs.highlightBlock(block);
            });
        });
    };
});

// End anonymous function
})();
