(function() {

var module = angular.module('ubc.ctlt.compair.common.timer',
   [
        'ngResource'
   ]
);

/***** Providers *****/
module.factory(
    'TimerResource',
    ['$resource',
    function($resource)
    {
        return $resource('/api/timer');
    }
]);

})();