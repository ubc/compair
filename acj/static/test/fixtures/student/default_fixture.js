var UserFactory = require('../../factories/user_factory.js');
var userFactory = new UserFactory();

var SessionFactory  = require('../../factories/session_factory.js');
var sessionFactory = new SessionFactory();

var storage = {
    session: {},
    users: []
}

var admin = userFactory.generateUser(1, "System Administrator", {
    username: "root",
    displayname: "root",
    firstname: "JaNy",
    lastname: "bwsV",
    fullname: "JaNy bwsV",
});
storage.users.push(admin);

var instructor = userFactory.generateUser(2, "Instructor", {
    username: "instructor1",
    displayname: "First Instructor",
    firstname: "First",
    lastname: "Instructor",
    fullname: "First Instructor",
    email: "first.instructor@exmple.com"
});
storage.users.push(instructor);

var student = userFactory.generateUser(3, "Student", {
    username: "student1",
    displayname: "First Student",
    firstname: "First",
    lastname: "Student",
    fullname: "First Student",
    email: "first.student@exmple.com"
});
storage.users.push(student);



storage.loginDetails = { id: student.id, username: student.username, password: "password" };
storage.session = sessionFactory.generateSession(student.id, student.system_role, {});


module.exports = storage;