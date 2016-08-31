// Holds service used by requests that can change the GET response cached in the $cacheFactory

(function() {

var module = angular.module('ubc.ctlt.acj.common.interceptor', []);

module.service('Interceptors', ['$q', '$cacheFactory', 'AnswerResource', function($q, $cacheFactory, AnswerResource) {
    var temporaryGroupStore = {};

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

    this.groupSessionInterceptor = {
        response: function(response) {
            // store all course group names until javascript memory wiped (page refreshed,closed,etc)
            // helps in case instructors make mistakes while editing groups on class list screen
            var courseId = response.config.url.match(/\d+/g)[0];
            if (temporaryGroupStore[courseId] == undefined) {
                temporaryGroupStore[courseId] = [];
            }
            temporaryGroupStore[courseId] = _.sortBy(
                _.union(temporaryGroupStore[courseId], response.data.objects),
                function(value) { return value; }
            );

            response.data.objects = temporaryGroupStore[courseId];

            return response.data;
        }
    };

    this.answerCommentCache = {
        response: function(response) {
            var cache = $cacheFactory.get('$http');
            // match both object endpoint and list endpoint
            var url = response.config.url.match(/\/api\/courses\/\d+\/assignments\/\d+\/answers\/\d+\/comments(\/\d+)?/g);
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