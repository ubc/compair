var myAfterHooks = function () {
	this.After(function (scenario, callback) {
		// Again, "this" is set to the World instance the scenario just finished
		// playing with.
		browser.executeAsyncScript(
			'var cb = arguments[arguments.length - 1];' +
			'var logoutScope = window.angular.element("#logout-link").scope();' +
			'if(logoutScope) { logoutScope.logout().then(cb); } else { cb() }').then(function() {
				browser.manage().deleteAllCookies().then(function () {
					// Release control:
					callback();
				});
			});
		//var displayNameElm = element(by.binding('loggedInUser.displayname'));
		//var logoutButtonElm = element(by.css('li[ng-controller=LogoutController] a'));
		//
		//displayNameElm.click();
		//
		//logoutButtonElm.click().then(function() {
		//	browser.manage().deleteAllCookies().then(function () {
		//		// Release control:
		//		callback();
		//	});
		//});
	});
};

module.exports = myAfterHooks;