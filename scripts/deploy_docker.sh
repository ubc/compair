#!/usr/bin/env bash

REPO=ubcctlt/compair-app

if [ -n "$TRAVIS_TAG" ]
then
    # tag image with git tag
    docker tag $REPO $REPO:$TRAVIS_TAG
elif [ "$TRAVIS_PULL_REQUEST" == "true" ]
then
    # tag PR requst built images
    docker tag $REPO $REPO:pr-$TRAVIS_BUILD_NUMBER-$TRAVIS_COMMIT
else
    # tag master or branch images
    TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
    docker tag $REPO $REPO:$TAG
    docker tag $REPO $REPO:travis-$TRAVIS_BUILD_NUMBER-$TRAVIS_COMMIT
fi

docker login -u $DOCKER_USER -p $DOCKER_PASS
docker push $REPO