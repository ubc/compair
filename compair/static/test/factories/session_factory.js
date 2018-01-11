var objectAssign = require('object-assign');

var permission_admin = {
    "Course": {
        "global": [
            "create",
            "delete",
            "edit",
            "manage",
            "read"
        ]
    },
    "Assignment": {
        "global": [
            "create",
            "delete",
            "edit",
            "manage",
            "read"
        ]
    },
    "User": {
        "global": [
            "create",
            "delete",
            "edit",
            "manage",
            "read"
        ]
    }
};

var permission_instructor = {
    "Course": {
        "global": [
            "create",
            "delete",
            "edit",
            "read"
        ]
    },
    "Assignment": {
        "global": [
            "create",
            "delete",
            "edit",
            "manage",
            "read"
        ]
    },
    "User": {
        "global": [
            "edit",
            "read"
        ]
    }
};


var permission_student = {
    "Course": {
        "global": [
            "read"
        ]
    },
    "Assignment": {
        "global": [
            "read"
        ]
    },
    "User": {
        "global": [
            "edit",
            "read"
        ]
    }
}

var permissionTemplates = {
    'System Administrator' : {
        'id': null,
        'permissions': permission_admin
    },
    'Instructor' : {
        'id': null,
        'permissions': permission_instructor
    },
    'Student' : {
        'id': null,
        'permissions': permission_student
    }
}

function SessionFactory() {};


SessionFactory.prototype.generateSession = function (user, additionalPermissions) {
    var newSession = objectAssign({}, permissionTemplates[user.system_role], {'id': user.id});

    if(additionalPermissions) {
        for(var domain in additionalPermissions) {
            for(var courseId in additionalPermissions[domain]) {
                newSession.permissions[domain][courseId] = additionalPermissions[domain][courseId];
            }
        }
    }

    return newSession;
};


module.exports = SessionFactory;
