module.exports = function (config) {
	var wiredep = require('wiredep');
	var bowerFiles = wiredep({devDependencies: true, cwd: __dirname + '/../../../..'})['js'];
	config.set({
		basePath: '../../',

		files: bowerFiles.concat([
			'modules/**/*.js',
			'acj-config.js'
		]),

		frameworks: ['jasmine'],

		autoWatch: true,

		browsers: ['Chrome'],

		junitReporter: {
			outputFile: 'test_out/unit.xml',
			suite: 'unit'
		}
	});
};