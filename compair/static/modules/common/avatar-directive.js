(function() {

    angular.module('ubc.ctlt.compair.common').directive('compairAvatar', function () {
        return {
            restrict: 'E',
            scope: {
                userId: '=',
                avatar: '=',
                mainIdentifier: '=?',
                secondaryIdentifier: '=?',
                me: '=?'
            },
            template: '<a ng-href="#/user/{{ userId }}">' +
                        '<img src="//www.gravatar.com/avatar/{{ avatar }}?s=32&d=retro" alt="" /> ' +
                      '</a>' +
                      '<a ng-href="#/user/{{ userId }}">' +
                        '{{ mainIdentifier }}' +
                        '<span ng-if="me">{{ mainIdentifier ? " (You)" : "You" }}</span>' +
                        '<span ng-if="secondaryIdentifier"> ({{ secondaryIdentifier }})</span>' +
                      '</a>'
        };
    });

})();
