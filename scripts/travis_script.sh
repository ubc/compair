#!/bin/bash

set -e -o pipefail

if [ "${INTEGRATION_TEST}" = "true" ]; then
    node_modules/.bin/gulp test:ci
elif [ "${DOCKER}" = "true" ]; then
    # test image in prod mode
    docker-compose -f deploy/docker/docker-compose.yml up -d; sleep 10;
    curl -sSL http://localhost > /dev/null && curl -sS http://localhost/api/healthz > /dev/null
else
    nosetests
    node_modules/karma/bin/karma start compair/static/test/config/karma.conf.js --single-run --browsers PhantomJS
fi
