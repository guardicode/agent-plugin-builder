# Agent Plugin Builder

The Agent Plugin Builder is a tool to help with building Agent Plugins for
[Infection Monkey](https://github.com/guardicore/monkey).

Since an Agent Plugin may run on multiple platforms, it may have
platform-specific dependencies. The Agent Plugin Builder will handle building
your plugin, including vendoring all of your platform-specific dependencies, so
you don't have to worry about it.

## Background

Current tooling for python packages does not support installing packages for
another platform. This means that the only supported way of installing
platform-specific dependencies is to do so on each supported platform. This
can be a burden to someone who wants to get into developing plugins for
Infection Monkey.

The Agent Plugin Builder is meant to ease that burden. It gets around the
platform limitation by using Docker containers, and notably a docker container
running WINE, to vendor platform-specific dependencies. That way, plugins can
be built cross-platform on a single machine.

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
