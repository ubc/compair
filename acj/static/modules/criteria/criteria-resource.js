// When a user makes a judgement between 2 answers, they can decide which answer
// is the better choice according to multiple criteria.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.criteria', 
	[
		'ngResource'
	]
);

/***** Providers *****/
module.factory('CriteriaResource', function($resource) {
	return $resource('/api/courses/:courseId/criteria');
});

/***** Controllers *****/
// TODO declare controllers here, e.g.:
// module.controller(...)

// End anonymous function
})();
