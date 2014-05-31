module.exports = function(grunt) {

	// Project configuration.
	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'),
		// Grab components from bower
		bower: {
			install: {
				options: {
					// copy front-end libs to to client/ directory
					targetDir: 'acj/static/libs'
				}
			}
		},
		// Automatically update given html files to import bower dependencies
		bowerInstall: {
			target: {
				src: ['acj/static/index.html']
			}
		}
	});

	// Load the plugins
	grunt.loadNpmTasks('grunt-bower-task');
	grunt.loadNpmTasks('grunt-wiredep');

	// Set up tasks
	// default task to execute all the installations
	grunt.registerTask('default', ['bower', 'bowerInstall']);
};
