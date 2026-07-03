require('../../webpack-entry.js');
require('angular-mocks');
require('../helpers/matcher.js');

var specFiles = require.context('../../modules', true, /_spec\.js$/);
specFiles.keys().forEach(specFiles);
