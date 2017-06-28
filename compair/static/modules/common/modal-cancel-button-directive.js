(function() {

    angular.module('ubc.ctlt.compair.common').directive('modalCancelButton',
        function () {
        return {
            restrict: 'E',
            scope: {
                modalInstance: '='
            },
            template: '<div class="clearfix">' +
                        '<p class="pull-right">' +
                            '<a href="" ng-click="cancel()">Cancel</a> ' +
                        '</p>'+
                      '</div>',
            link: function (scope, element, attrs) {
                scope.cancel = function() {
                    scope.modalInstance.dismiss();
                };
            }
        };
    });

})();
