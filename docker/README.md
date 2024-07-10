## Building the docker image

To build the docker image, you will first need to pull the submodules for the
base images:

```
git submodule init
git submodule update
```

Then, you simply execute the build script:

```
bash build.sh
```

## Upload the docker image

```
# Only necessary if you haven't logged in before
docker login -u <username>

docker push infectionmonkey/plugin-builder
```
