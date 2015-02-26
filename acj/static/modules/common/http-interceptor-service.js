// Holds service used by requests that can change the GET response cached in the $cacheFactory

(function() {

var module = angular.module('ubc.ctlt.acj.common.interceptor', []);

module.service('Interceptors', function($q, $cacheFactory) {
	this.cache = {
		response: function(response) {
			var cache = $cacheFactory.get('$http');
			cache.remove(response.config.url);	// remove cached GET response
			var url = response.config.url.replace(/\/(flagged)/g, "");
			url = url.replace(/\/\d+$/g, "");
			cache.remove(url);	// remove root GET responses - eg. groups
			return response.data;
		}
	};
});

})();