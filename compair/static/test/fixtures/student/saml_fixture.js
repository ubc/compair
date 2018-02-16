var deepcopy = require('deepcopy');
var default_fixture = require('./default_fixture.js')

var storage = deepcopy(default_fixture);

for (userId in storage.users) {
    delete storage.users[userId].username;
    storage.users[userId].uses_compair_login = false;
}

delete storage.loginDetails.username;
delete storage.loginDetails.password;

module.exports = storage;