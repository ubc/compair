// Directives for viewing PDF directly on a page, requires viewerjs:
// http://viewerjs.org/
(function() {

var module = angular.module('ubc.ctlt.compair.common.attachment',
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
module.directive('compairAttachmentInline', function() {
    return {
        templateUrl: 'modules/common/attachment-inline-template.html',
        scope: {
            attachment: '=?',
            downloadName: '=?',
            //attachments: '=?',
            label: '@'
        },
        controller: [
                "$scope", "$log", "$window", "$sce", "$uibModal", "xAPIStatementHelper",
                function ($scope, $log, $window, $sce, $uibModal, xAPIStatementHelper) {
            $scope.inline = null;
            $scope.inlineVisible = false;
            $scope.inlineUrl = null;

            $scope.openAttachment = function (file) {
                var filepath = '/app/attachment/' + file.name;
                if (file.extension == 'pdf') {
                    var modalScope = $scope.$new();
                    modalScope.file = filepath;
                    modalScope.name = 'Attached PDF: Use + and - to zoom';
                    var modalInstance = $uibModal.open({
                        templateUrl: 'modules/common/attachment-overlaid-template.html',
                        scope: modalScope
                    });
                    modalInstance.opened.then(function() {
                        xAPIStatementHelper.opened_pdf_modal(name);
                    });
                    modalInstance.result.finally(function() {
                        xAPIStatementHelper.closed_pdf_modal(name);
                    });
                } else {
                    if ($scope.downloadName) {
                        filepath += "?name="+encodeURIComponent($scope.downloadName+'.'+file.extension);
                    }
                    $window.open(filepath);
                }
            };

            $scope.updateInline = function (file) {
                // only pdfs can be opened inline
                if (file.extension == 'pdf') {
                    if (file != $scope.inline) {
                        $scope.inlineVisible = true;
                        $scope.inline = file;
                        $scope.inlineUrl = $sce.trustAsResourceUrl("/app/lib_extension/pdfjs/web/viewer.html?file=/app/attachment/" + $scope.inline.name);
                    } else {
                        $scope.inlineVisible = !$scope.inlineVisible;
                    }

                    if ($scope.inlineVisible) {
                        xAPIStatementHelper.opened_inline_pdf($scope.inline.name)
                    } else {
                        xAPIStatementHelper.closed_inline_pdf($scope.inline.name)
                    }
                }
            };
        }]
    };
});

})();

