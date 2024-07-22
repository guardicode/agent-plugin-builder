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

    build_agent_plugin <PLUGIN_PATH>

where:

    Required:
        PLUGIN_PATH: The path where you have the Agent Plugin code.

    Optional:
        -b/--build-dir-path: The path where all needed build artifacts will be stored.
        If the directory is not empty, it will delete it using `shutil.rmtree`
        Default: <current_working_directory>/build

        -d/--dist-dir-path: The path where resulting Agent Plugin archive will be stored.
        Default: <current_working_directory>/dist

        -s/--source-dir: The name of the source directory.
        Default: <plugin_name>_<plugin_type>

        -pd/--platform-dependencies: The platform dependencies for the Agent Plugin.
        Options:
        common: All dependencies are packaged once, and shared across all platforms. This
            should only be used if all dependencies are known to be platform-independent.
        separate: Some or all dependencies are platform-dependent, and are therefore packaged
            separately for each supported platform. This is the most reliable option,
            however it results in a larger plugin file, since dependencies are
            duplicated for each platform.
        autodetect: The plugin builder will attempt to detect the best method to use.
        Default: autodetect

        -ver/--verify/--no-verify: Specify whether to verify the plugin's dependencies.
        --verify: Verify the integrity of the plugin's dependencies. (Recommended, default)
        --no-hverify: Do not verify the integrity of the plugin's dependencies. (Not recommended)
        not specified: Same as --verify.

        -v/--verbose: Multiple occurrences increases the logging level of the console logging.
        Example: -v means CRITICAL, -vvvvv means DEBUG.
        Default: if not specific, the logging level will be INFO.

### Using Poetry

Alternatively one may use Agent Plugin Builder without installing it by
cloning this repository and invoking:

    poetry install
    poetry run build_agent_plugin <PLUGIN_PATH>

## Development

### Setting up your development environment

Run the following commands to install the necessary prerequisites:

    pip install poetry pre-commit
    poetry install
    pre-commit install -t pre-commit -t prepare-commit-msg
