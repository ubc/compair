var objectAssign = require('object-assign');

var userTempalte = {
    "id": null,
    "username": null,
    "displayname": null,
    "email": null,
    "firstname": null,
    "fullname": null,
    "fullname_sortable": null,
    "lastname": null,
    "student_number": null,
    "avatar": "63a9f0ea7bb98050796b649e85481845",
    "created": "Sat, 27 Dec 2014 20:13:11 -0000",
    "modified": "Sun, 11 Jan 2015 02:55:59 -0000",
    "last_online": "Sun, 11 Jan 2015 02:55:59 -0000",
    "system_role": null,
    "uses_compair_login": true,
    "email_notification_method": 'enable'
}

function UserFactory() {};


UserFactory.prototype.generateUser = function (id, system_role, parameters) {
    var newUser = objectAssign({}, userTempalte, parameters);
    newUser.id = id;
    newUser.system_role = system_role;

    return newUser;
};

module.exports = UserFactory;