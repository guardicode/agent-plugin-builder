# Agent Plugin Builder

A package which with a help of `infectionmonkey/agent-builder` and `infectionmonkey/plugin-builder`
Docker images, builts an Agent Plugin archive which can be installed in Monkey Island and
used in the simulation over your netwrok.

It uses an Python Docker API client to connect to your local Docker environment and
run with the mentioned Docker Images needed docker commands.

## Usage

```
poetry install
poetry run python build_plugin.py PLUGIN_PATH
```
