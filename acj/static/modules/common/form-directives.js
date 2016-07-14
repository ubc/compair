// Holds directives used to make building forms easier
//
// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.common.form', ['ckeditor']);

/***** Directives *****/
// add the css and elements required to show bootstrap's validation feedback
// requires the parameter form-control, which passes in the input being validated
module.directive('acjFieldWithFeedback', function() {
    return {
        restrict: 'E',
        scope: {
            formControl: '='
        },
        transclude: true,
        templateUrl: 'modules/common/form-field-with-feedback-template.html'
    };
});

/* check for matching passwords; can be modified to be more general to check for the matching of any fields*/
module.directive('pwMatch', function(){
    return {
        require: 'ngModel',
        link: function (scope, elem, attrs, ctrl) {
            var firstPassword = '#' + attrs.pwMatch;
            elem.add(firstPassword).on('keyup', function () {
                scope.$apply(function () {
                    var v = elem.val()===$(firstPassword).val();
                    ctrl.$setValidity('pwMatch', v);
                });
            });
        }
    }
});

/* prompt user when leaving page with unsaved work (applied only to forms for creating answer, creating comparison) */
module.directive('confirmFormExit', function(){
        return {
        link: function(scope, elem, attrs) {
            //refresh
            window.onbeforeunload = function() {
                //when confirmation is for answer AND an answer has been written or PDF file uploaded AND the user has not pressed submit
                if (attrs.formType == 'answer' && (scope.answer.content || scope.uploader.queue.length) && scope.preventExit) {
                    return "Do you want to refresh this page without saving? Any answering you've done will be lost.";
                }
                //when confirmation is for comparison AND the user has not pressed submit
                if (attrs.formType == 'compare' && scope.preventExit) {
                    return "Do you want to refresh this page without saving? Any work you've done for this answer pair will be lost.";
                }
            }
            //change URL
            scope.$on('$locationChangeStart', function(event, next, current) {
                if (attrs.formType == 'answer' && (scope.answer.content || scope.uploader.queue.length) && scope.preventExit) {
                    if (!confirm("Do you want to leave this page without saving? Any answering you've done will be lost.")) {
                        event.preventDefault();
                    }
                }
                if (attrs.formType == 'compare' && scope.preventExit) {
                    if (!confirm("Do you want to leave this page without saving? Any work you've done for this answer pair will be lost.")) {
                        event.preventDefault();
                    }
                }
            });
        }
        };
});

/***** Providers *****/
module.service('EditorOptions', function() {
    this.basic = {
        customConfig: '../../lib_extension/ckeditor/config.js'
    };
});

// End anonymous function
})();
