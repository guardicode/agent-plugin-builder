import logging
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    BooleanOptionalAction,
    RawTextHelpFormatter,
)
from pathlib import Path

from monkeytypes import AgentPluginManifest

from .build_options import (
    BUILD,
    DIST,
    PlatformDependencyPackagingMethod,
    parse_agent_plugin_build_options,
)
from .build_plugin import build_agent_plugin, get_agent_plugin_manifest
from .setup_build_plugin_logging import add_file_handler, reset_logger, setup_logging

logger = logging.getLogger(__name__)


class CustomFormatter(ArgumentDefaultsHelpFormatter, RawTextHelpFormatter):
    def _get_help_string(self, action):
        help_str = action.help or ""
        default = action.default

        # Custom replacements based on metavar
        if action.metavar == "SOURCE_DIR":
            default_str = "<plugin_name>_<plugin_type>: Ex. ssh_exploiter"
            help_str += "(Default: <plugin_name>_<plugin_type>: Ex. ssh_exploiter)"
        elif action.metavar == "PLATFORM_DEPENDENCIES":
            default_str = action.default.value
        elif action.metavar == "HASHES":
            default_str = "Include hashes in requirements.txt file"
        else:
            if action.dest == "verbosity":
                default_str = "INFO"
            else:
                default_str = default

        if "%(default)" not in help_str and default is not None:
            if action.dest != "help":
                help_str += "(Default: %(default)s)"

        return help_str % dict(default=default_str)


def main():
    parser = ArgumentParser(description="Build plugin", formatter_class=CustomFormatter)
    parser.add_argument("plugin_path", metavar="PLUGIN_PATH", type=Path, help="Path to the plugin")
    parser.add_argument(
        "-b",
        "--build-dir-path",
        metavar="BUILD_DIR_PATH",
        type=Path,
        default=(Path.cwd() / BUILD),
        help="Optional path to the build directory.\n",
    )
    parser.add_argument(
        "-d",
        "--dist-dir-path",
        metavar="DIST_DIR_PATH",
        type=Path,
        default=(Path.cwd() / DIST),
        help="Optional path to the dist directory.\n",
    )
    parser.add_argument(
        "-s",
        "--source-dir",
        metavar="SOURCE_DIR",
        type=str,
        default=None,
        help="Optional name of the source directory.\n",
    )
    parser.add_argument(
        "-pd",
        "--platform-dependencies",
        metavar="PLATFORM_DEPENDENCIES",
        type=PlatformDependencyPackagingMethod,
        default=PlatformDependencyPackagingMethod.AUTODETECT,
        help="""Since plugin dependencies must be vendored, this setting determines how
the plugin builder should package dependencies for it's supported platforms.

Options:
    common: All dependencies are packaged once, and shared across all platforms. This
            should only be used if all dependencies are known to be platform-independent.
    separate: Some or all dependencies are platform-dependent, and are therefore packaged
            separately for each supported platform. This is the most reliable option,
            however it results in a larger plugin file, since dependencies are
            duplicated for each platform.
    autodetect: The plugin builder will attempt to detect the best method to use.
""",
    )
    parser.add_argument(
        "--verify",
        metavar="HASHES",
        action=BooleanOptionalAction,
        help="""Some plugins may have dependencies for which we can't verify the hashes.

Options:
    --verify: will include hashes to verify the integrity of the plugin dependencies
    --no-verify: will exclude hashes which will not verify the integrity of the plugin
    dependencies. This is not recommended option for security reasons.

""",
        default=True,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=-1,
        help="""Verbosity (between 1-5 occurrences with more leading to more verbose logging).

Logging levels with occurrences:
    CRITICAL=1
    ERROR=2
    WARN=3
    INFO=4
    DEBUG=5
""",
    )
    args = parser.parse_args()
    _setup_logging(args.verbosity)
    _log_arguments(args)
    agent_plugin_manifest = get_agent_plugin_manifest(args.plugin_path)
    source_dir = _get_source_dir(args.source_dir, agent_plugin_manifest)
    args.source_dir = source_dir
    agent_plugin_build_options = parse_agent_plugin_build_options(args)
    try:
        build_agent_plugin(
            agent_plugin_build_options,
            agent_plugin_manifest,
            on_build_dir_created=lambda dir: add_file_handler(dir),
        )
    except Exception as e:
        logger.error(f"Error building plugin: {e}", exc_info=True)


def _log_arguments(args):
    arg_string = ", ".join([f"{key}: {value}" for key, value in vars(args).items()])
    logger.info(f"Agent Plugin Builder started with arguments: {arg_string}")


def _setup_logging(verbosity):
    reset_logger()
    setup_logging(verbosity)


def _get_source_dir(source_dir: str | None, agent_plugin_manifest: AgentPluginManifest) -> str:
    if source_dir is not None:
        return source_dir
    return f"{agent_plugin_manifest.name}_{agent_plugin_manifest.plugin_type.value}".lower()
