#!/bin/bash
EXIT_STATUS=0
if [ "${INTEGRATION_TEST}" = "true" ]; then
	node_modules/.bin/gulp test:ci || EXIT_STATUS=$?
else
    python -m unittest discover -s acj/tests || EXIT_STATUS=$?
    node_modules/karma/bin/karma start acj/static/test/config/karma.conf.js --single-run --browsers PhantomJS || EXIT_STATUS=$?
fi
echo $EXIT_STATUS
exit $EXIT_STATUS