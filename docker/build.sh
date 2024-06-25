#!/bin/bash
SCRIPT_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

WINE_DOCKER_TAG=infectionmonkey/wine-docker:devel
PYWINE_TAG=infectionmonkey/pywine:3.11

cd "$SCRIPT_DIR"/wine-docker || exit
docker build --platform linux/amd64 -t $WINE_DOCKER_TAG --build-arg WINE_FLAVOUR=devel .

cd "$SCRIPT_DIR"/pywine || exit
sed "s|FROM tobix/wine:devel|FROM $WINE_DOCKER_TAG|" Dockerfile > Dockerfile.modified
docker build --platform linux/amd64 -t $PYWINE_TAG --build-arg PYTHON_VERSION=3.11.9 -f Dockerfile.modified .
rm Dockerfile.modified

cd "$SCRIPT_DIR" || exit
IMAGE_NAME=infectionmonkey/plugin-builder
LATEST_IMAGE=${IMAGE_NAME}:latest
DOCKER_BUILDKIT=1 docker build \
    --platform linux/amd64 \
    --progress plain \
    -t $IMAGE_NAME -t $LATEST_IMAGE - < Dockerfile
