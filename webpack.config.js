var path = require('path');
var webpack = require('webpack');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
    mode: 'development',
    entry: './compair/static/webpack-entry.js',
    output: {
        path: path.resolve(__dirname, 'compair/static/build'),
        filename: 'webpack-bundle.js'
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                // Extracted to a real .css file, not injected via JS
                // (style-loader): a <link> at the top of <head> loads
                // before compair.less's output, so app style overrides
                // still win the cascade. style-loader injected too late
                // and lost the serif heading font to bootstrap.css.
                use: [MiniCssExtractPlugin.loader, 'css-loader']
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: 'webpack-bundle.css'
        }),
        // These libraries only assign to a global (window._, window.$, etc.)
        // when there's no CommonJS `module` present. Inside a webpack bundle
        // there always is one, so without this they'd load correctly but
        // never expose the global that the app's own code (written for
        // plain <script> tags) expects to find.
        new webpack.ProvidePlugin({
            // $/jQuery aren't listed here: webpack-entry.js sets
            // window.jQuery/window.$ explicitly instead (see its comment
            // for why), which also makes them resolve as bare identifiers
            // via normal global scope fallthrough, same as `angular`.
            _: 'lodash',
            moment: 'moment',
            hljs: 'highlightjs',
            humanizeDuration: 'humanize-duration'
        })
    ]
};
