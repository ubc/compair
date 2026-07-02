var path = require('path');
var webpack = require('webpack');

module.exports = {
    mode: 'development',
    entry: './compair/static/webpack-entry.js',
    output: {
        path: path.resolve(__dirname, 'compair/static/build'),
        filename: 'webpack-bundle.js'
    },
    plugins: [
        // These libraries only assign to a global (window._, window.$, etc.)
        // when there's no CommonJS `module` present. Inside a webpack bundle
        // there always is one, so without this they'd load correctly but
        // never expose the global that the app's own code (written for
        // plain <script> tags) expects to find.
        new webpack.ProvidePlugin({
            _: 'lodash',
            $: 'jquery',
            jQuery: 'jquery',
            moment: 'moment',
            hljs: 'highlightjs'
        })
    ]
};
