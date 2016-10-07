// Directives for viewing PDF directly on a page, requires viewerjs:
// http://viewerjs.org/
(function() {

var module = angular.module('ubc.ctlt.compair.common.pdf',
    [
        'ui.bootstrap',
        'ubc.ctlt.compair.common.xapi'
    ]
);

module.run([ "$http", "$templateCache", function ($http, $templateCache){
    // load the template into cache - but this breaks the overlay, as the file will not load, so commenting it out
    // $http.get('modules/common/pdf-overlaid-template.html', {cache:$templateCache});
}]);

// Display a PDF in a viewerjs iframe.
// Assumes that all PDF files are in the static/pdf directory in compair
// Requires 2 parameters:
// pdfs - a list of PDF files, required to be an array of hashes like:
//	[{'name':'pdf file name on the server', 'alias':'the pdf file original name'},{...}]
// label - instruction text shown to user before list of files
module.directive('compairPdfInline', function() {
    return {
        templateUrl: 'modules/common/pdf-inline-template.html',
        scope: {
            pdf: '=?',
            pdfs: '=?',
            label: '@'
        },
        controller: [
                "$scope", "$log", "$sce", "$modal", "xAPIStatementHelper",
                function ($scope, $log, $sce, $modal, xAPIStatementHelper) {
            $scope.pdfname = "";
            $scope.updatePDF = function (name) {
                if (name != $scope.pdfname) {
                    $scope.pdfvisible = true;
                    $scope.pdfname = name;
                    $scope.pdfurl = $sce.trustAsResourceUrl(
                        "/app/lib_extension/pdfjs/web/viewer.html#/app/pdf/" +
                        $scope.pdfname);
                } else {
                    $scope.pdfvisible = !$scope.pdfvisible;
                }

                if ($scope.pdfvisible) {
                    xAPIStatementHelper.opened_inline_pdf($scope.pdfname)
                } else {
                    xAPIStatementHelper.closed_inline_pdf($scope.pdfname)
                }
            };
            $scope.openPDF = function (name) {
                $scope.file = '/app/pdf/' + name;
                $scope.name = 'Attached PDF: Use + and - to zoom';
                var modalInstance = $modal.open({
                    templateUrl: 'modules/common/pdf-overlaid-template.html',
                    scope: $scope
                });
                modalInstance.opened.then(function() {
                    xAPIStatementHelper.opened_pdf_modal(name);
                });
                modalInstance.result.finally(function() {
                    xAPIStatementHelper.closed_pdf_modal(name);
                });
            }
        }]
    };
});

})();

