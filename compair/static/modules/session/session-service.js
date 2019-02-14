(function() {

    var module = angular.module('ubc.ctlt.compair.session', [
        'ngResource',
        'LocalStorageModule',
        'ubc.ctlt.compair.user'
    ]);

    module.factory('ImpersonateResource',
        ['$resource',
        function($resource)
        {
            var impersonate_url = '/api/impersonate';
            var impersonate_resource = $resource(
                impersonate_url, {userId: '@userId'}, {
                    impersonate: {method: 'POST', url: impersonate_url+'/:userId'},
                    stop_impersonate: {method: 'DELETE'},
                });
            return impersonate_resource;
        }]);

    module.constant('ImpersonationSettings', {
        enabled: false,
    });

    /**
     * Session Service manages the session data for the frontend
     * It retrieves the user information and permissions from backend if they are not
     * available. Otherwise, provides the information from local cached values.
     */
    module.factory('Session',
            ["$rootScope",  "$http", "$q", "localStorageService", "$log", "UserResource",
            "$route", "$window", "$location", "$cacheFactory", "ImpersonateResource",
            function ($rootScope, $http, $q, localStorageService, $log, UserResource,
                $route, $window, $location, $cacheFactory, ImpersonateResource) {
        var PERMISSION_REFRESHED_EVENT = "event:Session-refreshPermissions";
        var IMPERSONATE_START_EVENT = "event:Session-startImpersonation";
        var IMPERSONATE_END_EVENT = "event:Session-endImpersonation";

        // The impersonate functions need to call session refresh.  Assign the
        // return object to a variable so the functions can reference each others
        var session_exports = {
            _user: new UserResource,
            _permissions: null,
            _impersonation: null,
            PERMISSION_REFRESHED_EVENT: PERMISSION_REFRESHED_EVENT,
            IMPERSONATE_START_EVENT: IMPERSONATE_START_EVENT,
            IMPERSONATE_END_EVENT: IMPERSONATE_END_EVENT,
            /**
             * Get user object from Session. The user is loaded from local cache if
             * it's already received from remote. Otherwise, it issues API calls.
             * Avoid using assignment to _user as we would like to keep the object
             * reference unchanged.
             * @returns {Promise}
             *
             * ```js
             *     Session.getUser().then(function(user) {
             *         $scope.loggedInUser = user;
             *     });
             * ```
             */
            getUser: function () {
                if (this._user.hasOwnProperty('id')) {
                    return $q.when(this._user);
                }

                var stored_user = localStorageService.get('user');
                if (stored_user)
                {
                    angular.extend(this._user, stored_user);
                    return $q.when(this._user);
                }

                $log.debug('Getting user from server');
                var scope = this;
                var deferred = $q.defer();
                return $http.get('/api/session', {
                    cache:true,
                    // bypass for fetching user sessions (login modal will appear automatically instead)
                    bypassErrorsInterceptor: true
                }).then(function (result) {
                    // retrieve logged in user's information
                    // return a promise for chaining
                    var u = UserResource.get({"id": result.data.id}, function(user) {
                        localStorageService.set('user', user);
                        angular.extend(scope._user, user);
                        deferred.resolve(scope._user);
                    });
                    angular.extend(scope._user, u);
                    scope._permissions = result.data.permissions;
                    localStorageService.set('permissions', scope._permissions);
                    scope._impersonation = result.data.impersonation;
                    localStorageService.set('impersonation', scope._impersonation);
                    return deferred.promise;
                });
            },

            /**
             * Get user permissions from Session. The permission is loaded form local cache
             * if it's already received from remote. Otherwise, it issues an API call.
             * @returns {Promise}
             */
            getPermissions: function () {
                if (this._permissions) {
                    return $q.when(this._permissions);
                }

                var stored_permissions = localStorageService.get('permissions');
                if (stored_permissions)
                {
                    this._permissions = stored_permissions;
                    return $q.when(this._permissions);
                }

                $log.debug('Getting permission from server');
                var scope = this;
                return $http.get('/api/session/permission')
                    .then(function (result) {
                        scope._permissions = result.data;
                        localStorageService.set('permissions', scope._permissions);
                        $rootScope.$broadcast(PERMISSION_REFRESHED_EVENT);
                        return scope._permissions;
                    });
            },

            isLoggedIn: function() {
                if (this._user && this._user.hasOwnProperty('id')) {
                    return true;
                }

                return false;
            },

            destroy: function() {
                var isImpersonating = session_exports.isImpersonating();
                // delete properties in user but keep user object
                for (var prop in this._user) {
                    delete this._user[prop];
                }
                this._permissions = null;
                this._impersonation = null;
                localStorageService.remove('user', 'permissions', 'lti_status', 'impersonation');
                if (isImpersonating) {
                    $rootScope.$broadcast(IMPERSONATE_END_EVENT);
                }
            },
            refresh: function(use_cache) {
                use_cache = typeof use_cache !== 'undefined' ? use_cache : true;
                var scope = this;
                var deferred = $q.defer();
                return $http.get('/api/session', { cache:use_cache }).then(function (result) {
                    // retrieve logged in user's information
                    // return a promise for chaining
                    var u = UserResource.get({"id": result.data.id}, function(user) {
                        localStorageService.set('user', user);
                        angular.extend(scope._user, user);
                        deferred.resolve(scope._user);
                    });
                    angular.extend(scope._user, u);
                    scope._permissions = result.data.permissions;
                    localStorageService.set('permissions', scope._permissions);
                    scope._impersonation = result.data.impersonation;
                    localStorageService.set('impersonation', scope._impersonation);
                    return deferred.promise;
                });
            },
            expirePermissions: function() {
                this._permissions = null;
                localStorageService.remove('permissions');
            },

            getImpersonation: function() {
                if (this._impersonation) {
                    return $q.when(this._impersonation);
                } else {
                    // impersonation state is based on user info. make sure it is valid first
                    return session_exports.getUser().then(function(user) {
                        var stored_impersonation = localStorageService.get('impersonation');
                        if (stored_impersonation) {
                            return $q.when(stored_impersonation);
                        }
                    });
                }
                return $q.when({});
            },
            isImpersonating: function() {
                if (this._impersonation) {
                    return this._impersonation.impersonating;
                }

                var stored_impersonation = localStorageService.get('impersonation');
                if (stored_impersonation) {
                    return stored_impersonation.impersonating;
                }
                return null;
            },
            impersonate: function (courseId, userId) {
                return ImpersonateResource.impersonate({'userId': userId}).$promise.then(function(ret) {
                    // Destroy the session first. In case the refresh failed (e.g. network issue), 
                    // a success reload of the page will show the correct student view.
                    session_exports.destroy();
                    // clear angularjs cache
                    _.each(['$http', 'classlist'], function(id) {
                        var cache = $cacheFactory.get(id);
                        if (cache) {
                            cache.removeAll();
                        }
                    });
                    return session_exports.refresh(false).then(function () {
                        if (courseId) {
                            var newPath = '/course/' + courseId;
                            if ($location.path() == newPath) {
                                $route.reload();
                            } else {
                                $location.path(newPath);
                            }
                        } else {
                            $window.location.assign('/');
                        }
                        $rootScope.$broadcast(IMPERSONATE_START_EVENT);
                    });
                });
            },
            stop_impersonate: function(courseId) {
                return ImpersonateResource.stop_impersonate({}).$promise.then(function(ret) {
                    session_exports.destroy();
                    // clear angularjs cache
                    _.each(['$http', 'classlist'], function(id) {
                        var cache = $cacheFactory.get(id);
                        if (cache) {
                            cache.removeAll();
                        }
                    });
                    session_exports.refresh(false).then(function () {
                        if (courseId) {
                            var newPath = '/course/' + courseId;
                            if ($location.path() == newPath) {
                                $route.reload();
                            } else {
                                $location.path(newPath);
                            }
                        } else {
                            $window.location.assign('/');
                        }
                        $rootScope.$broadcast(IMPERSONATE_END_EVENT);
                    });
                });
            },
            detect_page_reload_and_flush: function() {
                if (performance && performance.navigation && performance.navigation.type == 1) {
                    localStorageService.clearAll();
                    session_exports.destroy();
                }
            },
        };

        return session_exports;
    }]);

})();
