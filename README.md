# Agent Plugin Builder

A package which with a help of `infectionmonkey/agent-builder` and `infectionmonkey/plugin-builder`
Docker images, builts an Agent Plugin archive which can be installed in Monkey Island and
used in the simulation over your netwrok.

It uses an Python Docker API client to connect to your local Docker environment and
run with the mentioned Docker Images needed docker commands.

## Usage

### CLI
```
poetry install
poetry run python build_plugin.py PLUGIN_PATH
```

### Package
```python
from agent_plugin_builder import build_plugin

build_plugin(PLUGIN_PATH)
```
