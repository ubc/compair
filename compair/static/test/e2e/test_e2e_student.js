describe('ComPAIR testsuite - Student', function() {
    var rootURL = "/app/#";
    var reset = false;

    beforeEach(function() {
        if (!reset) {
            browser().navigateTo('/resetdb');
            reset = true;
        }
    });

    describe('assignments', function() {
        it('user is logged in', function() {
            browser().navigateTo(rootURL + '/login');
            input('username').enter('testuser');
            input('password').enter('demo');
            element('.btn.btn-primary').click();
            expect(browser().location().url()).toBe('/');
        });
        it('go to assignment page', function() {
            element('#step2').click();
            expect(browser().location().url()).toMatch(/\/assignmentpage\/./);
        });
        it('create assignment', function() {
            var qCount = repeater("ul.postingsList.padding0 li").count();
            qCount.execute(function(){});
            input('name').enter("unittestquiz");
            contenteditable('div[name="assignment"]').enter('unit test assignment');
            contenteditable('div[name="answerq"]').enter('unit test answer');
            element(".btn.btn-primary:first").click();
            expect(repeater("ul.postingsList.padding0 li").count()).toBe(qCount.value + 1);
        });
        it('delete the created assignment', function() {
            var qCount = repeater("ul.postingsList.padding0 li").count();
            qCount.execute(function(){});
            confirmOK();
            element("a.btn.btn-danger.btn-sm.btnWidth:first").click();
            expect(repeater("ul.postingsList.padding0 li").count()).toBe(qCount.value - 1);
        });
    });

    describe('answers', function() {
        it('go to answer page', function() {
            element('a[ng-click="setType(\'discussion\');switchEdits(-1)"]').click();
            element('#stepAnswer:first').click();
            expect(browser().location().url()).toMatch(/\/answerpage\/./);
        });
        it('create answer', function() {
            var qCount = repeater("ul.postingsList.padding0 li").count();
            qCount.execute(function(){});
            contenteditable('div[name="answer"]').enter('unit test answer');
            element("a[ng-click='submit();submitted=true']").click();
            expect(repeater("ul.postingsList.padding0 li").count()).toBe(qCount.value + 1);
        });
        it('delete the created answer', function() {
            var qCount = repeater("ul.postingsList.padding0 li").count();
            qCount.execute(function(){});
            confirmOK();
            element("a.btn.btn-danger.btn-sm.btnWidth:first").click();
            expect(repeater("ul.postingsList.padding0 li").count()).toBe(qCount.value - 1);
        });
        it('return to assignment page', function() {
            element('a[href^="#/assignmentpage/"]').click();
            expect(browser().location().url()).toMatch(/\/assignmentpage\/./);
        });
    });
    describe('compare', function() {
        it('random compare', function() {
            element('a[href="#/quickcompare"]').click();
            element('#stepNext').click();
            element("div[ng-click=\"sideSelect($index, \'right\', crit.id);pick=\'right\'\"]").click();
            element("#stepSubmit").click();
            expect(element("li.alert.alert-success.text-center").text()).toBe("Script & Comparison updated");
        });
        it('compare answers', function() {
            element('a[ng-click="setType(\'discussion\');switchEdits(-1)"]').click();
            element('a#stepcompare:not(.ng-hide):first').click();
            element("div[ng-click=\"sideSelect($index, \'left\', crit.id);pick=\'left\'\"]").click();
            element("#stepSubmit").click();
            expect(element("li.alert.alert-success.text-center").text()).toBe("Script & Comparison updated");
        });
        it('user is logged out', function() {
            element('.dropdown-menu:last-child a').click();
            expect(browser().location().url()).toBe('/login');
            reset = false;
        });
    });
});
