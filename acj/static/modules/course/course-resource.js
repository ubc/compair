// Just holds the course resource object

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.course', ['ngResource']);

/***** Providers *****/
module.factory('CourseResource', function($resource) {
	return $resource('/api/courses/:id', {id: '@id'});
});

/***** Controllers *****/
// TODO declare controllers here, e.g.:
// module.controller(...)

// End anonymous function
})();
