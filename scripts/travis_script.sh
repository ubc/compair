#!/bin/bash
if [ "${INTEGRATION_TEST}" = "true" ]; then
	node_modules/.bin/gulp test:ci
else
    python -m unittest discover -s acj/tests/
    node_modules/karma/bin/karma start acj/static/test/config/karma.conf.js --single-run --browsers PhantomJS
fi