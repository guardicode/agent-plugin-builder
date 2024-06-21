# Agent Plugin Builder

A package which with a help of `infectionmonkey/agent-builder` and `infectionmonkey/plugin-builder`
Docker images, builts an Agent Plugin archive which can be installed in Monkey Island and
used in the simulation over your netwrok.

It uses an Python Docker API client to connect to your local Docker environment and
run with the mentioned Docker Images needed docker commands.

## Getting started

### Installation

Install Agent Plugin Builder with `pip install .`

### Running Agent Plugin Builder

After installation,  Agent Plugin Builder can be started by simply invoking
`build_agent_plugin <PLUGIN_PATH>`, if pip installed it somewhere in your `$PATH`.

### Using Poetry

You can also run it with `poetry run build_agent_plguin <PLUGIN_PATH>`.

## Resulting artifact

All build artifacts used to generate the plugin archive will be in `build` directory
and the Anget Plugin archive will be `dist` in the same directory when the
Agent Plugin Builder is run.

## Development

### Setting up your development environment

1. Run the following commands to install the necessary prerequisites:

    ```
    $ pip install poetry pre-commit
    $ poetry install
    $ pre-commit install -t pre-commit -t prepare-commit-msg
    ```
