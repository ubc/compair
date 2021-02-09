(function() {

angular.module('ubc.ctlt.compair.common').directive('compairAnswerAvatar', function () {
    return {
        restrict: 'E',
        scope: {
            answer: '=',
            skipName: '=',
            me: '=?'
        },
        template:   '<compair-user-avatar ng-if="answer.user_id" user="answer.user" skip-name="skipName" me="me"></compair-user-avatar>' +
                    '<compair-group-avatar ng-if="answer.group_id" group="answer.group" skip-name="skipName" me="me"></compair-group-avatar>'
    };
});


angular.module('ubc.ctlt.compair.common').directive('compairUserAvatar', function () {
    return {
        restrict: 'E',
        scope: {
            user: '=',
            skipName: '=?',
            me: '=?'
        },
        template:   '<a ng-href="#/user/{{ user.id }}">' +
                        '<img ng-src="//www.gravatar.com/avatar/{{ user.avatar }}?s=32&d=retro" alt="" /> ' +
                    '</a>' +
                    '<a ng-href="#/user/{{ user.id }}">' +
                        '<span ng-if="!skipName">{{ user.displayname }}</span>' +
                        '<span ng-if="me">{{ !!skipName ? "You" : " (You)" }}</span>' +
                        '<span ng-if="!skipName && user.fullname"> ({{ user.fullname }})</span>' +
                    '</a>'
    };
});

angular.module('ubc.ctlt.compair.common').directive('compairGroupAvatar', function () {
    return {
        restrict: 'E',
        scope: {
            group: '=',
            skipName: '=?',
            me: '=?'
        },
        template:   '<img ng-src="//www.gravatar.com/avatar/{{ group.avatar }}?s=32&d=retro" alt="" /> ' +
                    '<span ng-if="!skipName">{{ group.name }}</span>' +
                    '<span ng-if="me">{{ !!skipName ? "Your Group" : " (Your Group)" }}</span>'
    };
});

angular.module('ubc.ctlt.compair.common').directive('compairStudentAvatar', function () {
    return {
        restrict: 'E',
        scope: {
            user: '='
        },
        template:   '<a ng-href="#/user/{{ user.id }}">' +
                        '<img ng-src="//www.gravatar.com/avatar/{{ user.avatar }}?s=32&d=retro" alt="" /> ' +
                    '</a>' +
                    '<a ng-href="#/user/{{ user.id }}">' +
                        '{{ !!user.fullname? user.fullname : user.displayname }} {{ !!user.student_number? "(" + user.student_number + ")" : "" }}' +
                    '</a>'
    };
});

})();
