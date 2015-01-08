CKEDITOR.dialog.add('combinedmath', function( editor ) {
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
							var that = this;
							this.getInputElement().on( 'keyup', function() {
								that.refreshPreview(
									that.getInputElement().getValue());
							});
						},
						// helper method to refresh the preview math rendered
						refreshPreview: function(mathexp) {
							var previewDiv = document.
								getElementById("asciimathPreview");
							var element = CKEDITOR.dom.element.
								get(previewDiv);
							element.setText('`' + mathexp + '`');
							MathJax.Hub.Queue(
								["Typeset", MathJax.Hub, previewDiv]);
						},
						// called when loading an existing math element
						// have to load the existing data into the textarea
						setup: function( widget ) {
							if (widget.data.mathexp && 
								widget.data.mode=='ascii') {
								this.setValue(widget.data.mathexp);
								this.refreshPreview(widget.data.mathexp);
							} else {
								this.getInputElement().setValue('a^2+b^2=c^2');
								this.refreshPreview(
									this.getInputElement().getValue());
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
						id: 'asciimathpreview',
						type: 'html',
						html: "<label>Preview:</label><div style='text-align:center' id='asciimathPreview'></div>"
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
							var that = this;
							this.getInputElement().on( 'keyup', function() {
								that.refreshPreview(
									that.getInputElement().getValue());
							});
						},
						// helper method to refresh the preview math rendered
						refreshPreview: function(mathexp) {
							var previewDiv = document.
								getElementById("texmathPreviewWindow");
							var element = CKEDITOR.dom.element.
								get(previewDiv);
							element.setText('\\(' + mathexp + '\\)');
							MathJax.Hub.Queue(
								["Typeset", MathJax.Hub, previewDiv]);
						},
						// called when loading an existing math element
						// have to load the existing data into the textarea
						setup: function( widget ) {
							if (widget.data.mathexp && widget.data.mode=='tex') {
								this.setValue(widget.data.mathexp);
								this.refreshPreview(widget.data.mathexp);
								this.selectParentTab();
							} else {
								this.getInputElement().setValue('\\frac{d}{dx} \\int_{a}^{x}f(s) ds = f(x)');
								this.refreshPreview(
									this.getInputElement().getValue());
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
						id: 'texmathpreview',
						type: 'html',
						html: "<label>Preview:</label><div style='text-align:center' id='texmathPreviewWindow'></div>"
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
