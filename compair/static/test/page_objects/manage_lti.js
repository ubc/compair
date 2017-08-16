var LTIConsumersPage = function() {
    this.getLocation = function() {
        return 'lti/consumer';
    };

    this.clickButton = function(button) {
        switch (button) {
            case "Add LTI Consumer":
                return element(by.css('#create-lti-consumer-btn')).click();
        }
    }
};

module.exports = LTIConsumersPage;
