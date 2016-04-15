var users = {
    'admin': { username: 'root', password: 'password' },
    'instructor1': { username: 'instructor1', password: 'password' },
    'student1': { username: 'student1', password: 'password' },
    'student2': { username: 'student2', password: 'password' }
};

function UserFactory() {
}

UserFactory.prototype.getUser = function (username) {
    if (!users.hasOwnProperty(username)) {
        throw 'Test user "' + username + '" is not defined! Please define it in user_factory.js.';
    }

    return users[username];
};

module.exports = UserFactory;