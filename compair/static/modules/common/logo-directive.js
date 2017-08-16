(function() {
'use strict';

angular.module('ubc.ctlt.compair.common').constant('logoSettings', {
    path: 'img/'
});

angular.module('ubc.ctlt.compair.common').directive('compairLogo',
    ['logoSettings',
    function (logoSettings) {
        return {
            restrict: 'E',
            scope: {
                type: '=',
            },
            template: '<img ng-src="{{logo}}" alt="{{alt}}" class="compair-logo" />',
            link: function (scope, element, attrs) {
                scope.alt = scope.type == 'scale' ? "ComPAIR Scale" : "ComPAIR Logo";
                scope.logo = logoSettings.path + 'compair-logo-'+scope.type+'.png';
            }
        };
    }
]);

})();
