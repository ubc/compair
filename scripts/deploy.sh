#!/usr/bin/env bash

if [ -n "$TRAVIS_TAG" ]
then
    # tag image with git tag with # removed
    TAG=${TRAVIS_TAG/\#/}
elif [ "$TRAVIS_PULL_REQUEST" != "false" ]
then
    # deploy pull rquest build for review
    TAG="pr-$TRAVIS_BUILD_NUMBER-$TRAVIS_COMMIT"
else
    # deploy master or branch images
    TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
fi

curl -X POST \
     -F token=$DEPLOYMENT_TOKEN \
     -F ref=master \
     -F "variables[EVENT_TYPE]=$TRAVIS_EVENT_TYPE" \
     -F "variables[PULL_REQUEST]=$TRAVIS_PULL_REQUEST" \
     -F "variables[app__image__tag]=$TAG" \
     -F "variables[worker__image__tag]=$TAG" \
     https://repo.code.ubc.ca/api/v3/projects/366/trigger/builds
