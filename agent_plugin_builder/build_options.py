import logging
from enum import Enum
from pathlib import Path
from typing import Annotated

from monkeytypes.base_models import InfectionMonkeyBaseModel
from pydantic import Field

BUILD = "build"
DIST = "dist"

logger = logging.getLogger(__name__)


class PlatformDependencyPackagingMethod(Enum):
    COMMON = "common"
    SEPARATE = "separate"
    AUTODETECT = "autodetect"


class AgentPluginBuildOptions(InfectionMonkeyBaseModel):
    plugin_dir_path: Annotated[
        Path,
        Field(
            title="The path to the plugin code directory.",
        ),
    ]
    build_dir_path: Annotated[
        Path,
        Field(
            title="The path to the build directory.",
            default_factory=lambda: Path.cwd() / BUILD,
        ),
    ]
    dist_dir_path: Annotated[
        Path,
        Field(
            title="The path to the dist directory.",
            default_factory=lambda: Path.cwd() / DIST,
        ),
    ]
    source_dir: Annotated[
        str,
        Field(
            title="The name of the source directory.",
        ),
    ]
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
                        duplicated for each platform.
              autodetect: The plugin builder will attempt to detect the best method to use.
                        Default option
            """,
            default=PlatformDependencyPackagingMethod.AUTODETECT,
        ),
    ]
    verify_hashes: Annotated[
        bool,
        Field(
            title="Whether to verify plugin's dependencies.",
            default=False,
        ),
    ]


def parse_agent_plugin_build_options(args) -> AgentPluginBuildOptions:
    """
    Validate the arguments passed to the agent plugin builder

    :param args: The arguments passed to the agent plugin builder.
    :return: AgentPluginBuildOptions.
    """
    arguments_dict = vars(args)

    arguments_dict["verify_hashes"] = arguments_dict["verify"]
    del arguments_dict["verify"]
    del arguments_dict["verbosity"]

    return AgentPluginBuildOptions(**arguments_dict)
