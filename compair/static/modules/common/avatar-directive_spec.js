describe('avatar-directive', function () {
    var $compile, $rootScope;

    var mockStudent = {
        "id": "1abcABC123-abcABC123_Z",
        "avatar": "63a9f0ea7bb98050796b649e85481845",
        "created": "Tue, 27 May 2014 00:02:38 -0000",
        "displayname": "student1",
        "email": null,
        "firstname": "John",
        "fullname": "John Smith",
        "fullname_sortable": 'Smith, John',
        "lastname": "Smith",
        "last_online": "Tue, 12 Aug 2014 20:53:31 -0000",
        "modified": "Tue, 12 Aug 2014 20:53:31 -0000",
        "username": "root",
        "system_role": "Student",
        "uses_compair_login": true,
        "student_number": "1234567890",
        "email_notification_method": 'enable'
    }

    var mockAnswerWithUser = {
        "assignment_id": "1abcABC123-abcABC123_Z",
        "course_id": "1abcABC123-abcABC123_Z",
        "comment_count": 0,
        "content": "<p>I&#39;m the instructor</p>\n",
        "course_id": "1abcABC123-abcABC123_Z",
        "created": "Mon, 06 Jun 2016 21:07:57 -0000",
        "file": null,
        "top_answer": false,
        "id": "12bcABC123-abcABC123_Z",
        "private_comment_count": 0,
        "public_comment_count": 0,
        "score": null,
        "user": {
            "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
            "displayname": "student one",
            "fullname": "thkx UeNV",
            "fullname_sortable": "UeNV, thkx",
            "student_number": "1234567890",
            "id": "1abcABC123-abcABC123_Z"
        },
        "user_id": "1abcABC123-abcABC123_Z",
        "group": null,
        "group_id": null
    };

    var mockAnswerWithPartialUser = {
        "assignment_id": "1abcABC123-abcABC123_Z",
        "course_id": "1abcABC123-abcABC123_Z",
        "comment_count": 0,
        "content": "<p>I&#39;m the instructor</p>\n",
        "course_id": "1abcABC123-abcABC123_Z",
        "created": "Mon, 06 Jun 2016 21:07:57 -0000",
        "file": null,
        "top_answer": false,
        "id": "12bcABC123-abcABC123_Z",
        "private_comment_count": 0,
        "public_comment_count": 0,
        "score": null,
        "user": {
            "avatar": "9445e064ca06f7de8c2f0689ef6b9e8b",
            "displayname": "student one",
            "id": "1abcABC123-abcABC123_Z"
        },
        "user_id": "1abcABC123-abcABC123_Z",
        "group": null,
        "group_id": null
    };

    var mockGroupAnswer = {
        "assignment_id": "1abcABC123-abcABC123_Z",
        "course_id": "1abcABC123-abcABC123_Z",
        "comment_count": 0,
        "content": "<p>I&#39;m the instructor</p>\n",
        "course_id": "1abcABC123-abcABC123_Z",
        "created": "Mon, 06 Jun 2016 21:07:57 -0000",
        "file": null,
        "top_answer": false,
        "id": "12bcABC123-abcABC123_Z",
        "private_comment_count": 0,
        "public_comment_count": 0,
        "score": null,
        "user": null,
        "user_id": null,
        "group": {
            "id": "1abcABC123-abcABC123_Z",
            "avatar": "0445e064ca06f7de8c2f0689ef6b9e8b",
            "name": "Group 1",
        },
        "group_id": "1abcABC123-abcABC123_Z"
    };

    beforeEach(module('ubc.ctlt.compair.common'));

    beforeEach(inject(function(_$compile_, _$rootScope_){
        $compile = _$compile_;
        $rootScope = _$rootScope_;
    }));

    describe('compair-answer-avatar', function () {
        describe('for group answer', function () {
            beforeEach(function() {
                $rootScope.$apply(function() {
                    $rootScope.answer = angular.copy(mockGroupAnswer);
                });
            });

            it('should replace the element with the appropriate content', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(0);
                expect(element.text()).toEqual(' Group 1');
            });

            it('should show "(Your Group)" if me is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" me="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(0);
                expect(element.text()).toEqual(' Group 1 (Your Group)');
            });

            it('should show only avatar if skip-name is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" skip-name="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(0);
                expect(element.text()).toEqual(' ');
            });

            it('should show "Your Group" if me is true and skip-name is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" skip-name="true" me="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(0);
                expect(element.text()).toEqual(' Your Group');
            });
        });

        describe('for individual answer with partial user information', function () {
            beforeEach(function() {
                $rootScope.$apply(function() {
                    $rootScope.answer = angular.copy(mockAnswerWithPartialUser);
                });
            });

            it('should replace the element with the appropriate content', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one');
            });

            it('should show "(You)" if me is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" me="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one (You)');
            });

            it('should show only avatar if skip-name is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" skip-name="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' ');
            });

            it('should show "You" if me is true and skip-name is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" skip-name="true" me="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' You');
            });
        });

        describe('for individual answer with full user information', function () {
            beforeEach(function() {
                $rootScope.$apply(function() {
                    $rootScope.answer = angular.copy(mockAnswerWithUser);
                });
            });

            it('should replace the element with the appropriate content', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one (thkx UeNV)');
            });

            it('should show "(You)" if me is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" me="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one (You) (thkx UeNV)');
            });

            it('should show only avatar if skip-name is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" skip-name="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.find('span').length).toBe(0);
                expect(element.text()).toEqual(' ');
            });

            it('should show "You" if me is true and skip-name is true', function() {
                element = angular.element(
                    '<compair-answer-avatar answer="answer" skip-name="true" me="true"></compair-answer-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' You');
            });
        });
    });

    describe('compair-group-avatar', function () {
        beforeEach(function() {
            $rootScope.$apply(function() {
                $rootScope.group = angular.copy(mockGroupAnswer.group);
            });
        });

        it('should replace the element with the appropriate content', function() {
            element = angular.element(
                '<compair-group-avatar group="group"></compair-group-avatar>'
            );
            $compile(element)($rootScope);
            $rootScope.$digest();

            expect(element.find('img').length).toBe(1);
            expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
            expect(element.find('a').length).toBe(0);
            expect(element.text()).toEqual(' Group 1');
        });

        it('should show "(Your Group)" if me is true', function() {
            element = angular.element(
                '<compair-group-avatar group="group" me="true"></compair-group-avatar>'
            );
            $compile(element)($rootScope);
            $rootScope.$digest();

            expect(element.find('img').length).toBe(1);
            expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
            expect(element.find('a').length).toBe(0);
            expect(element.text()).toEqual(' Group 1 (Your Group)');
        });

        it('should only avatar skip-name is true', function() {
            element = angular.element(
                '<compair-group-avatar group="group" skip-name="true"></compair-group-avatar>'
            );
            $compile(element)($rootScope);
            $rootScope.$digest();

            expect(element.find('img').length).toBe(1);
            expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
            expect(element.find('a').length).toBe(0);
            expect(element.text()).toEqual(' ');
        });

        it('should show "Your Group" if me is true and skip-name is true', function() {
            element = angular.element(
                '<compair-group-avatar group="group" skip-name="true" me="true"></compair-group-avatar>'
            );
            $compile(element)($rootScope);
            $rootScope.$digest();

            expect(element.find('img').length).toBe(1);
            expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/0445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
            expect(element.find('a').length).toBe(0);
            expect(element.text()).toEqual(' Your Group');
        });
    });

    describe('compair-user-avatar', function () {
        describe('with partial user information', function () {
            beforeEach(function() {
                $rootScope.$apply(function() {
                    $rootScope.user = angular.copy(mockAnswerWithPartialUser.user);
                });
            });

            it('should replace the element with the appropriate content', function() {
                element = angular.element(
                    '<compair-user-avatar user="user"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one');
            });

            it('should show "(You)" if me is true', function() {
                element = angular.element(
                    '<compair-user-avatar user="user" me="true"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one (You)');
            });

            it('should show only avatar if skip-name is true', function() {
                element = angular.element(
                    '<compair-user-avatar user="user" skip-name="true"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' ');
            });

            it('should show "You" if me is true and skip-name is true', function() {
                element = angular.element(
                    '<compair-user-avatar user="user" skip-name="true" me="true"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' You');
            });
        });

        describe('with full user information', function () {
            beforeEach(function() {
                $rootScope.$apply(function() {
                    $rootScope.user = angular.copy(mockAnswerWithUser.user);
                });
            });

            it('should replace the element with the appropriate content', function() {
                element = angular.element(
                    '<compair-user-avatar user="user"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one (thkx UeNV)');
            });

            it('should show "(You)" if me is true', function() {
                element = angular.element(
                    '<compair-user-avatar user="user" me="true"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' student one (You) (thkx UeNV)');
            });

            it('should show only avatar if skip-name is true', function() {
                element = angular.element(
                    '<compair-user-avatar user="user" skip-name="true"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' ');
            });

            it('should show "You" if me is true and skip-name is true', function() {
                element = angular.element(
                    '<compair-user-avatar user="user" skip-name="true" me="true"></compair-user-avatar>'
                );
                $compile(element)($rootScope);
                $rootScope.$digest();

                expect(element.find('img').length).toBe(1);
                expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/9445e064ca06f7de8c2f0689ef6b9e8b?s=32&d=retro');
                expect(element.find('a').length).toBe(2);
                expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
                expect(element.text()).toEqual(' You');
            });
        });
    });

    describe('compair-student-avatar', function () {
        beforeEach(function() {
            $rootScope.$apply(function() {
                $rootScope.user = angular.copy(mockStudent);
            });
        });

        it('should replace the element with the appropriate content', function() {
            element = angular.element(
                '<compair-student-avatar user="user"></compair-group-avatar>'
            );
            $compile(element)($rootScope);
            $rootScope.$digest();

            expect(element.find('img').length).toBe(1);
            expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/63a9f0ea7bb98050796b649e85481845?s=32&d=retro');
            expect(element.find('a').length).toBe(2);
            expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
            expect(element.text()).toEqual(' John Smith (1234567890)');
        });
    });
});
