/* check for matching passwords; can be modified to be more general to check for the matching of any fields*/
myApp.directive('pwMatch', function(){
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

myApp.directive('backButton', function(){
    return {
      restrict: 'A',

      link: function(scope, element, attrs) {
        element.bind('click', goBack);

        function goBack() {
          history.back();
          scope.$apply();
        }
      }
    };
});

myApp.directive('halloEditor', function() {
    return {
        restrict: 'A',
        require: '?ngModel',
        link: function(scope, element, attrs, ngModel) {
            if (!ngModel) {
                return;
            }
 
            element.hallo({
               plugins: {
                 'halloformat': {'formattings': {"bold": true, "italic": true, "strikethrough": true, "underline": true}},
                 'halloheadings': [1,2,3],
                 'hallojustify' : {},
                 'hallolists': {},
               }
            });
 
            ngModel.$render = function($scope) {
                element.html(ngModel.$viewValue || '');
            };
 
            element.on('hallomodified', function() {
                ngModel.$setViewValue(element.html());
                scope.$apply();
            });
        }
    };
});

myApp.directive("uploadImage", function() {
	return {
		restrict: "A",
		replace: true,
		scope: {
			image: "@image",
			editor: "@editor"
		},
		// create a file upload field and submit button
		template: '<form ng-upload action="/uploadimage" class="margin0" enctype="multipart/form-data" name="uploadImg" novalidate>' +
			'<div><label for="stepBrowse" class="marginR5">Image</label><input type=file name=file id="stepBrowse" class="inlineBlock">' + 
			'<span class="btn btn-primary" upload-submit="addImage(content)">Insert image</span></div></form>',
		controller: function($rootScope, $scope, $element, $attrs, flashService) {
			$scope.addImage = function(content) {
				// insert the image at the cursor position
				// (don't allow image upload if the text is already at the given limit)
				if (content.completed && content.file && content.file.length > 0) {
					img = document.createElement("IMG");
					img.src = "user_images/" + content.file;
					divElmnt = document.getElementById($scope.editor);
					if ($rootScope.savedRange && $rootScope.savedRange.compareNode(divElmnt) == 2) {
						$rootScope.savedRange.insertNode(img);
						rangy.getSelection().setSingleRange($rootScope.savedRange);
					}
					else {
						var textarea = angular.element("div#"+$scope.editor);
						textarea.append(img);
					}
				} else if(content.completed) {
					if(content.msg && content.msg.length > 0) {
						flashService.flash('danger', content.msg);
					}
					else {
						flashService.flash('danger', 'An error occured while uploading the image.');
					}
				}
			};
		}
	};
});

myApp.directive("mathFormula", function() {
	return {
		restrict: "A",
		replace: true,
		scope: {
			equation: "@mathEquation",
			editor: "@editor",
			label: "@label"
		},
		template: '<span ng-click="add()" class="btn btn-default" mathjax-bind="label"></span>',
		controller: function($rootScope, $scope, $element, $attrs) {
			$scope.add = function() {
				divElmnt = document.getElementById($scope.editor);
				// insert the formular at the cursor position using Rangy's insert method
				if ($rootScope.savedRange && $rootScope.savedRange.compareNode(divElmnt) == 2) {
					$rootScope.savedRange.insertNode(document.createTextNode($scope.equation));
					rangy.getSelection().setSingleRange($rootScope.savedRange);
				}
				else {
					var textarea = angular.element("div#"+$scope.editor);
					textarea.append($scope.equation);
				}
			};
		}
	};
});

myApp.directive("mathImage", function() {
	return {
		restrict: "A",
		replace: true,
		scope: {
			equation: "@mathEquation",
			editor: "@editor",
			label: "@label",
			imgSrc: "@imgSrc",
			height: "@height"				
		},
		template: '<span ng-click="add()" class="btn btn-default"><img ng-src="img/{{imgSrc}}" style="height:{{height || 18}}px;" /></span>',
		controller: function($rootScope, $scope, $element, $attrs) {
			$scope.add = function() {
				divElmnt = document.getElementById($scope.editor);
				// insert the formular at the cursor position using Rangy's insert method
				if ($rootScope.savedRange && $rootScope.savedRange.compareNode(divElmnt) == 2) {
					$rootScope.savedRange.insertNode(document.createTextNode($scope.equation));
					rgy = rangy.getSelection().setSingleRange($rootScope.savedRange);
				}
				else {
					var textarea = angular.element("div#"+$scope.editor);
					textarea.append($scope.equation);
				}
			};
		}
	};
});

myApp.directive("mathToolbar", function() {
	return {
		restrict: "A",
		replace: false,
		scope: {
			editor: "@editor",
		},
		controller: function($scope, $element, $attrs) {
			$scope.toolbarOption = 'undefined';
		},
		templateUrl: 'mathjax/toolbar.html',
	};
});

myApp.directive("notification", function() {
	return {		
		restrict: "A",
		replace: true,
		scope: true,
		template: '<ul class="dropdown-menu"><li>{{notificationsCount}} new answer(s):</li>' + 
		'<li ng-repeat="item in notificationdropdown"><a href="{{item.href}}">{{item.text}}</a>' +
		'</li></ul>'	
	};
});

myApp.directive("commentBlock", function() {
	return {
		restrict: "A",
		scope: {
			type: "@ctype",
			login: "@clogin",
			instructor: "@cinstructor",
			sid: "@csid",
			sidl: "@sidl",
			sidr: "@sidr",
			qid: "@qid",
			contentLength: "@contentlength",
			comCount: "=comcount",
		},
		controller: function($rootScope, $scope, $element, $attrs, $routeParams, flashService, commentQService, commentAService, commentJService) {
			var questionId = $routeParams.questionId;
			
			$scope.commentEditId = -1;
			$scope.switchEdits = function(id) {		
				if (id) {
					$scope.myComment = null;
					$scope.lcomm =  null;
					$rootScope.savedRange = null;
				}
				$scope.commentEditId = id ? id == $scope.commentEditId ? -1 : id : $scope.commentEditId;				
				return $scope.commentEditId;
			};
	
			$scope.getComments = function() {
				if ($scope.type == 'Question') {
					var retval = commentQService.get( {id: questionId}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
							var divs = jQuery('[contenteditable="true"][name]').filter(function() {
								return $(this).attr("name").toString().toLowerCase().indexOf("com") > -1;
							});
							for ( var i = 0; divs[i]; i++) {
								jQuery(divs[i]).unbind('paste');
								jQuery(divs[i]).bind('paste', function(e) {
									$scope.saveRange(e, $scope.contentLength);
								});
							}
						} else {
							flashService.flash('danger', 'The comments could not be found.');
						}
					});
				} else if ($scope.type == 'Answer') {
					var retval = commentAService.get( {id: $scope.sid}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
							var divs = jQuery('[contenteditable="true"][name]').filter(function() {
								return $(this).attr("name").toString().toLowerCase().indexOf("com") > -1;
							});
							for ( var i = 0; divs[i]; i++) {
								jQuery(divs[i]).unbind('paste');
								jQuery(divs[i]).bind('paste', function(e) {
									$scope.saveRange(e, $scope.contentLength);
								});
							}
						} else {
							flashService.flash('danger', 'The comments could not be found.');
						}
					});
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					var retval = commentJService.get( {id: $scope.type == 'Judgement' ? questionId : $scope.qid, sidl: $scope.sidl, sidr: $scope.sidr}, function() {
						if (retval.comments) {
							$scope.anyComments = retval.comments;
							var divs = jQuery('[contenteditable="true"][name*="com"]');
							for ( var i = 0; divs[i]; i++) {
								jQuery(divs[i]).unbind('paste');
								jQuery(divs[i]).bind('paste', function(e) {
									$scope.saveRange(e, $scope.contentLength);
								});
							}
						} else {
							flashService.flash('danger', 'The comments could not be found.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
				}
			};
			$scope.getComments();
			
			$scope.makeComment = function() {
				var myComment = angular.element("#mycomment"+$scope.type + ($scope.type == "Answer" ? $scope.sid : "")).html();
				var newstring = angular.element("#mycomment"+$scope.type + ($scope.type == "Answer" ? $scope.sid : "")).text();
				var input = {"content": myComment};
				if (!newstring) {
					return '';
				}
				if ($scope.contentLength > 0) {
					elmt = angular.element("#mycomment"+$scope.type + ($scope.type == "Answer" ? $scope.sid : ""));
					fullRange = rangy.createRange();
					fullRange.setStartBefore(elmt[0]);
					fullRange.setEndAfter(elmt[0]);
					if (fullRange.toString().length > $scope.contentLength) {
						flashService.flash('danger', 'The comment is too long.');
						return '';
					}
				}
				if ($scope.type == 'Question') {
					var retval = commentQService.save( {id: questionId}, input, function() {
						if (retval.comment) {
							$scope.anyComments.push( retval.comment );
							$scope.myComment = '';
							$scope.lcomm = false;
							$scope.comCount++;
							flashService.flash('success', 'The comment has been successfully added');
						} else {
							flashService.flash('danger', 'Please submit a valid comment.');
						}
					});
				} else if ($scope.type == 'Answer') {
					var retval = commentAService.save( {id: $scope.sid}, input, function() {
						if (retval.comment) {
							$scope.anyComments.push( retval.comment );
							$scope.myComment = '';
							$scope.lcomm = false;
							$scope.comCount++;
							flashService.flash('success', 'The comment has been successfully added.');
						} else {
							flashService.flash('danger', 'Please submit a valid comment.');
						}
					});
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					var retval = commentJService.save( {id: $scope.type == 'Judgement' ? questionId : $scope.qid, sidl: $scope.sidl, sidr: $scope.sidr}, input, function() {
						if (retval.comment) {
							$scope.anyComments.push( retval.comment );
							$scope.myComment = '';
							$scope.lcomm = false;
							$scope.comCount++;
							flashService.flash('success', 'The comment has been successfully added.');
						} else {
							flashService.flash('danger', 'Please submit a valid comment.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
				}
				$scope.switchEdits(-1);
			};

			$scope.delComment = function( comment ) {
				if ($scope.type == 'Question') {
					if (confirm("Delete Question Comment?") == true) {
						var retval = commentQService.remove( {id: comment.id}, function() {
							if (retval.msg != 'PASS') {
								flashService.flash('danger', 'The comment was unsuccessfully deleted.');
							} else {
								var index = jQuery.inArray(comment, $scope.anyComments);
								$scope.anyComments.splice(index, 1);
								$scope.comCount--;
							}
						});
					}
				} else if ($scope.type == 'Answer') {
					if (confirm("Delete Answer Comment?") == true) {
						var retval = commentAService.remove( {id: comment.id}, function() {
							if (retval.msg != 'PASS') {
								flashService.flash('danger', 'The comment was unsuccessfully deleted.');
							} else {
								var index = jQuery.inArray(comment, $scope.anyComments);
								$scope.anyComments.splice(index, 1);
								$scope.comCount--;
							}
						});
					}
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					if (confirm("Delete Answer Comment?") == true) {
						var retval = commentJService.remove( {id: comment.id, sidl: $scope.sidl, sidr: $scope.sidr}, function() {
							if (retval.msg != 'PASS') {
								flashService.flash('danger', 'The comment was unsuccessfully deleted.');
							} else {
								var index = jQuery.inArray(comment, $scope.anyComments);
								$scope.anyComments.splice(index, 1);
								$scope.comCount--;
							}
						});
					}
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
				}
			};

			$scope.editComment = function( comment ) {
				var newcontent = angular.element("#editcom"+comment.id).html();
				var newstring = angular.element("#editcom"+comment.id).text();
				if (!newstring) {
					return '';
				}
				if ($scope.contentLength > 0) {
					elmt = angular.element("#editcom"+comment.id);
					fullRange = rangy.createRange();
					fullRange.setStartBefore(elmt[0]);
					fullRange.setEndAfter(elmt[0]);
					if (fullRange.toString().length > $scope.contentLength) {
						flashService.flash('danger', 'The comment is too long.');
						return '';
					}
				}
				var input = {"content": newcontent};
				if ($scope.type == 'Question') {
					var retval = commentQService.put( {id: comment.id}, input, function() {
						if (retval.msg != 'PASS') {
							// can't seem to use regular span error messages
							// causes the edit toggle not to close if the edit is successful
							flashService.flash('danger', 'Please submit a comment.');
						} else {
							var index = jQuery.inArray(comment, $scope.anyComments);
							$scope.anyComments[index].content = newcontent;
							flashService.flash('success', 'The comment has been successfully modified');
						}
					});
				} else if ($scope.type == 'Answer') {
					var retval = commentAService.put( {id: comment.id}, input, function() {
						if (retval.msg != 'PASS') {
							//alert('something is wrong');
							flashService.flash('danger', 'Please submit a valid comment');
						} else {
							var index = jQuery.inArray(comment, $scope.anyComments);
							$scope.anyComments[index].content = newcontent;
							flashService.flash('success', 'The comment has been successfully added.');
						}
					});
				} else if ($scope.type == 'Judgement' || $scope.type == 'ReviewJudgement') {
					var retval = commentJService.put( {id: comment.id, sidl: $scope.sidl, sidr: $scope.sidr}, input, function() {
						if (retval.msg != 'PASS') {
							//alert('something is wrong');
							flashService.flash('danger', 'Please submit a valid comment');
						} else {
							var index = jQuery.inArray(comment, $scope.anyComments);
							$scope.anyComments[index].content = newcontent;
							flashService.flash('success', 'The comment has been successfully added.');
						}
					});
				} else {
					alert('something is wrong; comment type should be either Question, Answer or Judgement');
				}
				$scope.switchEdits(-1);
			};
			
			// save the Rangy object for the selected hallo editor
			$scope.saveRange = function($event, max) {
				var selRange = rangy.getSelection();
				$rootScope.savedRange = selRange.rangeCount ? selRange.getRangeAt(0) : null;
				if (max && max > 0) {
					elmt = selRange.getRangeAt(0).startContainer;
					while (elmt.contentEditable != 'true') {
						elmt = elmt.parentNode;
					}
					fullRange = rangy.getSelection().getRangeAt(0);
					fullRange.setStartBefore(elmt);
					fullRange.setEndAfter(elmt);
					//[backspace,shift,ctrl,alt,end,home,left,up,down,right,delete]
					allowedKeys = [8, 16, 17, 18, 35, 36, 37, 38, 39, 40, 46];
					if($event && allowedKeys.indexOf($event.which) == -1 && fullRange.toString().length >= max) {
						$event.preventDefault();
						jQuery("#" + elmt.id).effect("highlight", {"color":"#dFb5b4"}, 50);
						jQuery("#" + elmt.id + "Error").removeClass('ng-hide');
				    }
					else {
						jQuery("#" + elmt.id + "Error").addClass('ng-hide');
					}
				}
			};
		},
		templateUrl: 'templates/comments.html',
	};
});
