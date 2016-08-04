/**
 * @license Copyright (c) 2003-2015, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */

CKEDITOR.editorConfig = function( config ) {
    // Define changes to default configuration here.
    // For complete reference see:
    // http://docs.ckeditor.com/#!/api/CKEDITOR.config

    // The toolbar groups arrangement, optimized for two toolbar rows.
    config.toolbarGroups = [
        { name: 'clipboard',   groups: [ 'clipboard', 'undo' ] },
        //{ name: 'editing',     groups: [ 'find', 'selection', 'spellchecker' ] },
        { name: 'insert' },
        { name: 'links' },
        { name: 'forms' },
        //{ name: 'tools' },
        //{ name: 'document',	   groups: [ 'mode', 'document', 'doctools' ] },
        { name: 'others' },
        '/',
        { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
        { name: 'paragraph',   groups: [ 'list', 'indent', 'blocks', 'align', 'bidi' ] },
        //{ name: 'styles' },
        { name: 'colors' },
        //{ name: 'about' }
    ];

    // Remove some buttons provided by the standard plugins, which are
    // not needed in the Standard(s) toolbar.
    config.removeButtons = 'Cut,Copy,Paste,PasteText,PasteFromWord,Font,Anchor';

    // Set the most common block elements.
    config.format_tags = 'p;h1;h2;h3;pre';

    // Simplify the dialog windows.
    config.removeDialogTabs = 'image:advanced;link:advanced';

    // change Code Snippet's theme
    config.codeSnippet_theme = 'foundation';

    config.height="150px";

    // enable custom plugin that combines ASCIIMath and LaTeX math input and code highlighting
    config.extraPlugins = 'codesnippet,combinedmath';
};
