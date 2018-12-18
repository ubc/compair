(function() {

var module = angular.module('ubc.ctlt.compair.attachment.image.viewer', []);

// Directive for viewing images with rotation.
// Based on https://github.com/fcrohas/angular-canvas-viewer
// Image source can be specified as url ('ng-src') or File/Blob object ('ng-model').
// In case of using File / Blob, rotatation will update the image object.
module.directive('imageViewer', ['$window', '$q',
    function($window, $q) {
        var template =
            '<div class="text-center image-viewer">' +
                '<div class="btn btn-sm btn-info" ng-click="rotate(-1)"><span class="fa fa-rotate-left"></span></div>' +
                '<div class="btn btn-sm btn-info" ng-click="rotate(1)"><span class="fa fa-rotate-right"></span></div>' +
                '<br/>' +
                '<span ng-if="!canvasLoaded"><i class="fa fa-spin fa-spinner"></i></span>' +
                '<br/>' +
                '<canvas class="attachment-view" ng-show="canvasLoaded" />' +
            '</div>';

        return {
            restrict: 'AE',
            replace: true,
            scope: {
                rotated: "=",
                src: '@?ngSrc',         // Can specify image as source URL...
                imgFile: '=?ngModel',   // ... or File / Blob object...
                onLoadCallback: '&?'    // callback when image loaded
            },
            template: template,
            link: function(scope, element, attributes) {
                scope.canvasLoaded = false;

                // default values
                scope.orientation = { rotate: 0, zoom: 1 };
                scope.options = { backgroundColor: 'transparent' };

                // round to nearest 90
                scope.orientation.rotate = Math.round(scope.orientation.rotate / 90.0) * 90;
                if ((scope.orientation.rotate <= -360) || (scope.orientation.rotate >= 360)) {
                    scope.orientation.rotate = 0;
                }

                var canvas = element.find('canvas')[0];
                var ctx = canvas.getContext("2d");
                var picPos = { x : 0, y : 0 };  // origin of the image

                var imgFileMimeType = scope.imgFile? scope.imgFile.type : 'image/png';
                var imgFileName = (scope.imgFile && scope.imgFile.name)? scope.imgFile.name : 'image.png'
                var img = new Image();
                img.onload = onLoadImage;

                // load image either by src URL or by selected file
                if (scope.src && typeof(scope.src) === 'string') {
                    img.src = scope.src;
                } else if (scope.imgFile) {
                    var reader = new FileReader();
                    reader.onload = function(event) {
                        img.src = event.target.result;
                    };
                    reader.readAsDataURL(scope.imgFile);
                }

                // for monitoring canvas resize
                function parentChange() {
                    return {
                        height: canvas.parentNode.clientHeight,
                        width: canvas.parentNode.clientWidth };
                }

                function onLoadImage() {
                    scope.canvasLoaded = true;

                    // TODO: parse EXIF data to auto rotate the image
                    resizeCanvas();

                    // start monitoring resize
                    scope.$watch(parentChange, function() {
                        resizeCanvas();
                    }, true);

                    refreshFileObj().then(function() {
                        if (scope.onLoadCallback) {
                            scope.onLoadCallback();
                        }
                    });
                }

                // https://stackoverflow.com/questions/4998908/convert-data-uri-to-file-then-append-to-formdata
                function dataUrlToBlob(dataUrl) {
                    // convert base64/URLEncoded data component to raw binary data held in a string
                    var byteString;
                    if (dataUrl.split(',')[0].indexOf('base64') >= 0) {
                        byteString = atob(dataUrl.split(',')[1]);
                    } else {
                        byteString = unescape(dataUrl.split(',')[1]);
                    }

                    // write the bytes of the string to a typed array
                    var ia = new Uint8Array(byteString.length);
                    for (var i = 0; i < byteString.length; i++) {
                        ia[i] = byteString.charCodeAt(i);
                    }

                    return new Blob([ia], {type: imgFileMimeType});
                }

                // Return a Promise with File object based on given data url
                function dataUrlToFile(dataUrl) {
                    /* Commented out for now.  Since not all browsers support the fetch function and
                       File constructor.  Will fake it with Blob object instead.
                       This works with AngularJS File Uploader.
                     */
                    // try {
                    //     // if browser has fetch function and can create new File object
                    //     if (typeof fetch === "function" && new File([], '')) {
                    //         return fetch(dataUrl)
                    //             .then(function (resp) { return resp.arrayBuffer(); })
                    //             .then(function (buffer) { return new File([buffer], imgFileName, { type: imgFileMimeType }); });
                    //     }
                    // } catch (err) {
                    //     // Ignore. Possible reason is IE / Edge don't have File constructor.
                    //     // Fallthrough to use Blob instead
                    // }

                    var tmpBlob = dataUrlToBlob(dataUrl);
                    var nowTime = Date.now();
                    tmpBlob.name = imgFileName;
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
                    picPos = {
                        x : centerX - (img.width * scope.orientation.zoom) / 2,
                        y : centerY - (img.height * scope.orientation.zoom) / 2
                    };
                };

                var resizeCanvas = function() {
                    var ratio = img.width / img.height;
                    var displayWidth = img.width;
                    var parent = $(canvas.parentNode);

                    if (Math.abs(scope.orientation.rotate) == 90 ||
                        Math.abs(scope.orientation.rotate) == 270) {
                        ratio = 1 / ratio;
                        displayWidth = img.height;
                    }
                    displayWidth = Math.min(displayWidth, parent.width());

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
                var rotateOriginalImage = function() {
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

                    return tempCanvas.toDataURL(imgFileMimeType);
                };

                angular.element($window).bind('resize', function() {
                    scope.$apply();
                });

                var refreshFileObj = function() {
                    // if imgFile is given, replace it with a new File object in current orientation
                    if (scope.imgFile) {
                        return dataUrlToFile(
                            rotateOriginalImage()
                        ).then(function (newFile) {
                            if (scope.imgFile.rotateDirty) {
                                newFile.rotateDirty = scope.imgFile.rotateDirty;
                            }
                            scope.imgFile = newFile;
                            if (scope.orientation.rotate !== 0) {
                                scope.rotated = true;
                            } else {
                                scope.rotated = false;
                            }
                            scope.$apply();
                        }, function() {
                            // do nothing if failed. use original image as-is
                        });
                    }

                    return Promise.resolve();
                };

                scope.rotate = function(direction) {
                    scope.$applyAsync(function(scope) {
                        if (scope.imgFile) {
                            scope.imgFile.rotateDirty = true;
                        }
                        scope.orientation.rotate += 90 * direction;
                        if ((scope.orientation.rotate <= -360) || (scope.orientation.rotate >= 360)) {
                            scope.orientation.rotate = 0;
                        }
                        resizeCanvas();
                        refreshFileObj();
                    });
                };
            },  // link
        };  // return
}]);


})();