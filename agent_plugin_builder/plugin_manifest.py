import logging
from pathlib import Path

import yaml
from monkeytypes import AgentPluginManifest

MANIFEST = "manifest"

logger = logging.getLogger(__name__)


def get_agent_plugin_manifest(build_dir_path: Path) -> AgentPluginManifest:
    """
    Get the Agent Plugin manifest from the build directory.

    :param build_dir_path: Path to the build directory.
    :raises FileNotFoundError: If the manifest file does not exist.
    :raises yaml.YAMLError: If the manifest file is not a valid YAML file.
    :return: The Agent Plugin manifest.
    """
    manifest_file_path = get_plugin_manifest_file_path(build_dir_path)

    logger.info(f"Reading plugin manifest file: {manifest_file_path}")
    with manifest_file_path.open("r") as f:
        return AgentPluginManifest(**yaml.safe_load(f))


def get_plugin_manifest_file_path(build_dir_path: Path) -> Path:
    agent_plugin_manifest_file = build_dir_path / f"{MANIFEST}.yaml"
    if agent_plugin_manifest_file.exists():
        return agent_plugin_manifest_file

    return build_dir_path / f"{MANIFEST}.yml"
