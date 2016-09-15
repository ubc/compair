describe('criterion-module', function () {
    var $httpBackend;

    beforeEach(module('ubc.ctlt.acj.criterion'));
    beforeEach(module('modules/criterion/criterion-form-partial.html',
        'modules/common/form-field-with-feedback-template.html'));
    beforeEach(function () {
        module('ckeditor', function ($provide) {
            $provide.factory('ckeditorDirective', function () {
                return {  };
            })
        });
    });

    beforeEach(inject(function ($injector) {
        $httpBackend = $injector.get('$httpBackend');
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('criterion-form-directive', function () {
        var element, scope, directiveScope;
        beforeEach(inject(function ($rootScope) {
            scope = $rootScope;
        }));

        describe('with criterion binding', function() {
            beforeEach(inject(function ($compile) {
                scope.criterion = {};
                element = angular.element(
                    '<criterion-form criterion=criterion></criterion-form>'
                );
                $compile(element)(scope);
                scope.$digest();

                directiveScope = element.isolateScope();
            }));

            it('should bind criterion from parent scope', function() {
                scope.$apply(function() {
                    scope.criterion.name = 'Test';
                    scope.criterion.description = 'description'
                });

                expect(directiveScope.criterion.name).toEqual('Test');
                expect(directiveScope.criterion.description).toEqual('description');
            });

            it('should emit CRITERION_UPDATED event when click on submit', function() {
                spyOn(directiveScope, '$emit');
                var response = {
                    id: "1abcABC123-abcABC123_Z",
                    name: 'Test',
                    description: 'description'
                };
                scope.$apply(function() {
                    angular.copy(response, scope.criterion)
                });
                $httpBackend.expectPOST('/api/criteria/1abcABC123-abcABC123_Z', directiveScope.criterion).respond(response);

                directiveScope.criterionSubmit();
                $httpBackend.flush();

                expect(directiveScope.$emit).toHaveBeenCalledWith('CRITERION_UPDATED', jasmine.objectContaining(response));
            })
        });

        describe('without criterion binding', function() {
            beforeEach(inject(function ($compile) {
                scope.criterion = {name:'Test'};

                element = angular.element(
                    '<criterion-form></criterion-form>'
                );
                $compile(element)(scope);
                scope.$digest();

                directiveScope = element.isolateScope();
            }));

            it('should render and create form with disabled button', function() {
                expect(element.find('ng-form[name=criterionForm]').length).toBe(1);
                expect(element.find('#criterionName').length).toBe(1);
                expect(element.find('#criterionDescription').length).toBe(1);
                expect(element.find('input[type=button]').length).toBe(1);
                expect(element.find('input[type=button]').eq(0)).toHaveAttr('disabled', 'disabled');
                expect(directiveScope.criterionSubmitted).toBe(false);
            });

            describe('with form content', function() {
                beforeEach(function() {
                    scope.$apply(function() {
                        directiveScope.criterion = {
                            name: 'Test',
                            description: 'description'
                        }
                    });
                    spyOn(directiveScope, '$emit');
                });

                it('should enabled submit button and be able to submit', function() {
                    expect(element.find('input[type=button]').eq(0)).not.toHaveAttr('disabled', 'disabled');

                    var response = angular.merge({}, directiveScope.criterion, {id: "2abcABC123-abcABC123_Z"});
                    $httpBackend.expectPOST('/api/criteria', directiveScope.criterion).respond(response);

                    directiveScope.criterionSubmit();
                    expect(directiveScope.criterionSubmitted).toBe(true);

                    $httpBackend.flush();

                    expect(directiveScope.criterionSubmitted).toBe(false);
                    expect(directiveScope.criterion).toEqual({name:'', description:'', default: false});
                    expect(directiveScope.$emit).toHaveBeenCalledWith('CRITERION_ADDED', jasmine.objectContaining(response));
                });

                it('should reset criterionSubmitted flag when failed submitting', function() {
                    $httpBackend.whenPOST('/api/criteria', directiveScope.criterion).respond(400);

                    directiveScope.criterionSubmit();
                    expect(directiveScope.criterionSubmitted).toBe(true);

                    $httpBackend.flush();

                    expect(directiveScope.criterionSubmitted).toBe(false);
                    expect(directiveScope.criterion).toEqual({name: 'Test', description: 'description'});
                    expect(directiveScope.$emit).not.toHaveBeenCalled();
                })
            })
        });
    });
});
