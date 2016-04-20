var objectAssign = require('object-assign');

var permission_admin = {
    "Courses": {
        "create": {'global': true},
        "delete": {'global': true},
        "edit": {'global': true},
        "manage": {'global': true},
        "read": {'global': true}
    },
    "PostsForQuestions": {
        "create": {'global': true},
        "delete": {'global': true},
        "edit": {'global': true},
        "manage": {'global': true},
        "read": {'global': true}
    },
    "Users": {
        "create": {'global': true},
        "delete": {'global': true},
        "edit": {'global': true},
        "manage": {'global': true},
        "read": {'global': true}
    }
};

var permission_instructor = {
    "Courses": {
        "create": {'global': true},
        "delete": {'global': false},
        "edit": {'global': true},
        "manage": {'global': false},
        "read": {'global': true}
    },
    "PostsForQuestions": {
        "create": {'global': true},
        "delete": {'global': true},
        "edit": {'global': true},
        "manage": {'global': true},
        "read": {'global': true}
    },
    "Users": {
        "create": {'global': true},
        "delete": {'global': false},
        "edit": {'global': true},
        "manage": {'global': false},
        "read": {'global': true}
    }
};


var permission_student = {
    "Courses": {
        "create": {'global': false},
        "delete": {'global': false},
        "edit": {'global': false},
        "manage": {'global': false},
        "read": {'global': true}
    },
    "PostsForQuestions": {
        "create": {'global': false},
        "delete": {'global': false},
        "edit": {'global': false},
        "manage": {'global': false},
        "read": {'global': true}
    },
    "Users": {
        "create": {'global': false},
        "delete": {'global': false},
        "edit": {'global': true},
        "manage": {'global': false},
        "read": {'global': true}
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


SessionFactory.prototype.generateSession = function (userId, type, additionalPermissions) {
    var newSession = objectAssign({}, permissionTemplates[type]);
    newSession.id = userId;
    
    if(additionalPermissions) {
        for(var domain in additionalPermissions) {
            for(var action in additionalPermissions[domain]) {
                var permissionBase = newSession.permissions[domain][action];
                var permissionExtend = additionalPermissions[domain][action];
                newSession.permissions[domain][action] = objectAssign({}, permissionBase, permissionExtend);
            }
        }
    }
    
    return newSession;
};


module.exports = SessionFactory;
