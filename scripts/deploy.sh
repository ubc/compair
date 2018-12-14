#!/usr/bin/env bash

if [ "$TRAVIS_EVENT_TYPE" == "pull_request" ]; then
    # deploy pull rquest build for review
    TAG="pr-$TRAVIS_BUILD_NUMBER-$TRAVIS_COMMIT"
    ENV_NAME="review/$TRAVIS_PULL_REQUEST"
elif [ "$TRAVIS_EVENT_TYPE" == "push" ]; then
    # deploy master or branch images
    TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
    ENV_NAME=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "staging"; else echo $TRAVIS_BRANCH ; fi`
else
    # no deploy for other event types
    exit 0
fi

# clean tags
TAG=${TAG//[^a-zA-Z0-9-\._]/}
ENV_NAME=${ENV_NAME//[^a-zA-Z0-9-\._ ]/}

curl -X POST \
     -F token=$DEPLOYMENT_TOKEN \
     -F ref=master \
     -F "variables[EVENT_TYPE]=$TRAVIS_EVENT_TYPE" \
     -F "variables[ENV_NAME]=$ENV_NAME" \
     -F "variables[BUILD_NUMBER]=$TRAVIS_BUILD_NUMBER" \
     -F "variables[app__image__tag]=$TAG" \
     -F "variables[worker__image__tag]=$TAG" \
     https://repo.code.ubc.ca/api/v4/projects/366/trigger/pipeline
