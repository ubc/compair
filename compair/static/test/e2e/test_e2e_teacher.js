describe('ComPAIR testsuite - Teacher', function() {
    var rootURL = "/app/#";
    var reset = false;

    beforeEach(function() {
        if (!reset) {
            browser().navigateTo('/resetdb');
            reset = true;
        }
    });

    describe('course', function() {
        it('user is logged in', function() {
            browser().navigateTo(rootURL + '/login');
            input('username').enter('testteacher');
            input('password').enter('demo');
            element('.btn.btn-primary').click();
            expect(browser().location().url()).toBe('/');
        });
        it('create a new course', function() {
            element('#step1').click();
            input('course').enter("test course 101");
            element(".btn.btn-primary[value='Create']").click();
            expect(element('tr[ng-repeat="course in courses | orderBy:orderProp | filter:cquery"]').text()).toContain("test course 101");
        });
        it('edit the new course', function() {
            element('a[href^="#/editcourse/"]').click();
            input("newname").enter("test course 201");
            element('button[ng-click="submit();submitted=true"]').click();

            expect(element("h2.ng-binding").text()).toBe("Edit Course - test course 201");
            input("newtag").enter("Testtag 1");
            element("button.btn.btn-primary.btn-sm").click();
            input("newtag").enter("Testtag 2");
            element("button.btn.btn-primary.btn-sm").click();
            expect(repeater('tr[ng-repeat="tag in tags"]').count()).toBe(2);
            element("button.btn.btn-danger.btn-xs:eq(0)").click();
            expect(repeater('tr[ng-repeat="tag in tags"]').count()).toBe(1);
        });
        it('enroll students in the new course', function() {
            browser().navigateTo(rootURL);
            element('a[href^="#/enrollpage/"]').click();
            element('p[ng-click="add(student, \'S\')"]:eq(0)').click();
            element('p[ng-click="add(student, \'S\')"]:eq(2)').click();
            element('p[ng-click="add(student, \'S\')"]:eq(4)').click();
            expect(repeater('p[ng-click="drop(student, \'S\')"]').count()).toBe(3);
            element('p[ng-click="drop(student, \'S\')"]').click();
            expect(repeater('p[ng-click="drop(student, \'S\')"]').count()).toBe(0);

            input("params.filter()[name]").enter("Three");
            expect(repeater('tr[ng-repeat="teacher in teachers"]').count()).toBe(1);
            input("params.filter()[name]").enter("Seven");
            expect(repeater('tr[ng-repeat="student in students"]').count()).toBe(1);
        });
    });
    describe('new user', function() {
        it('create a new student', function() {
            element('a[href="#/createuser"]').click();
            select("role").option("Student");
            input("username").enter("teststudent");
            input("firstname").enter("test");
            input("lastname").enter("student");
            input("display").enter("teststudent");
            input("email").enter("teststudent@test.test");
            input("password").enter("demo");
            input("retypepw").enter("demo");
            element('input.btn.btn-primary').click();
            expect(element("li.alert.alert-success.text-center").text()).toBe("User created successfully");
        });
        it('user is logged out', function() {
            element('.dropdown-menu:last-child a').click();
            expect(browser().location().url()).toBe('/login');
        });
    });
});
