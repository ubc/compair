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

module.directive('ckeditorHtmlContent',
    ['$sce',
    function ($sce)
    {
        return {
            restrict: 'E',
            scope: {
                htmlContent: '='
            },
            link: function(scope, element, attrs) {
                scope.trustedContent = [];

                scope.$watch('htmlContent', function(walks) {
                    scope.bindHtml();
                })

                scope.bindHtml = function() {
                    if (scope.htmlContent) {
                        // add trusted content (iframe) as safe html
                        var chunks = scope.htmlContent.split(/\<iframe|\<\/iframe\>/gi);

                        // add back iframe tags and mark safe
                        chunks.forEach(function(chunk, index) {
                            if (index % 2 == 1) {
                                chunks[index] = $sce.trustAsHtml("<iframe"+chunk+"</iframe>");
                            }
                        });

                        scope.trustedContent = chunks;
                    } else {
                        scope.trustedContent = [];
                    }
                }
                scope.bindHtml();
            },
            template: '<div mathjax hljs ng-repeat="htmlContent in trustedContent"> ' +
                          '<div ng-bind-html="htmlContent"></div>' +
                      '</div>'
        };
    }]
);

})();
