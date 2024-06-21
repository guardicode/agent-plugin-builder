#!/bin/bash
SCRIPT_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

cd "$SCRIPT_DIR"/wine-docker || exit
docker build --platform linux/amd64 -t wine-docker:devel --build-arg WINE_FLAVOUR=devel .

cd "$SCRIPT_DIR"/pywine || exit
sed 's|FROM tobix/wine:devel|FROM wine-docker:devel|' Dockerfile > Dockerfile.modified
docker build --platform linux/amd64 -t pywine:3.11 --build-arg PYTHON_VERSION=3.11.9 -f Dockerfile.modified .
rm Dockerfile.modified

cd "$SCRIPT_DIR" || exit
IMAGE_NAME=infectionmonkey/plugin-builder
LATEST_IMAGE=${IMAGE_NAME}:latest
DOCKER_BUILDKIT=1 docker build \
    --platform linux/amd64 \
    --progress plain \
    -t $IMAGE_NAME -t $LATEST_IMAGE - < Dockerfile
