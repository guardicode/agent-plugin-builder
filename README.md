# Agent Plugin Builder

A package which with a help of `infectionmonkey/agent-builder` and `infectionmonkey/plugin-builder`
Docker images, builds an Agent Plugin archive which can be installed in Monkey Island and
used in the simulation over your network.

It uses an Python Docker API client to connect to your local Docker environment and
run with the mentioned Docker Images needed docker commands.

## Getting started

### Installation

Install Agent Plugin Builder with `pip install .`

### Running Agent Plugin Builder

After installation, if pip installed it somewhere in your `$PATH` Agent Plugin Builder
can be started by simply invoking:

    build_agent_plugin <PLUGIN_PATH> -b/--build-dir-path <BUILD_DIR_PATH> -d/--dist-dir-path <DIST_DIR_PATH> -v/--verbose

where:

    Required:
        PLUGIN_PATH: The path where you have the Agent Plugin code.
    Optional:
        -b/--build-dir-path: The path where all needed build artifacts will be stored.
        If the directory is not empty, it will delete it using shutil.rmtree
        Default: <current_working_directory>/build

        -d/--dist-dir-path: The path where resulting Agent Plugin archive will be stored.
        Default: <current_working_directory>/dist

        -v/--verbose: Multiple occurenences increases the logging level of the console logging.
        Example: -v means logging.CRITICAL, -vvvvv means logging. DEBUG.
        Default: if not specific, the logging level will be INFO.

### Using Poetry

Alternatively one may use Agent Plugin Builder without installing it by
cloning this repository and invoking:

    poetry install
    poetry run build_agent_plugin <PLUGIN_PATH> -b/--build-dir-path <BUILD_DIR_PATH> -d/--dist-dir-path <DIST_DIR_PATH> -v/--verbose

## Development

### Setting up your development environment

Run the following commands to install the necessary prerequisites:

    pip install poetry pre-commit
    poetry install
    pre-commit install -t pre-commit -t prepare-commit-msg
