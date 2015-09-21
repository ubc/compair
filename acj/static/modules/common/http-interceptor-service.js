// Holds service used by requests that can change the GET response cached in the $cacheFactory

(function() {

var module = angular.module('ubc.ctlt.acj.common.interceptor', []);

module.service('Interceptors', ['$q', '$cacheFactory', 'AnswerResource', function($q, $cacheFactory, AnswerResource) {
	this.cache = {
		response: function(response) {
			var cache = $cacheFactory.get('$http');
			cache.remove(response.config.url);	// remove cached GET response
			// removing the suffix of some of the actions - eg. flagged
			var url = response.config.url.replace(/\/(flagged)/g, "");
			cache.remove(url);
			url = url.replace(/\/\d+$/g, "");
			cache.remove(url);	// remove root GET responses - eg. groups
			return response.data;
		}
	};

	this.enrolCache = {
		response: function(response) {
			var cache = $cacheFactory.get('classlist');
			if(cache) {
				var url = response.config.url.match(/\/api\/courses\/\d+/g);
				cache.remove(url[0] + '/users');
			}
			return response.data;
		}
	};

	this.answerCommentCache = {
		response: function(response) {
			var cache = $cacheFactory.get('$http');
			// match both object endpoint and list endpoint
			var url = response.config.url.match(/\/api\/courses\/\d+\/questions\/\d+\/answers\/\d+\/comments(\/\d+)?/g);
			cache.remove(url[0]);
			var listUrl = url[0].replace(/\/\d+$/g, "");
			if (listUrl != url[0]) {
				cache.remove(listUrl);
			}
			AnswerResource.invalidListCache();

			return response.data;
		}
	};
}]);

})();