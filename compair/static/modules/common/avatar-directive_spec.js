describe('avatar-directive', function () {
    var $compile, $rootScope;

    beforeEach(module('ubc.ctlt.compair.common'));

    beforeEach(inject(function(_$compile_, _$rootScope_){
        $compile = _$compile_;
        $rootScope = _$rootScope_;
    }));

    it('should replace the element with the appropriate content', function() {
        $rootScope.$apply(function() {
            $rootScope.userId = "1abcABC123-abcABC123_Z";
            $rootScope.avatar = 'avatar-string';
            $rootScope.displayName = 'Optimus Prime';
        });
        element = angular.element(
            '<compair-avatar user-id="userId" avatar="avatar" main-identifier="displayName"></compair-avatar>'
        );
        $compile(element)($rootScope);
        $rootScope.$digest();

        expect(element.find('img').length).toBe(1);
        expect(element.find('img').attr('src')).toEqual('//www.gravatar.com/avatar/avatar-string?s=32&d=retro');
        expect(element.find('a').length).toBe(2);
        expect(element.find('a').attr('href')).toEqual('#/user/1abcABC123-abcABC123_Z');
        expect(element.find('span').length).toBe(0);
        expect(element.html()).toContain('Optimus Prime');
    });

    it('should show "(You)" if me is true', function() {
        $rootScope.$apply(function() {
            $rootScope.userId = "1abcABC123-abcABC123_Z";
            $rootScope.avatar = 'avatar-string';
            $rootScope.displayName = 'Optimus Prime';
        });
        element = angular.element(
            '<compair-avatar user-id="userId" avatar="avatar" main-identifier="displayName" me="true"></compair-avatar>'
        );
        $compile(element)($rootScope);
        $rootScope.$digest();

        expect(element.find('span').length).toBe(1);
        expect(element.find('span').text()).toEqual(' (You)');
        expect(element.html()).toContain('Optimus Prime');
    });

    it('should show "You" if me is true and no display name', function() {
        $rootScope.$apply(function() {
            $rootScope.userId = "1abcABC123-abcABC123_Z";
            $rootScope.avatar = 'avatar-string';
        });
        element = angular.element(
            '<compair-avatar user-id="userId" avatar="avatar" me="true"></compair-avatar>'
        );
        $compile(element)($rootScope);
        $rootScope.$digest();

        expect(element.find('span').length).toBe(1);
        expect(element.text()).toEqual(' You');
    });

    it('should show full name when provided', function() {
        $rootScope.$apply(function() {
            $rootScope.userId = "1abcABC123-abcABC123_Z";
            $rootScope.avatar = 'avatar-string';
            $rootScope.displayName = 'Optimus Prime';
            $rootScope.fullName = 'John Smith';
        });
        element = angular.element(
            '<compair-avatar user-id="userId" avatar="avatar" main-identifier="displayName" secondary-identifier="fullName"></compair-avatar>'
        );
        $compile(element)($rootScope);
        $rootScope.$digest();

        expect(element.find('span').length).toBe(1);
        expect(element.text()).toEqual(' Optimus Prime (John Smith)');
    });

    it('should not show full name if undefined', function() {
        $rootScope.$apply(function() {
            $rootScope.userId = "1abcABC123-abcABC123_Z";
            $rootScope.avatar = 'avatar-string';
            $rootScope.displayName = 'Optimus Prime';
        });
        element = angular.element(
            '<compair-avatar user-id="userId" avatar="avatar" main-identifier="displayName" secondary-identifier="fullName"></compair-avatar>'
        );
        $compile(element)($rootScope);
        $rootScope.$digest();

        expect(element.find('span').length).toBe(0);
        expect(element.text()).toEqual(' Optimus Prime');

    })
});
