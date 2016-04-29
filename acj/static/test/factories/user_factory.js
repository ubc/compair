var objectAssign = require('object-assign');

var userTempalte = {
    "id": null,
    "username": null,
    "displayname": null,
    "email": null,
    "firstname": null,
    "fullname": null,
    "lastname": null,
    "student_no": null,
    "avatar": "63a9f0ea7bb98050796b649e85481845",
    "created": "Sat, 27 Dec 2014 20:13:11 -0000",
    "modified": "Sun, 11 Jan 2015 02:55:59 -0000",
    "lastonline": "Sun, 11 Jan 2015 02:55:59 -0000",
    "system_role": null, 
    "usertypeforsystemTemplate": null,
    "usertypesforsystem_id": null
}

var usertypeforsystemTemplate = {
    "id": null,
    "name": null
};

function UserFactory() {};


UserFactory.prototype.generateUser = function (id, userType, parameters) {
    var newUser = objectAssign({}, userTempalte, parameters);
    newUser.id = id;
    newUser.system_role = userType;
    
    newUser.usertypeforsystem = objectAssign({}, usertypeforsystemTemplate);
    newUser.usertypeforsystem.name = userType;
    
    switch (userType) {
        case "System Administrator":
            newUser.usertypesforsystem_id = 3;
            newUser.usertypeforsystem.id = 3;
            break;
        case "Instructor":
            newUser.usertypesforsystem_id = 2;
            newUser.usertypeforsystem.id = 2;
            break;
        case "Student":
            newUser.usertypesforsystem_id = 1;
            newUser.usertypeforsystem.id = 1;
            break;
    }
    
    return newUser;
};

module.exports = UserFactory;