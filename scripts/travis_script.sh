#!/bin/bash

set -e -o pipefail

if [ "${INTEGRATION_TEST}" = "true" ]; then
	node_modules/.bin/gulp test:ci
elif [ "${DOCKER}" = "true" ]; then
    # test image in dev mode, e.g. settings from docker-compose
    curl -sSf http://localhost:8080 > /dev/null && curl -sSf http://localhost:8080/api/healthz > /dev/null
    # test image in prod mode
    docker-compose stop app
    docker run -d --name compair_app_prod --network acjversus_default -e DATABASE_URI=mysql+pymysql://compair:compair@db:3306/compair ubcctlt/compair-app
    curl -sSf http://localhost:8080 > /dev/null && curl -sSf http://localhost:8080/api/healthz > /dev/null
else
    python -m unittest discover -s acj/tests || EXIT_STATUS=$?
    node_modules/karma/bin/karma start acj/static/test/config/karma.conf.js --single-run --browsers PhantomJS
fi
