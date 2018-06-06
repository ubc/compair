// Holds service used by requests that can change the GET response cached in the $cacheFactory
(function() {

var module = angular.module('ubc.ctlt.compair.common.interceptor', []);

module.service('Interceptors', ['$q', '$cacheFactory', 'AnswerResource', function($q, $cacheFactory, AnswerResource) {
    var temporaryGroupStore = {};

    this.cache = {
        response: function(response) {
            var cache = $cacheFactory.get('$http');
            cache.remove(response.config.url);	// remove cached GET response
            // removing the suffix of some of the actions - eg. top
            var url = response.config.url.replace(/\/(top)/g, "");
            cache.remove(url);
            url = url.replace(/\/[A-Za-z0-9_-]{22}$/g, "");
            cache.remove(url);	// remove root GET responses - eg. groups
            return response.data;
        }
    };

    this.enrolCache = {
        response: function(response) {
            var cache = $cacheFactory.get('classlist');
            if(cache) {
                var url = response.config.url.match(/\/api\/courses\/[A-Za-z0-9_-]{22}/g);
                cache.remove(url[0] + '/users');
            }
            cache = $cacheFactory.get('$http');
            if(cache) {
                var url = response.config.url.match(/\/api\/courses\/[A-Za-z0-9_-]{22}/g);
                cache.remove(url[0] + '/groups');
                cache.remove(url[0] + '/groups/user');
            }
            return response.data;
        }
    };

    this.enrolCacheLTI = {
        response: function(response) {
            var cache = $cacheFactory.get('classlist');
            if(cache) {
                var courseId = response.config.url.match(/[A-Za-z0-9_-]{22}/g)[0];
                cache.remove('/api/courses/' + courseId + '/users');
            }
            return response.data;
        }
    };

    this.contextCacheLTI = {
        response: function(response) {
            // force refresh enrolment status
            var cache = $cacheFactory.get('classlist');
            if(cache) {
                var courseId = response.config.url.match(/[A-Za-z0-9_-]{22}/g)[0];
                cache.remove('/api/courses/' + courseId + '/users');
            }
            // force refresh lti status
            cache = $cacheFactory.get('$http');
            if(cache) {
                var courseId = response.config.url.match(/[A-Za-z0-9_-]{22}/g)[0];
                cache.remove('/api/courses/' + courseId);
            }
            return response.data;
        }
    };

    this.answerCommentCache = {
        response: function(response) {
            var cache = $cacheFactory.get('$http');
            // match both object endpoint and list endpoint
            var url = response.config.url.match(/\/api\/courses\/[A-Za-z0-9_-]{22}\/assignments\/[A-Za-z0-9_-]{22}\/answers\/[A-Za-z0-9_-]{22}\/comments(\/[A-Za-z0-9_-]{22})?/g);
            cache.remove(url[0]);
            var listUrl = url[0].replace(/\/[A-Za-z0-9_-]{22}$/g, "");
            if (listUrl != url[0]) {
                cache.remove(listUrl);
            }
            AnswerResource.invalidListCache();

            return response.data;
        }
    };
}]);

})();