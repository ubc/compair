// TODO
// Insert short explanation of what this module does, for this module, it'd be:
// An example/template of how to create functionally isolated modules in
// Angular for organizing code.

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.user', ['ngResource']);

/***** Providers *****/
module.factory('UserResource', function($resource) {
	return $resource('/api/users/:id', {id: '@id'},
		{
			'getUserCourses':
			{
				method: 'GET',
				url: '/api/users/:id/courses'
			}
		}
	);
});

/***** Controllers *****/
// TODO declare controllers here, e.g.:
// module.controller(...)

// End anonymous function
})();
