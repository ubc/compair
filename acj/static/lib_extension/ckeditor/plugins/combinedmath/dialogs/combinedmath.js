CKEDITOR.dialog.add('combinedmath', function( editor ) {
    // For the onLoad handler, sets up automatic preview when user stops typing
    var automaticPreview = function(that) {
        var duration = 1000;
        var stillTyping = false;
        var hasTimeout = false;
        var timeoutHandler = function() {
            if (stillTyping) {
                stillTyping = false;
                setTimeout(timeoutHandler, duration);
            }
            else {
                hasTimeout = false;
                that.refreshPreview(
                    that.getInputElement().getValue());
            }
        };
        // only want 1 timeout in process at a time
        that.getInputElement().on( 'keyup', function() {
            if (hasTimeout) stillTyping = true;
            else {
                hasTimeout = true;
                setTimeout(timeoutHandler, duration);
            }
        });
    };
    // both asciimath and texmath needs a way to refresh the math preview render
    var refreshPreview = function(that, mathtype, mathexp) {
        var previewDiv = that.getDialog().
            getContentElement(mathtype, mathtype+'preview').getInputElement();
        previewDiv.setText('`' + mathexp + '`');
        MathJax.Hub.Queue(
            ["Typeset", MathJax.Hub, previewDiv.$]);

    };
    // the actual dialog configurate for the combined math plugin
    return {
        title: 'Edit Math Expression',
        minWidth: 200,
        minHeight: 100,
        contents: [
            {
                id: 'asciimath',
                label: 'ASCII Math Entry',
                elements: [
                    {
                        id: 'equation-asciimath',
                        type: 'textarea',
                        label: "Enter your math expression:",
                        // called when this dialog is first created
                        // need to setup the automatic preview refresh
                        onLoad: function() {
                            automaticPreview(this);
                        },
                        // helper method to refresh the preview math rendered
                        refreshPreview: function(mathexp) {
                            refreshPreview(this, 'asciimath', mathexp);
                        },
                        // loads an existing math expression into the textarea
                        // and refreshes the preview
                        setMathexp: function(mathexp) {
                            this.setValue(mathexp);
                            this.refreshPreview(mathexp);
                        },
                        // called when loading an existing math element
                        // have to load the existing data into the textarea
                        setup: function( widget ) {
                            if (widget.data.mathexp &&
                                widget.data.mode=='ascii') {
                                this.setMathexp(widget.data.mathexp);
                            }
                        },
                        // called when the user clicks "OK" on the element
                        // need to save the data user entered so that it is
                        // accessible by the rest of the plugin
                        commit: function( widget ) {
                            if (this.isVisible()) {
                                widget.setData('mode', 'ascii');
                                widget.setData( 'mathexp', this.getValue());
                            }
                        }
                    },
                    {
                        type: 'button',
                        id: 'asciimathExampleBtn',
                        label: 'Load Example',
                        onClick: function() {
                            asciimathElem = this.getDialog().getContentElement(
                                'asciimath', 'equation-asciimath');
                            asciimathElem.setMathexp('a^2+b^2=c^2');
                            asciimathElem.focus();
                        }
                    },
                    // Preview labels and div are separated for convenience.
                    // Due to the fact there may be multiple CKEditor
                    // instances, we can't rely on static IDs to retrieve the
                    // preview window div to change values on it. So we have to
                    // use CKEditor's built in mechanism for giving each
                    // elements unique IDs. Since this only works on the first
                    // element given in html, we had to separate the label and
                    // div.
                    {
                        id: 'asciimathpreviewLabel',
                        type: 'html',
                        html: "<label>Preview:</label>"
                    },
                    {
                        id: 'asciimathpreview',
                        type: 'html',
                        html: "<div style='text-align:center'></div>"
                    },
                    {
                        id: 'asciimathinstructions',
                        type: 'html',
                        html: "<label>ASCII Math Help:</label>" +
                        "<p>AsciiMath is an easy-to-write markup language for mathematics.</p>" +
                        "<p>The best way to learn is by looking at <a href='http://math.chapman.edu/~jipsen/mathml/asciimathjax.html' target='_blank' style='color: blue'>some examples</a>.</p>" +
                        "<p>There is a short description of the <a href='http://asciimath.org/#syntax' target='_blank' style='color: blue'>syntax and list of symbols</a>. </p>"
                    }
                ]
            },
            {
                id: 'texmath',
                label: 'LaTeX Math Entry',
                elements: [
                    {
                        id: 'equation-texmath',
                        type: 'textarea',
                        label: "Enter your math expression:",
                        // called when this dialog is first created
                        // need to setup the automatic preview refresh
                        onLoad: function() {
                            automaticPreview(this);
                        },
                        // helper method to refresh the preview math rendered
                        refreshPreview: function(mathexp) {
                            refreshPreview(this, 'texmath', mathexp);
                        },
                        setMathexp: function(mathexp) {
                            this.setValue(mathexp);
                            this.refreshPreview(mathexp);
                        },
                        // called when loading an existing math element
                        // have to load the existing data into the textarea
                        setup: function( widget ) {
                            if (widget.data.mathexp && widget.data.mode=='tex') {
                                this.setMathexp(widget.data.mathexp);
                                this.selectParentTab();
                                this.focus()
                            }
                        },
                        // called when the user clicks "OK" on the element
                        // need to save the data user entered so that it is
                        // accessible by the rest of the plugin
                        commit: function( widget ) {
                            if (this.isVisible()) {
                                widget.setData('mode', 'tex');
                                widget.setData( 'mathexp', this.getValue());
                            }
                        }
                    },
                    {
                        type: 'button',
                        id: 'texmathExampleBtn',
                        label: 'Load Example',
                        onClick: function() {
                            texmathElem = this.getDialog().getContentElement(
                                'texmath', 'equation-texmath');
                            texmathElem.setMathexp(
                                '\\frac{d}{dx} \\int_{a}^{x}f(s) ds = f(x)');
                            texmathElem.focus();
                        }
                    },
                    {
                        id: 'texmathpreviewLabel',
                        type: 'html',
                        html: "<label>Preview:</label>"
                    },
                    {
                        id: 'texmathpreview',
                        type: 'html',
                        html: "<div style='text-align:center'></div>"
                    },
                    {
                        id: 'texmathinstructions',
                        type: 'html',
                        html:
                        "<label>TeX Math Help:</label>" +
                        "<p>For advanced users, math expressions can be entered using LaTeX.</p>" +
                        "<p>For an introduction to LaTeX math entry, <a style='color: blue' href='http://en.wikibooks.org/wiki/LaTeX/Mathematics' target='_blank'>click here</a>.</p>"
                    }
                ]
            }
        ]
    };
} );
