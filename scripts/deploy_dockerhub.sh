#!/usr/bin/env bash

REPO=ubcctlt/compair-app


if [ -n "$TRAVIS_TAG" ]
then
    # tag image with git tag with # removed
    TAG=${TRAVIS_TAG/\#/}
elif [ "$TRAVIS_PULL_REQUEST" != "false" ]
then
    # tag PR requst built images
    TAG="pr-$TRAVIS_BUILD_NUMBER-$TRAVIS_COMMIT"
else
    # tag master or branch images
    TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
    #docker tag $REPO $REPO:travis-$TRAVIS_BUILD_NUMBER-$TRAVIS_COMMIT
fi

# clean tags
TAG=${TAG//[^a-zA-Z0-9-\._]/}

docker login -u $DOCKER_USER -p $DOCKER_PASS
docker tag $REPO $REPO:$TAG
docker push $REPO:$TAG
