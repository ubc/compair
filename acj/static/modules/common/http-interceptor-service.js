// Holds service used by requests that can change the GET response cached in the $cacheFactory

(function() {

var module = angular.module('ubc.ctlt.acj.common.interceptor', []);

module.service('Interceptors', function($q, $cacheFactory) {
	this.cache = {
		response: function(response) {
			var cache = $cacheFactory.get('$http');
			cache.remove(response.config.url);	// remove cached GET response
			// removing the suffix of some of the actions - eg. flagged
			var url = response.config.url.replace(/\/(flagged)/g, "");
			url = url.replace(/\/\d+$/g, "");
			cache.remove(url);	// remove root GET responses - eg. groups
			return response.data;
		}
	};

	this.enrolCache = {
		response: function(response) {
			var cache = $cacheFactory.get('classlist');
			var url = response.config.url.match(/\/api\/courses\/\d+/g);
			console.log(url[0]+'/users');
			cache.remove(url[0]+'/users');
			return response.data;
		}
	}
});

})();