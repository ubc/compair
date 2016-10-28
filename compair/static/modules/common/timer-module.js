(function() {

var module = angular.module('ubc.ctlt.acj.common.timer',
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