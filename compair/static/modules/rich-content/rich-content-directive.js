(function() {

var module = angular.module('ubc.ctlt.compair.rich.content',
    [
        'Kaltura.directives',
        'ui.bootstrap',
        'ubc.ctlt.compair.learning_records.learning_record',
        'ubc.ctlt.compair.rich.content.mathjax',
        'ubc.ctlt.compair.rich.content.highlightjs',
        'ubc.ctlt.compair.rich.content.twttr',
        'ubc.ctlt.compair.attachment.image.viewer',
    ]
);


module.constant('embedRegexpPatterns', {
    // files
    basicVideo   : /((?:https?|ftp|file):\/\/\S*\.(?:ogv|webm|mp4)(\?([\w=&_%\-]*))?)/gi,
    basicAudio   : /((?:https?|ftp|file):\/\/\S*\.(?:wav|mp3|ogg)(\?([\w=&_%\-]*))?)/gi,
    basicImage   : /((?:https?|ftp|file):\/\/\S*\.(?:gif|jpg|jpeg|tiff|png|svg|webp)(\?([\w=&_%\-]*))?)/gi,
    pdf          : /((?:https?|ftp|file):\/\/\S*\.(?:pdf)(\?([\w=&_%\-]*))?)/gi,
    // audio
    soundCloud   : /soundcloud.com\/[a-zA-Z0-9-_]+\/[a-zA-Z0-9-_]+/gi,
    spotify      : /spotify.com\/track\/[a-zA-Z0-9_]+/gi,
    // video
    vimeo        : /vimeo.com\/(?:channels\/(?:\w+\/)?|groups\/([^\/]*)\/videos\/|album\/(\d+)\/video\/|)(\d+)(?:$|\/|\?)*/gi,
    youtube      : /(?:[0-9A-Z-]+\.)?(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/ytscreeningroom\?v=|\/feeds\/api\/videos\/|\/user\S*[^\w\-\s]|\S*[^\w\-\s]))([\w\-]{11})[?=&+%\w-]*/gi,
    // social media
    twitter      : /https:\/\/twitter\.com\/\w+\/\w+\/\d+/gi
});

// Modified version of https://github.com/ritz078/ng-embed
// made to work with html link tags and to produce a list of items to be processed elsewhere
module.factory("embeddableRichContent",
    ["$q", "$http", "$sce", "embedRegexpPatterns",
    function ($q, $http, $sce, embedRegexpPatterns)
    {
        var pdfEmbed = function(url) {
            var embed =
                '<iframe src="' + url + '" class="content-item embed-responsive-item" '+
                'allowfullscreen webkitallowfullscreen></iframe>';
            return $sce.trustAsHtml(embed);
        }

        var soundCloudEmbed = function(url) {
            var url = embedRegexpPatterns.soundCloud.exec(url)[0];
            var embed =
                '<iframe height="160" scrolling="no" ' +
                'src="https://w.soundcloud.com/player/?url=https://' + url + '&auto_play=false&hide_related=true&'+
                'show_comments=false&show_user=false&show_reposts=false&visual=false&download=false&'+
                'color=f50000&theme_color=f50000" frameborder="0" class="content-item"></iframe>';
            return $sce.trustAsHtml(embed);
        }

        var spotifyEmbed = function(url) {
            var track = embedRegexpPatterns.spotify.exec(url)[0].split('/')[2];
            var embed =
                '<iframe src="https://embed.spotify.com/?uri=spotify:track:'+track+'" '+
                'frameborder="0" allowtransparency="true" class="content-item"></iframe>' +
                '</div>';
            return $sce.trustAsHtml(embed);
        }

        var vimeoEmbed = function(url) {
            var videoId = embedRegexpPatterns.vimeo.exec(url)[3];
            var embed =
                '<iframe src="//player.vimeo.com/video/' + videoId + '?title=0&byline=0&portrait=0&autoplay=0" ' +
                'webkitallowfullscreen mozallowfullscreen allowfullscreen class="content-item embed-responsive-item"></iframe>';
            return $sce.trustAsHtml(embed);
        }

        var youtubeEmbed = function(url) {
            var videoId = embedRegexpPatterns.youtube.exec(url)[1];
            var embed =
                '<iframe src="https://www.youtube.com/embed/' + videoId + '?autoplay=0" ' +
                'frameBorder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen '+
                'class="content-item embed-responsive-item"></iframe>';
            return $sce.trustAsHtml(embed);
        }

        var twitterPromise = function(url) {
            var twitterUrl =
                'https://api.twitter.com/1/statuses/oembed.json?omit_script=true&&url=' + url + '&'+
                'maxwidth=600&hide_media=false&hide_thread=false&align=none&lang=en';

            var deferred = $q.defer();

            $http.jsonp(twitterUrl + '&callback=JSON_CALLBACK').success(function (data, status, headers, config) {
                deferred.resolve(data);
            }).error(function (data, status, headers, config) {
                deferred.reject(status);
            });

            return deferred.promise;
        }

        return {
            generateEmbeddableContent: function(url, downloadName) {
                if (url.match(embedRegexpPatterns.basicVideo)) {
                    return {
                        type: 'video',
                        url: url,
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.basicAudio)) {
                    return {
                        type: 'audio',
                        url: url,
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.basicImage)) {
                    return {
                        type: 'image',
                        url: url,
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.pdf)) {
                    return {
                        type: 'pdf',
                        url: url,
                        embed: pdfEmbed(url),
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.soundCloud)) {
                    return {
                        type: 'soundCloud',
                        url: url,
                        embed: soundCloudEmbed(url),
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.spotify)) {
                    return {
                        type: 'spotify',
                        url: url,
                        embed: spotifyEmbed(url),
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.vimeo)) {
                    return {
                        type: 'vimeo',
                        url: url,
                        embed: vimeoEmbed(url),
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.youtube)) {
                    return {
                        type: 'youtube',
                        url: url,
                        embed: youtubeEmbed(url),
                        displayInline: false
                    };
                } else if (url.match(embedRegexpPatterns.twitter)) {
                    var promise = twitterPromise(url);
                    var embeddableLink = {
                        type: 'twitter',
                        url: url,
                        promise: promise,
                        embed: "",
                        displayInline: false
                    };
                    promise.then(function(ret) {
                        embeddableLink.embed = $sce.trustAsHtml(ret.html);
                    });
                    return embeddableLink;
                }
            },
            generateAttachmentContent: function(file, downloadName, displayInline) {
                var content = {
                    type: 'attachment', // default type, should be overwritten below
                    title: file.name,
                    displayInline: displayInline ? displayInline : false
                };
                if (file.kaltura_media) {
                    content.id = file.id;
                    content.service_url = file.kaltura_media.service_url;
                    content.show_recent_warning = file.kaltura_media.show_recent_warning;
                    content.kalturaAttributes = {
                        pid: file.kaltura_media.partner_id,
                        uiconfid: file.kaltura_media.player_id,
                        entryid: file.kaltura_media.entry_id,
                        flashvars: '{"streamerType": "auto"}'
                    };

                    if (file.kaltura_media.media_type == 1) {
                        content.type = 'kaltura_video';
                    } else {
                        content.type = 'kaltura_audio';
                    }
                } else {
                    var filePath = '/app/attachment/' + file.name;
                    if (downloadName) {
                        content.title = downloadName;
                        filePath += "?name="+encodeURIComponent(downloadName+'.'+file.extension);
                    }
                    content.url = filePath;

                    if (file.extension == 'pdf') {
                        content.type = 'pdf';
                        content.url = $sce.trustAsResourceUrl('/app/pdf?file='+encodeURIComponent(content.url)+'#page=1');
                    } else if (file.mimetype.match(/image/ig)) {
                        content.type = 'image';
                    } else if (file.mimetype.match(/video/ig)) {
                        content.type = 'video';
                    } else if (file.mimetype.match(/audio/ig)) {
                        content.type = 'audio';
                    }
                }
                return content;
            }
        }
    }
]);

app.directive('dynamicRichContent',
    ["$compile",
    function ($compile)
    {
        return {
            restrict: 'A',
            replace: true,
            link: function (scope, ele, attrs) {
                scope.$watch(attrs.dynamicRichContent, function(html) {
                    ele.html(html);
                    $compile(ele.contents())(scope);
                });
            }
        };
    }
]);

//
module.directive('richContent',
    ["$filter", "LearningRecordStatementHelper", "$uibModal", "embeddableRichContent", "$sanitize",
    function ($filter, LearningRecordStatementHelper, $uibModal, embeddableRichContent, $sanitize)
    {
        return {
            restrict: 'E',
            scope: {
                content: '=',
                attachment: '=?',
                downloadName: '=?',
                displayInline: '=?'
                //attachments: '=?',
            },
            templateUrl: 'modules/rich-content/rich-content-template.html',
            link: function($scope, elem, attrs) {
                $scope.attachmentContent = [];
                $scope.isString = angular.isString;
                $scope.embeddableLinks = [];

                $scope.toggleShowContent = function(content) {
                    content.displayInline = !content.displayInline;
                };

                $scope.showAttachmentContentModal = function (content) {
                    var modalScope = $scope.$new();
                    modalScope.content = content;
                    modalScope.downloadName = $scope.downloadName;
                    modalScope.modalInstance = $uibModal.open({
                        templateUrl: 'modules/rich-content/rich-content-attachment-modal-template.html',
                        scope: modalScope
                    });
                    modalScope.modalInstance.opened.then(function() {
                        LearningRecordStatementHelper.opened_attachment_modal(content.title);
                    });
                    modalScope.modalInstance.result.finally(function() {
                        LearningRecordStatementHelper.closed_attachment_modal(content.title);
                    });
                };

                $scope.showEmbeddableLinkModal = function (content) {
                    var modalScope = $scope.$new();
                    modalScope.content = content;
                    modalScope.downloadName = $scope.downloadName;
                    modalScope.modalInstance = $uibModal.open({
                        templateUrl: 'modules/rich-content/rich-content-embeddable-modal-template.html',
                        scope: modalScope
                    });
                    modalScope.modalInstance.opened.then(function() {
                        LearningRecordStatementHelper.opened_embeddable_content_modal(content.url);
                    });
                    modalScope.modalInstance.result.finally(function() {
                        LearningRecordStatementHelper.closed_embeddable_content_modal(content.url);
                    });
                };

                var processContent = function() {
                    var content = $sanitize($scope.content);

                    $scope.embeddableLinks = [];
                    var linkMatches = [];
                    var linkRegex = /<a[^>]*>[^<]+<\/a>/ig;
                    var linkMatch = null;
                    while ( (linkMatch = linkRegex.exec(content)) !== null ) {
                        // add processed link if valid
                        var link = $(linkMatch[0]);
                        var href = link.attr("href");
                        if (href) {
                            var embeddableContent = embeddableRichContent.generateEmbeddableContent(href, $scope.downloadName);
                            if (embeddableContent) {
                                $scope.embeddableLinks.push(embeddableContent);
                                linkMatches.push({
                                    contentIndex: linkRegex.lastIndex,
                                    embeddableLinkIndex: $scope.embeddableLinks.length-1
                                })
                            }
                        }
                    }

                    for (var count = linkMatches.length-1; count >= 0; --count) {
                        var contentIndex = linkMatches[count].contentIndex;
                        var embeddableLinkIndex = linkMatches[count].embeddableLinkIndex;
                        var template =
                            '&mdash;<a href="" ng-click="showEmbeddableLinkModal(embeddableLinks['+embeddableLinkIndex+'])" '+
                                'class="btn btn-info btn-xs">'+
                                'Open in Pop-up'+
                            '</a>';
                        content = content.substr(0, contentIndex) + template + content.substr(contentIndex);
                    }

                    var mediaMatches = [];
                    // image, audio, or video tags
                    var mediaRegex = /<img[^>]*>|<video[^>]*>|<audio[^>]*>/ig;
                    var mediaMatch = null;
                    while ( (mediaMatch = mediaRegex.exec(content)) !== null ) {
                        mediaMatches.push(mediaRegex.lastIndex);
                    }

                    // add crossorigin="anonymous" to image, video, and audio tags
                    for (var count = mediaMatches.length-1; count >= 0; --count) {
                        var contentIndex = mediaMatches[count];
                        var template = ' crossorigin="anonymous" ';
                        content = content.substr(0, contentIndex-1) + template + content.substr(contentIndex-1);
                    }

                    // needs to be compiled by dynamic
                    $scope.richContent = '<div mathjax hljs >'+content+'</div>';
                };

                var processAttachment = function() {
                    $scope.attachmentContent = [];
                    if ($scope.attachment) {
                        $scope.attachmentContent.push(
                            embeddableRichContent.generateAttachmentContent($scope.attachment, $scope.downloadName, $scope.displayInline)
                        );
                    }
                };

                $scope.$watchCollection('content', processContent);
                $scope.$watchCollection('attachment', processAttachment);
                processContent();
                processAttachment();
            }
        };
    }
]);

})();
