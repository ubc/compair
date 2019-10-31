CKEDITOR.plugins.add( 'combinedmath', {
    requires: 'widget',
    icons: 'combinedmath',
    init: function( editor ) {
        var pluginPath = this.path;
        CKEDITOR.dialog.add( 'combinedmath', this.path + 'dialogs/combinedmath.js' );
        editor.widgets.add( 'combinedmath', {
            button: 'Create a math expression',
            template: '<span class="combinedmath"></span> ',
            allowedContent: 'span(combinedmath);',
            requiredContent: 'span(combinedmath)',
            dialog: 'combinedmath',
            parts: {
                span: 'span'
            },
            mask: true,
            // called when scanning for combinedmath instances in text
            // just need to initialize data.mathexp
            upcast: function( element, data ) {
                var isValidCombinedMath =
                    element.name == 'span' && element.hasClass( 'combinedmath' );
                if (isValidCombinedMath) {
                    var math = element.getHtml();
                    if (math.charAt(0) == '`') {
                        data.mode = 'ascii';
                        math = math.replace(/`/g, '');
                    }
                    else {
                        data.mode = 'tex';
                        math = math.replace(/\\\(/g, '');
                        math = math.replace(/\\\)/g, '');
                    }
                    // undo any escape done by ckeditor
                    var parser = new DOMParser;
                    var textContent = parser.parseFromString(math, 'text/html').body.textContent;
                    data.mathexp = textContent;
                }
                return isValidCombinedMath;
            },
            // called when we want to strip the rendered mathjax and go back
            // to just the span and its math expression, this is what CKEditor
            // submits as the actual data to be saved
            downcast: function(element) {
                // this is the span that contains the original math expression
                var span = element.getFirst();
                var expression = span.getHtml();
                element.setHtml(expression);
                return element;
            },
            // called when finally inserting the widget element into editor
            data: function() {
                if (this.data.mathexp) {
                    // clear the previous expression
                    this.element.setText('');
                    // insert appropriate math marker around the new expression
                    var expression = this.data.mathexp;
                    if (this.data.mode == 'ascii') {
                        expression = '`' + expression + '`';
                    }
                    else {
                        expression = '\\(' + expression + '\\)';
                    }
                    // create an iframe for displaying the rendered math,
                    // necessary cause ckeditor's CSS keeps interfering
                    // with what mathjax rendered.
                    var iframe = new CKEDITOR.dom.element('iframe');
                    // the iframe will be pulling a bare page that'll display
                    // just the rendered mathjax. the math expression is passed
                    // along as a GET parameter.
                    var encodedMath = encodeURIComponent(expression);
                    iframe.setAttribute('src', pluginPath +
                        'iframe/mathjax.html?mathexp=' + encodedMath);
                    // keep browsers from showing a window around the iframe
                    iframe.setAttribute('frameborder', 0);
                    iframe.setAttribute('border', 0);
                    // start out at 0 size or we'll get the browser's default
                    // iframe size
                    iframe.setStyle('height', '0');
                    iframe.setStyle('width', '0');
                    // make inline-block so it'll expand to fit the iframe
                    this.element.setStyle('display', 'inline-block');
                    // Create a span that preserves the original math
                    // expression.
                    var span = new CKEDITOR.dom.element('span');
                    span.setStyle('display', 'none');
                    span.setText(expression);
                    // Insert both the original math expression span and the
                    // iframe that shows the rendered math
                    this.element.append(span);
                    this.element.append(iframe);
                }
            },
            init: function() {
                this.setData('mode', 'ascii');
            }
        });
    }
});
