import logging
from enum import Enum
from pathlib import Path
from typing import Annotated

import yaml
from monkeytypes.base_models import InfectionMonkeyBaseModel
from pydantic import Field

logger = logging.getLogger(__name__)


class PlatformDependencyPackagingMethod(Enum):
    COMMON = "common"
    SEPARATE = "separate"
    AUTODETECT = "autodetect"


class AgentPluginBuildOptions(InfectionMonkeyBaseModel):
    platform_dependencies: Annotated[
        PlatformDependencyPackagingMethod,
        Field(
            title="The method to use to package platform dependencies.",
            description="""Since plugin dependencies must be vendored, this setting determines how
            the plugin builder should package dependencies for it's supported platforms.

            Options are:
              common: All dependencies are packaged once, and shared across all platforms. This
                      should only be used if all dependencies are known to be platform-independent.
              separate: Some or all dependencies are platform-dependent, and are therefore packaged
                        separately for each supported platform. This is the most reliable option,
                        however it results in a larger plugin file, since dependencies are
                        duplicated for each platform. This is the default option.
              autodetect: The plugin builder will attempt to detect the best method to use.
            """,
            default=PlatformDependencyPackagingMethod.SEPARATE,
        ),
    ]


def parse_agent_plugin_build_options(plugin_path: Path) -> AgentPluginBuildOptions:
    """
    Parse the build options for an agent plugin from the plugin's directory.

    :param plugin_path: The path to the plugin code directory.
    """
    build_config_file_path = plugin_path / "build.yaml"
    if not build_config_file_path.exists():
        build_config_file_path = plugin_path / "build.yml"

    if not build_config_file_path.exists():
        logger.info("Build options not found, using defaults.")
        return AgentPluginBuildOptions()

    logger.info(f"Using build options from {build_config_file_path}")
    with build_config_file_path.open("r") as f:
        return AgentPluginBuildOptions(**yaml.safe_load(f))
