// Directives for viewing PDF directly on a page, requires viewerjs:
// http://viewerjs.org/
(function() {
var module = angular.module('ubc.ctlt.acj.common.pdf', ['ui.bootstrap'])
	.run([ "$http", "$templateCache", function ($http, $templateCache){
		// load the template into cache - but this breaks the overlay, as the file will not load, so commenting it out
		// $http.get('modules/common/pdf-overlaid-template.html', {cache:$templateCache});
	}]);

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
		controller: ["$scope", "$log", "$sce", "$modal", function ($scope, $log, $sce, $modal) {
			$scope.pdfname = "";
			$scope.updatePDF = function (name) {
				if (name != $scope.pdfname) {
					$scope.pdfvisible = true;
					$scope.pdfname = name;
					$scope.pdfurl = $sce.trustAsResourceUrl(
						"/static/lib/pdfjs/web/viewer.html#../../../pdf/" +
						$scope.pdfname);
				}
				else {
					$scope.pdfvisible = !$scope.pdfvisible;
				}
			};
			$scope.openPDF = function (name) {
				$scope.file = 'pdf/' + name;
				$scope.title = 'Attached PDF: Use + and - to zoom';
				$modal.open({
					templateUrl: 'modules/common/pdf-overlaid-template.html',
					scope: $scope
				});
			}
		}]
	};
});

})();

