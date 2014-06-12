# angular-ckeditor

[![Build Status](https://travis-ci.org/lemonde/angular-ckeditor.svg?branch=master)](https://travis-ci.org/lemonde/angular-ckeditor)
[![Dependency Status](https://david-dm.org/lemonde/angular-ckeditor.svg?theme=shields.io)](https://david-dm.org/lemonde/angular-ckeditor)
[![devDependency Status](https://david-dm.org/lemonde/angular-ckeditor/dev-status.svg?theme=shields.io)](https://david-dm.org/lemonde/angular-ckeditor#info=devDependencies)

CKEditor directive for Angular.

## Install

### Using bower

```sh
bower install angular-ckeditor
```

## Usage

HTML:

```html
<!-- Load files. -->
<script src="angular.js"></script>
<script src="angular-ckeditor.js"></script>

<div ng-controller="CkeditorCtrl">
  <div ckeditor="options" ng-model="content" ready="onReady()"></div>
</div>
```

JavaScript:

```js
angular.module('controllers.ckeditor', ['ckeditor'])
.controller('CkeditorCtrl', function ($scope) {

  // Editor options.
  $scope.options = {
    language: 'en',
    allowedContent: true,
    entities: false
  };

  // Called when the editor is completely ready.
  $scope.onReady = function () {
    // ...
  };
});
```

### "ckeditor" directive

- "ckeditor" Specify editor options. Accepts an Object.
- "ng-model" Binded scope variable.
- "ready" Called when the editor is completely ready. Accepts an Angular expression.
- Inline editing mode is enabled if element has a `contenteditable` attribute set to true.

## License

MIT
