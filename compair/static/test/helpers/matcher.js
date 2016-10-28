beforeEach(function () {
    jasmine.addMatchers({
        toEqualData: function () {
            return {
                compare: function (actual, expected) {
                    var pass = angular.equals(actual, expected);
                    var toEqual = pass ? "not to equal" : "to equal";
                    return {
                        pass: pass,
                        message: "Expected " + angular.mock.dump(actual) + " data " + toEqual + " " + expected
                    };
                }
            };
        },
        toHaveText: function () {
            return {
                compare: function (actual, expected) {
                    var pass = actual.text().trim() === expected;
                    var toHave = pass ? "not to have" : "to have";

                    return {
                        pass: pass,
                        message: "Expected '" + angular.mock.dump(actual) + "' " + toHave + " the exact text '" + expected + "'"
                    };
                }
            };
        },
        toContainText: function () {
            return {
                compare: function (actual, expected) {
                    var text = actual.text();
                    var pass = text != null && (text.indexOf(expected) > -1 );
                    var toHave = pass ? "not to have" : "to have";

                    return {
                        pass: pass,
                        message: "Expected '" + angular.mock.dump(actual) + "' " + toHave + " the text '" + expected + "'"
                    };
                }
            };
        },
        toHaveClass: function () {
            return {
                compare: function (actual, expected) {
                    var pass = actual.hasClass(expected);
                    var toHave = pass ? "not to have" : "to have";

                    return {
                        pass: pass,
                        message: "Expected '" + angular.mock.dump(actual) + "' " + toHave + " a class '" + expected + "'."
                    };
                }
            };
        },
        toHaveAttr: function () {
            return {
                compare: function (actual, attributeName, expectedAttributeValue) {
                    var pass = expectedAttributeValue === undefined ? attributeName !== undefined : actual.attr(attributeName) === expectedAttributeValue;
                    var toHave = pass ? "not to have" : "to have";

                    return {
                        pass: pass,
                        message: "Expected '" + angular.mock.dump(actual) + "' " + toHave + " attribute '" + attributeName + "' with value " + expectedAttributeValue + "."
                    }
                }
            };
        },
        toBeHidden: function () {
            return {
                compare: function (actual) {
                    var expected = 'ng-hide';
                    var pass = actual.hasClass(expected);
                    var toHave = pass ? "not to have" : "to have";

                    return {
                        pass: pass,
                        message: "Expected '" + angular.mock.dump(actual) + "' " + toHave + " a class '" + expected + "'."
                    };
                }
            };
        }
    });
});
