(function() {

    angular.module('ubc.ctlt.compair.common').directive('compairAvatar', function () {
        return {
            restrict: 'E',
            scope: {
                userId: '=',
                avatar: '=',
                displayName: '=?',
                fullName: '=?',
                me: '=?'
            },
            template: '<a ng-href="#/user/{{ userId }}">' +
                        '<img src="//www.gravatar.com/avatar/{{ avatar }}?s=32&d=retro" alt="" /> ' +
                      '</a>' +
                      '<a ng-href="#/user/{{ userId }}">' +
                        '{{ displayName }}' +
                        '<span ng-if="me">{{ displayName ? " (You)" : "You" }}</span>' +
                        '<span ng-if="fullName"> ({{ fullName }})</span>' +
                      '</a>'
        };
    });

})();
