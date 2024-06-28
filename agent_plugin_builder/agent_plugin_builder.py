import logging
from argparse import ArgumentParser
from pathlib import Path

from .build_plugin import BUILD, DIST, build_agent_plugin
from .setup_build_plugin_logging import add_file_handler, reset_logger, setup_logging

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(description="Build plugin")
    parser.add_argument("plugin_path", metavar="PLUGIN_PATH", type=Path, help="Path to the plugin)")
    parser.add_argument(
        "-b",
        "--build-dir-path",
        metavar="BUILD_DIR_PATH",
        type=Path,
        default=(Path.cwd() / BUILD),
        help="Optional path to the build directory. Default: <current_working_directory>/build.",
    )
    parser.add_argument(
        "-d",
        "--dist-dir-path",
        metavar="DIST_DIR_PATH",
        type=Path,
        default=(Path.cwd() / DIST),
        help="Optional path to the dist directory. Default: <current_working_directory>/dist.",
    )
    parser.add_argument(
        "-s",
        "--source-dir",
        metavar="SOURCE_DIR",
        type=str,
        default=None,
        help="Optional name of the source directory. Default: <plugin_name>_<plugin_type>.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=-1,
        help="Verbosity (between 1-5 occurrences with more leading to more "
        "verbose logging). CRITICAL=1, ERROR=2, WARN=3, INFO=4, "
        "DEBUG=5. Default(0 or more than 5 occurrences)  level: INFO.",
    )
    args = parser.parse_args()
    _setup_logging(args.verbosity)
    _log_arguments(args)
    try:
        build_agent_plugin(
            args.plugin_path,
            args.build_dir_path,
            args.dist_dir_path,
            source_dirname=args.source_dir,
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
