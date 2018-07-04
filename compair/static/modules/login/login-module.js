// Login/logout controllers

// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.login',
    [
        'ngAnimate',
        'ngResource',
        'ngRoute',
        'ui.bootstrap',
        'ubc.ctlt.compair.authentication',
        'ubc.ctlt.compair.authorization',
        'ubc.ctlt.compair.user',
        'ubc.ctlt.compair.lti'
    ]
);

/***** Providers *****/
module.factory('LoginResource', ["$resource", function($resource) {
    return $resource(
        '/api/:operation',
        {},
        {
            login: { method:'POST', params: {operation: "login"} },
            logout: { method:'DELETE', params: {operation: "logout"} }
        }
    );
}]);

module.factory('DemoResource', ['$resource', function($resource) {
    var User = $resource('/api/demo/', {
        'save': {method: 'POST'}
    });
    User.MODEL = "User";

    User.prototype.isLoggedIn = function() {
        return this.hasOwnProperty('id');
    };

    return User;
}]);

module.constant('AuthTypesEnabled', {
    app: true,
    cas: true,
    saml: true,
    lti: true,
    demo: false
});

module.constant('LoginConfigurableHTML', {
    addition_instructions: "",
    cas: "",
    saml: ""
});

/***** Directives *****/
// TODO this might be useful elsewhere, if we need to autofocus something
// html5 property autofocus behaves differently on Firefox than in Chrome, in Firefox
// it only works before onload, so it doesn't do anything if we pop the login modal
// after the entire page has been loaded.
// The timeout forces a wait for the loginbox to be rendered.
module.directive('autoFocus', ["$timeout", function($timeout) {
    return {
        restrict: 'AC',
        link: function(scope, _element, attr) {
            $timeout(function(){
                _element[0].focus();
            }, 100);
        }
    };
}]);

/***** Listeners *****/
// display the login page if user is not logged in
module.run(
    ["$rootScope", "$uibModal", "$cacheFactory", "AuthenticationService", "Toaster",
    function ($rootScope, $uibModal, $cacheFactory, AuthenticationService, Toaster) {
    // Create a modal dialog box for containing the login form
    var loginBox;
    var modalScope = $rootScope.$new();
    var isOpen = false;
    // Functions to display/hide the login form

    // for creating new account via 3rd-party authentication
    $rootScope.displayCreateUser = function() {
        modalScope.showCreateUserForm = true;
        modalScope.showComPAIRAccountFieldsCreateUserForm = false;
    };

    $rootScope.showLoginWithCreateUser = function() {
        modalScope.allowCreateUser = true;
        modalScope.showComPAIRAccountFieldsCreateUserForm = true;
        $rootScope.showLogin();
    };

    $rootScope.showLogin = function() {
        if (isOpen) return;
        loginBox = $uibModal.open({
            backdrop: 'static', // can't close login on backdrop click
            controller: "LoginController",
            templateUrl: 'modules/login/login-partial.html',
            keyboard: false, // can't close login on pressing Esc key
            scope: modalScope
        });
        isOpen = true;
    };
    $rootScope.hideLogin = function() {
        if (loginBox) {
            loginBox.close();
            modalScope = $rootScope.$new();
        }
        isOpen = false;
    };
    // Show the login form when we have a login required event
    $rootScope.$on(AuthenticationService.LOGIN_REQUIRED_EVENT, $rootScope.showLogin);
    $rootScope.$on(AuthenticationService.LTI_LOGIN_REQUIRED_EVENT, $rootScope.showLoginWithCreateUser);
    // Show the login form when we have a 3rd-party authentication login required event
    $rootScope.$on(AuthenticationService.AUTH_LOGIN_REQUIRED_EVENT, $rootScope.displayCreateUser);

    // Hide the login form on login
    $rootScope.$on(AuthenticationService.LOGIN_EVENT, $rootScope.hideLogin);
    // listen to 403 response for CAS/SAML user that do not exist in the system
    $rootScope.$on(AuthenticationService.LOGIN_FORBIDDEN_EVENT, function(event, rejection) {
        if ('type' in rejection.data && (rejection.data.type == 'CAS' || rejection.data.type == 'SAML')) {
            Toaster.warning('Log In Failed', 'Please double-check your username and password and try again.');
            $rootScope.$broadcast(AuthenticationService.LOGIN_REQUIRED_EVENT);
        }
    });
    $rootScope.$on(AuthenticationService.LOGOUT_EVENT, function () {
        $cacheFactory.get('$http').removeAll();
        var cache = $cacheFactory.get('classlist');
        if (cache) {
            cache.removeAll();
        }
    });
}]);


