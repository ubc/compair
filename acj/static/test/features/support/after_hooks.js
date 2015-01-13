var myAfterHooks = function () {
  this.After(function(callback) {
    // Again, "this" is set to the World instance the scenario just finished
    // playing with.

    // We can then do some cleansing:
    browser.manage().deleteAllCookies();

    // Release control:
    callback();
  });
};

module.exports = myAfterHooks;