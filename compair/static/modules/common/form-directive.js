// Holds directives used to make building forms easier
//
// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.compair.common.form', ['ckeditor']);

/***** Directives *****/
// add the css and elements required to show bootstrap's validation feedback
// requires the parameter form-control, which passes in the input being validated
// and is-date, which when true prevents display of helper icon on required fields
module.directive('compairFieldWithFeedback', function() {
    return {
        restrict: 'E',
        scope: {
            formControl: '=',
            isDate: '='
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

/* prompt user when leaving page with unsaved work (applied only to forms for answers, comparisons, and self-evaulations) */
module.directive('confirmFormExit', ['Session', function(Session){
    return {
        require: 'form',
        link: function(scope, elem, attrs, formController) {
            //refresh
            window.onbeforeunload = function() {
                //when generic confirmation is needed regardless of form state
                if (scope.forcePreventExit && !Session.isImpersonating()) {
                    return "Are you sure you want to refresh this page? Any unsaved changed you've made will be lost.";
                }
                //when confirmation is for answer AND an answer has been written or file uploaded AND the user has not pressed submit
                else if (attrs.formType == 'answer' && (scope.answer.content || scope.uploader.queue.length) && scope.preventExit && formController.$dirty && !Session.isImpersonating()) {
                    return "Are you sure you want to refresh this page? Any unsaved changed you've made will be lost.";
                }
                //when confirmation is for comparison AND the user has not pressed submit
                else if (attrs.formType == 'compare' && scope.preventExit && formController.$dirty && !Session.isImpersonating()) {
                    return "Are you sure you want to refresh this page? Any unsaved work you've done for this round will be lost.";
                }
                //when confirmation is for comment AND the user has not pressed submit
                else if (attrs.formType == 'comment' && scope.preventExit && formController.$dirty && !Session.isImpersonating()) {
                    return "Are you sure you want to refresh this page? Any unsaved changed you've made will be lost.";
                }
            };
            // clean up event handlers
            scope.$on('$destroy', function() {
                window.onbeforeunload = function() {};
            });
            //change URL
            scope.$on('$locationChangeStart', function(event, next, current) {
                if (scope.forcePreventExit && !Session.isImpersonating()) {
                    if (!confirm("Are you sure you want to leave this page? Any unsaved changes you've made will be lost.")) {
                        event.preventDefault();
                        return;
                    }
                    if (scope.trackExited && typeof scope.trackExited === "function") {
                        scope.trackExited();
                    }
                } else if (attrs.formType == 'answer' && scope.preventExit && !Session.isImpersonating()) {
                    if ((scope.answer.content || scope.uploader.queue.length) && formController.$dirty) {
                        if (!confirm("Are you sure you want to leave this page? Any unsaved changes you've made will be lost.")) {
                            event.preventDefault();
                            return;
                        }
                    }
                    if (scope.trackExited && typeof scope.trackExited === "function") {
                        scope.trackExited();
                    }
                } else if (attrs.formType == 'compare' && scope.preventExit && !Session.isImpersonating()) {
                    if (formController.$dirty) {
                        if (!confirm("Are you sure you want to leave this page? Any unsaved work you've done for this round will be lost.")) {
                            event.preventDefault();
                            return;
                        }
                    }
                    if (scope.trackExited && typeof scope.trackExited === "function") {
                        scope.trackExited();
                    }
                } else if (attrs.formType == 'comment' && scope.preventExit && !Session.isImpersonating()) {
                    if (formController.$dirty) {
                        if (!confirm("Are you sure you want to leave this page? Any unsaved changes you've made will be lost.")) {
                            event.preventDefault();
                            return;
                        }
                    }
                    if (scope.trackExited && typeof scope.trackExited === "function") {
                        scope.trackExited();
                    }
                }
            });
        }
    };
}]);

/***** Providers *****/
module.service('EditorOptions', function() {
    // For complete reference see:
    // http://docs.ckeditor.com/#!/api/CKEDITOR.config
    this.basic = {
        // do not load external custom config file
        customConfig: '',
        // The toolbar groups arrangement, optimized for two toolbar rows.
        toolbarGroups: [
            { name: 'clipboard',   groups: [ 'clipboard', 'undo' ] },
            //{ name: 'editing',     groups: [ 'find', 'selection', 'spellchecker' ] },
            { name: 'insert' },
            { name: 'links' },
            { name: 'forms' },
            //{ name: 'tools' },
            //{ name: 'document',	   groups: [ 'mode', 'document', 'doctools' ] },
            { name: 'others' },
            '/',
            { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
            { name: 'paragraph',   groups: [ 'list', 'indent', 'blocks', 'align', 'bidi' ] },
            //{ name: 'styles' },
            { name: 'colors' }
            //{ name: 'about' }
        ],
        // Remove some buttons provided by the standard plugins, which are
        // not needed in the Standard(s) toolbar.
        removeButtons: 'Cut,Copy,Paste,PasteText,PasteFromWord,Font,Anchor',

        // Set the most common block elements.
        format_tags: 'p;h1;h2;h3;pre',

        // Simplify the dialog windows.
        removeDialogTabs: 'image:advanced;link:advanced',

        // change Code Snippet's theme
        codeSnippet_theme: 'foundation',

        linkShowTargetTab: false,

        height: "150px",

        // enable custom plugin that combines ASCIIMath and LaTeX math input and code highlighting
        extraPlugins: 'codesnippet,combinedmath,autolink'

    };
});

// End anonymous function
})();
