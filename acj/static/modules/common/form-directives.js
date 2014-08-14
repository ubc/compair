// Holds directives used to make building forms easier
//
// Isolate this module's creation by putting it in an anonymous function
(function() {

var module = angular.module('ubc.ctlt.acj.common.form', []);

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

/***** Providers *****/
module.service('EditorOptions', function() {
	this.basic = 
	{
		language: 'en',
		disableInline: true,
		removeButtons: 'Anchor,Strike,Subscript,Superscript',
		toolbarGroups: [
			{ name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
			{ name: 'links' }
		]
	};

});

// End anonymous function
})();
