// Directives to integrate mathjax into AngularJS
//
// Code from:
// https://github.com/ViktorQvarfordt/AngularJS-MathJax-Directive
// Unfortunately, it's not Bower enabled, so have to manually include it
(function() {

var module = angular.module('ubc.ctlt.compair.rich.content.mathjax', []);

/***** Directives *****/
// add the css and elements required to show bootstrap's validation feedback
// requires the parameter form-control, which passes in the input being validated
module.directive('mathjax', function() {
    return function(scope, el, attrs, ctrl) {
      scope.$watch(attrs.mathjax, function() {
        MathJax.Hub.Queue(['Typeset', MathJax.Hub, el[0]]);
      });
    };
});

// End anonymous function
})();
