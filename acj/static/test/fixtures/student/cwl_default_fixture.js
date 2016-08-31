var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var storage = {
    session: {},
    users: []
}

var admin = userFactory.generateUser(1, "System Administrator", {
    displayname: "root",
    firstname: "JaNy",
    lastname: "bwsV",
    fullname: "JaNy bwsV",
    uses_acj_login: false
});
storage.users.push(admin);

var instructor = userFactory.generateUser(2, "Instructor", {
    displayname: "First Instructor",
    firstname: "First",
    lastname: "Instructor",
    fullname: "First Instructor",
    email: "first.instructor@exmple.com",
    uses_acj_login: false
});
storage.users.push(instructor);

var student = userFactory.generateUser(3, "Student", {
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    email: "first.student@exmple.com",
    uses_acj_login: false
});
storage.users.push(student);



storage.loginDetails = { id: student.id };
storage.session = sessionFactory.generateSession(student.id, student.system_role, {});


module.exports = storage;