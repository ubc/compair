#!/bin/bash

set -e -o pipefail

if [ "${INTEGRATION_TEST}" = "true" ]; then
	node_modules/.bin/gulp test:ci
elif [ "${DOCKER}" = "true" ]; then
    # test image in dev mode, e.g. settings from docker-compose
    curl -sSfL http://localhost:8080 | grep '<title>ComPAIR Learning Application</title>' > /dev/null && curl -sSf http://localhost:8080/api/healthz > /dev/null
    # test image in prod mode
    docker-compose stop app
    docker run -d --name compair_app_prod --network compair_default -e DATABASE_URI=mysql+pymysql://compair:compair@db:3306/compair ubcctlt/compair-app
    curl -sSfL http://localhost:8080 | grep '<title>ComPAIR Learning Application</title>' > /dev/null && curl -sSf http://localhost:8080/api/healthz > /dev/null
else
    nosetests
    node_modules/karma/bin/karma start compair/static/test/config/karma.conf.js --single-run --browsers PhantomJS
fi
