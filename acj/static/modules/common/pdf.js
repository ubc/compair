// Directives for viewing PDF directly on a page, requires viewerjs:
// http://viewerjs.org/
(function() {
var module = angular.module('ubc.ctlt.acj.common.pdf', []);

// Display a PDF in a viewerjs iframe.
// Assumes that all PDF files are in the static/pdf directory in ACJ
// Requires 2 parameters:
// pdfs - a list of PDF files, required to be an array of hashes like:
//	[{'name':'pdf file name on the server', 'alias':'the pdf file original name'},{...}]
// label - instruction text shown to user before list of files
module.directive('acjPdfInline', function() {
	return {
		templateUrl: 'modules/common/pdf-inline-template.html',
		scope: {
			pdfs: '=',
			label: '@'
		},
		controller: function ($scope, $log, $sce) {
			$scope.pdfname = "";
			$scope.updatePDF = function (name) {
				if (name != $scope.pdfname) {
					$scope.pdfvisible = true;
					$scope.pdfname = name;
					$scope.pdfurl = $sce.trustAsResourceUrl(
						"/static/lib/viewerjs/index.html#../../pdf/" + 
						$scope.pdfname);
				}
				else {
					$scope.pdfvisible = !$scope.pdfvisible;
				}
			};
		}
	};
});

})();

