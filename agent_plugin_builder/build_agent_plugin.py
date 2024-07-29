import logging
import shutil
from pathlib import Path
from pprint import pformat
from typing import Callable

from monkeytypes import AgentPluginManifest

from agent_plugin_builder.plugin_archive_generation import create_agent_plugin_archive

from .agent_plugin_build_options import AgentPluginBuildOptions

logger = logging.getLogger(__name__)


def build_agent_plugin(
    agent_plugin_build_options: AgentPluginBuildOptions,
    agent_plugin_manifest: AgentPluginManifest,
    on_build_dir_created: Callable[[Path], None] | None = None,
):
    """
    Build the agent plugin by copying the plugin code to the build directory and generating the
    Agent Plugin archive.

    :param agent_plugin_build_options: Agent Plugin build options.
    :param agent_plugin_manifest: Agent Plugin manifest.
    :param on_build_dir_created: Callback function to be called after the build directory is
        created. The function will be called with the build directory path as an argument.
    :raises FileNotFoundError: If the plugin path does not exist.
    :raises shutil.Error: If there is an error preparing the build directory.
    """

    if not agent_plugin_build_options.plugin_dir_path.exists():
        logger.error(f"Plugin path {agent_plugin_build_options.plugin_dir_path} does not exist")
        raise FileNotFoundError(
            f"Plugin path {agent_plugin_build_options.plugin_dir_path} does not exist"
        )

    if agent_plugin_build_options.build_dir_path.exists():
        try:
            logger.info(f"Clearing build directory: {agent_plugin_build_options.build_dir_path}")
            shutil.rmtree(agent_plugin_build_options.build_dir_path)
        except shutil.Error as err:
            logger.error(
                f"Unable to clear build directory: {agent_plugin_build_options.build_dir_path}"
            )
            raise err

    try:
        logger.info(
            "Copying plugin code to build directory: "
            f"{agent_plugin_build_options.plugin_dir_path} -> "
            f"{agent_plugin_build_options.build_dir_path}"
        )
        shutil.copytree(
            agent_plugin_build_options.plugin_dir_path,
            agent_plugin_build_options.build_dir_path,
            dirs_exist_ok=True,
        )
    except shutil.Error as err:
        logger.error(
            "Unable to copy plugin code to build directory: "
            f"{agent_plugin_build_options.plugin_dir_path} -> "
            f"{agent_plugin_build_options.build_dir_path}"
        )
        raise err

    if on_build_dir_created:
        on_build_dir_created(agent_plugin_build_options.build_dir_path)

    logger.debug(f"Using build options: {pformat(agent_plugin_build_options.model_dump())}")
    logger.debug(type(create_agent_plugin_archive))
    create_agent_plugin_archive(agent_plugin_build_options, agent_plugin_manifest)
