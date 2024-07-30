import json
import logging
from importlib import import_module
from pathlib import Path

from monkeytypes import AgentPluginManifest

from .agent_plugin_build_options import SourceDirName

logger = logging.getLogger(__name__)


CONFIG_SCHEMA = "config-schema.json"


def generate_plugin_config_schema(
    build_dir_path: Path, source_dir_name: SourceDirName, agent_plugin_manifest: AgentPluginManifest
):
    """
    Generate the config-schema file for the plugin. The schema is generated
    based on the plugin's options model.

    :param build_dir_path: Path to the build directory.
    :param source_dir_name: Name of the plugin source directory.
    :param agent_plugin_manifest: Agent Plugin manifest.
    """
    plugin_options_file_path = (
        build_dir_path / source_dir_name / f"{agent_plugin_manifest.name.lower()}_options.py"
    )
    plugin_config_schema_file_path = build_dir_path / CONFIG_SCHEMA
    plugin_options_model_name = f"{agent_plugin_manifest.name}Options"

    if plugin_config_schema_file_path.exists():
        logger.info(f"Skipping generating config-schema. Reason: {CONFIG_SCHEMA} already exists")
        return

    config_schema = {"type": "object"}
    if plugin_options_file_path.exists():
        plugin_options_filename = plugin_options_file_path.stem
        import sys

        sys.path.append(str(build_dir_path / source_dir_name))
        options = getattr(import_module(plugin_options_filename), plugin_options_model_name)
        config_schema = {"properties": options.model_json_schema()["properties"]}

    logger.info(f"Generating config-schema for plugin: {agent_plugin_manifest.name}")
    schema_contents = json.dumps(config_schema)
    with plugin_config_schema_file_path.open("w") as f:
        f.write(schema_contents)