/***** Controllers *****/
module.controller(
    "LoginController",
    [ "$rootScope", "$scope", "$location", "$log", "$route", "AuthTypesEnabled",
      "LoginResource", "AuthenticationService", "LTI", "LTIResource", "SystemRole",
      "DemoResource", "LoginConfigurableHTML",
    function ($rootScope, $scope, $location, $log, $route, AuthTypesEnabled,
              LoginResource, AuthenticationService, LTI, LTIResource, SystemRole,
              DemoResource, LoginConfigurableHTML)
    {
        $scope.submitted = false;
        $scope.SystemRole = SystemRole;
        $scope.LoginConfigurableHTML = LoginConfigurableHTML;

        // update allowCreateUser if needed
        $rootScope.$on(AuthenticationService.LTI_LOGIN_REQUIRED_EVENT, function() {
            $scope.allowCreateUser = true;
            $scope.showComPAIRAccountFieldsCreateUserForm = true;
        });

        $rootScope.$on(AuthenticationService.AUTH_LOGIN_REQUIRED_EVENT, function() {
            $scope.showCreateUserForm = true;
            $scope.showComPAIRAccountFieldsCreateUserForm = false;
        });

        $scope.AuthTypesEnabled = AuthTypesEnabled;
        // open account login automatically if cas and saml is disabled
        if (!$scope.AuthTypesEnabled.cas && !$scope.AuthTypesEnabled.saml &&
                !AuthTypesEnabled.demo && $scope.AuthTypesEnabled.app) {
            $scope.showAppLogin = true;
        }

        $scope.createDemoAccount = function(system_role) {
            DemoResource.save({system_role: system_role}).$promise.then(
                function(ret) {
                    // demo account creation successful
                    $log.debug("Demo account creation successful!");
                    userid = ret.user_id;
                    $log.debug("Login User ID: " + userid);
                    // retrieve logged in user's information
                    AuthenticationService.login(true).then(function() {
                        $scope.login_err = "";
                        $scope.submitted = false;

                        // force route to "/"
                        // can't rely on authentication service reloading since uuids might be erased
                        if ($location.path() == "/") {
                            $route.reload();
                        } else {
                            $location.path("/");
                        }
                    }, function() {
                        $log.error("Failed to retrieve logged in user's data: " + JSON.stringify(ret));
                        $scope.login_err = "Unable to retrieve user information, server problem?";
                        $scope.submitted = false;
                    });
                },
                function(ret) {
                    // login failed
                    $log.debug("Login authentication failed.");
                    if (ret.data.error) {
                        $scope.login_err = ret.data.error;
                    }
                    else {
                        $scope.login_err = "Server error during authentication.";
                    }
                    $scope.submitted = false;
                }
            );
        }

        $scope.submit = function() {
            $scope.submitted = true;
            var params = {"username": $scope.username,  "password": $scope.password};
            LoginResource.login(params).$promise.then(
                function(ret) {
                    // login successful
                    $log.debug("Login authentication successful!");
                    userid = ret.user_id;
                    $log.debug("Login User ID: " + userid);
                    // retrieve logged in user's information
                    AuthenticationService.login().then(function() {
                        $scope.login_err = "";
                        $scope.submitted = false;
                        $route.reload();
                    }, function() {
                        $log.error("Failed to retrieve logged in user's data: " + JSON.stringify(ret));
                        $scope.login_err = "Unable to retrieve user information, server problem?";
                        $scope.submitted = false;
                    });
                },
                function(ret) {
                    // login failed
                    $log.debug("Login authentication failed.");
                    $scope.login_err = ret.data.message ? ret.data.message : "Server error during authentication.";
                    $scope.submitted = false;
                }
            );

        };
    }
]);

module.controller(
    "LogoutController",
    [ "$scope", "$location", "$log", "$route", "LoginResource", "AuthenticationService", "Session",
    function LogoutController($scope, $location, $log, $route, LoginResource, AuthenticationService, Session) {
        $scope.logout = function() {
            return LoginResource.logout().$promise.then(
                function(data) {
                    $log.debug("Logging out user successful.");
                    if ("redirect" in data) {
                        Session.destroy();
                        window.location = data.redirect;
                    } else {
                        AuthenticationService.logout();
                        $location.path("/"); //redirect user to home screen
                        $route.reload();
                    }
                }
                // TODO do we care about logout failure? if so, handle it here
            );
        };
    }
]);
// End anonymous function
})();
