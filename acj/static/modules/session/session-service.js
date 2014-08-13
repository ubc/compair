(function() {

    var module = angular.module('ubc.ctlt.acj.session', ['ngResource', 'ngCookies', 'ubc.ctlt.acj.user']);

    /**
     * Session Service manages the session data for the frontend
     * It retrieves the user information and permissions from backend if they are not
     * available. Otherwise, provides the information from local cached values.
     */
    module.factory('Session', function ($http, $q, $cookieStore, $log, UserResource) {
        return {
            _user: new UserResource,
            _permissions: null,
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

                var cookie_user = $cookieStore.get('current.user');
                if (cookie_user)
                {
                    angular.extend(this._user, cookie_user);
                    return $q.when(this._user);
                }

                $log.debug('Getting user from server');
                var scope = this;
                var deferred = $q.defer();
                return $http.get('/session')
                    .then(function (result) {
                        // retrieve logged in user's information
                        // return a promise for chaining
                        var u = UserResource.get({"id": result.data.id}, function(user) {
                            $cookieStore.put('current.user', user);
                            angular.extend(scope._user, user);
                            deferred.resolve(scope._user);
                        });
                        angular.extend(scope._user, u);
                        scope._permissions = result.data.permissions;
                        $cookieStore.put('current.permissions', scope._permissions);
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

                var cookie_permissions = $cookieStore.get('current.permissions');
                if (cookie_permissions)
                {
                    this._permissions = cookie_permissions;
                    return $q.when(this._permissions);
                }

                $log.debug('Getting permission from server');
                var scope = this;
                return $http.get('/session/permissions')
                    .then(function (result) {
                        scope._permissions = result.data;
                        $cookieStore.put('current.permissions', scope._permissions);
                        return scope._permissions;
                    });
            },

            isLoggedIn: function() {
                if (this._user) {
                    return true;
                }

                return false;
            },

            destroy: function() {
                // delete properties in user but keep user object
                for (var prop in this._user) {
                    delete this._user[prop];
                }
                this._permissions = null;
                $cookieStore.remove('current.user');
                $cookieStore.remove('current.permissions');
            }
        };
    });

})();
