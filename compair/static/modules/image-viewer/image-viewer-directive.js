(function() {

var module = angular.module('ubc.ctlt.compair.image.viewer', []);

// Directive for viewing images with rotation
// Simplified version of https://github.com/fcrohas/angular-canvas-viewer
module.directive('imageViewer', ['$window', '$q',
    function($window, $q) {
        var template =
            '<div class="text-center image-viewer">' +
                '<div class="btn btn-sm btn-info" ng-click="rotate(-1)"><span class="fa fa-rotate-left"></span></div>'+
                '<div class="btn btn-sm btn-info" ng-click="rotate(1)"><span class="fa fa-rotate-right"></span></div>'+
                '<br/>' +
                '<i class="fa fa-spin fa-spinner" ng-show="!canvasLoaded"></i>' +
                '<canvas class="attachment-view" ng-show="canvasLoaded" />'+
            '</div>';

        return {
            restrict: 'A',
            replace: true,
            scope: {
                src: '@?ngSrc',     // Can specify image as source URL...
                imgFile: '<?',      // ... or File / Blob object...
                orientation: '=?',  // Orientation of current view
                uploadFile: '=?',   // File object of original image oriented as current view
                options: '<?',
                onLoadCallback: '&?'   // callback when image loaded
            },
            template: template,
            link: function(scope, element, attributes) {
                scope.canvasLoaded = false;

                // default values
                _.defaults(scope.orientation, { rotate: 0, zoom: 1});
                scope.options = $.extend({
                    backgroundColor: 'transparent',
                }, scope.options);

                // round to nearest 90
                scope.orientation.rotate = Math.round(scope.orientation.rotate / 90.0) * 90;
                if ((scope.orientation.rotate <= -360) || (scope.orientation.rotate >= 360)) {
                    scope.orientation.rotate = 0;
                }

                var canvas = element.find('canvas')[0];
                var ctx = canvas.getContext("2d");
                var picPos = { x : 0, y : 0 };  // origin of the image

                var uploadFileMimeType = scope.imgFile? scope.imgFile.type : 'image/png';
                var img = new Image();
                img.onload = onLoadImage;

                // load image either by src URL or by selected file
                if (scope.src && typeof(scope.src) === 'string') {
                    img.src = scope.src;
                } else if (scope.imgFile) {
                    var reader = new FileReader();
                    reader.onload = onLoadFile;
                    reader.readAsDataURL(scope.imgFile);
                }

                // for monitoring canvas resize
                function parentChange() {
                    return {
                        height: canvas.parentNode.clientHeight,
                        width: canvas.parentNode.clientWidth };
                }

                function onLoadFile(event) {
                    img.src = event.target.result;
                }

                function onLoadImage() {
                    scope.canvasLoaded = true;

                    // TODO: parse EXIF data to auto rotate the image
                    resizeCanvas();

                    // start monitoring resize
                    scope.$watch(parentChange, function() {
                        resizeCanvas();
                    }, true);

                    refreshUploadFile().then(function() {
                        if (scope.onLoadCallback) {
                            scope.onLoadCallback();
                        }
                    });
                }

                // https://stackoverflow.com/questions/4998908/convert-data-uri-to-file-then-append-to-formdata
                function dataUrlToBlob(dataUrl, mimeType) {
                    // convert base64/URLEncoded data component to raw binary data held in a string
                    var byteString;
                    if (dataUrl.split(',')[0].indexOf('base64') >= 0)
                        byteString = atob(dataUrl.split(',')[1]);
                    else
                        byteString = unescape(dataUrl.split(',')[1]);

                    // separate out the mime component
                    var mimeString = dataUrl.split(',')[0].split(':')[1].split(';')[0];

                    // write the bytes of the string to a typed array
                    var ia = new Uint8Array(byteString.length);
                    for (var i = 0; i < byteString.length; i++) {
                        ia[i] = byteString.charCodeAt(i);
                    }

                    return new Blob([ia], {type: mimeType});
                }

                // Return a Promise with File object based on given data url
                function dataUrlToFile(dataUrl, fileName, mimeType) {
                    try {
                        // if browser has fetch function and can create new File object
                        if (typeof fetch === "function" && new File([], '')) {
                            return fetch(dataUrl)
                                .then(function (resp) { return resp.arrayBuffer(); })
                                .then(function (buffer) { return new File([buffer], fileName, { type: mimeType }); });
                        }
                    } catch (err) {
                        // Ignore. Possible reason is IE / Edge don't have File constructor.
                        // Fallthrough to use Blob instead
                    }

                    // When all things fail, fake it with a Blob object. It works with AngularJS file uploader.
                    var tmpBlob = dataUrlToBlob(dataUrl, mimeType);
                    var nowTime = Date.now();
                    tmpBlob.name = fileName;
                    tmpBlob.lastModifiedDate = new Date(nowTime);
                    tmpBlob.lastModified = nowTime;
                    return Promise.resolve(tmpBlob);
                };

                // calculate the max zoom to fit the whole image within canvas
                var getMaxZoom = function(image, displayWidth, rotate) {
                    var zoom;
                    if (Math.abs(rotate) == 90 ||
                        Math.abs(rotate) == 270) {
                        zoom = displayWidth / image.height;
                    } else {
                        zoom = displayWidth / image.width;
                    }
                    return zoom;
                };

                var applyTransform = function() {
                    if (!img.complete) return;

                    var orientation = scope.orientation;
                    var centerX = img.width * orientation.zoom/2;
                    var centerY = img.height * orientation.zoom/2;
                    // Clean before draw
                    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                    ctx.fillStyle = scope.options.backgroundColor;
                    ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                    // Save context
                    ctx.save();
                    ctx.translate((picPos.x + centerX), (picPos.y + centerY));
                    // Rotate canvas
                    ctx.rotate(orientation.rotate * Math.PI/180);
                    // Go back
                    ctx.translate(-centerX, -centerY);
                    ctx.scale(orientation.zoom , orientation.zoom);
                    ctx.drawImage(img, 0, 0, img.width, img.height);
                    // Restore
                    ctx.restore();
                };

                var centerImg = function() {
                    var centerX = canvas.width / 2;
                    var centerY = canvas.height / 2;
                    var picPosX = 0;
                    var picPosY = 0;
                    picPosX =  centerX - (img.width * scope.orientation.zoom) / 2;
                    picPosY = centerY - (img.height * scope.orientation.zoom) / 2;
                    picPos = { x : picPosX, y : picPosY };
                };

                var resizeCanvas = function() {
                    var ratio = img.width / img.height;
                    var displayWidth = img.width;
                    var parent = canvas.parentNode;

                    if (Math.abs(scope.orientation.rotate) == 90 ||
                        Math.abs(scope.orientation.rotate) == 270) {
                        ratio = 1 / ratio;
                        displayWidth = img.height;
                    }
                    // scale the canvas to be slightly smaller than parent (by 10px).
                    // if using same size as parent, Firefox will go into
                    // infinite loop to expand parent -> resizeCanvas -> expand parent...
                    displayWidth = Math.max(0, Math.min(displayWidth, parent.clientWidth) - 10);

                    // scale down the image to fit if necessary
                    scope.orientation.zoom = Math.min(getMaxZoom(img, displayWidth, scope.orientation.rotate), 1);

                    scope.$applyAsync(function() {
                        canvas.width  = displayWidth;
                        canvas.height = canvas.width / ratio;
                        centerImg();
                        applyTransform();
                    });
                };

                // return a data URL of the original image with viewing rotation
                var rotateOriginalImage = function(mimeType) {
                    // use an invisible canvas to rotate the original image
                    var tempCanvas = document.createElement("canvas");
                    var tempCtx = tempCanvas.getContext("2d");

                    if (Math.abs(scope.orientation.rotate) == 90 ||
                        Math.abs(scope.orientation.rotate) == 270) {
                        tempCanvas.width = img.height;
                        tempCanvas.height = img.width;
                    } else {
                        tempCanvas.width = img.width;
                        tempCanvas.height = img.height;
                    }

                    var centerX=tempCanvas.width/2, centerY=tempCanvas.height/2;

                    tempCtx.save();
                    tempCtx.translate(centerX, centerY);
                    tempCtx.rotate(scope.orientation.rotate * Math.PI/180);
                    if (Math.abs(scope.orientation.rotate) == 90 ||
                        Math.abs(scope.orientation.rotate) == 270) {
                        tempCtx.translate(-centerY, -centerX);
                    } else {
                        tempCtx.translate(-centerX, -centerY);
                    }
                    tempCtx.drawImage(img, 0, 0, img.width, img.height)
                    tempCtx.restore();

                    return tempCanvas.toDataURL(mimeType);
                };

                angular.element($window).bind('resize', function() {
                    scope.$apply();
                });

                var refreshUploadFile = function() {
                    // if uploadFile is given, replace it with a new File object in current orientation
                    if (scope.uploadFile) {
                        return dataUrlToFile(rotateOriginalImage(uploadFileMimeType),
                            scope.uploadFile.name? scope.uploadFile.name : 'image.png',
                            uploadFileMimeType
                        ).then(function (newFile) {
                            scope.uploadFile = newFile;
                            scope.$apply();
                        }, function() {
                            // do nothing if failed. use original image as-is
                        });
                    }

                    return Promise.resolve();
                };

                scope.rotate = function(direction) {
                    scope.$applyAsync(function(scope) {
                        scope.orientation.rotate += 90 * direction;
                        if ((scope.orientation.rotate <= -360) || (scope.orientation.rotate >= 360)) {
                            scope.orientation.rotate = 0;
                        }
                        resizeCanvas();
                        refreshUploadFile();
                    });
                };
            },  // link
        };  // return
}]);


})();