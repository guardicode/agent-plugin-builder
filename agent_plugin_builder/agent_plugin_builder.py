import logging
from argparse import ArgumentParser
from contextlib import suppress
from pathlib import Path
from tempfile import mkdtemp

from .build_plugin import BUILD, DIST, build_agent_plugin
from .setup_build_plugin_logging import reset_logger, setup_logging, AGENT_PLUGIN_BUILDER_LOG_FILENAME

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(description="Build plugin")
    parser.add_argument("plugin_path", metavar="PLUGIN_PATH", type=Path, help="Path to the plugin)")
    parser.add_argument(
        "-b",
        "--build_dir_path",
        metavar="BUILD_DIR_PATH",
        type=Path,
        default=(Path.cwd() / BUILD),
        help="Optional path to the build directory. Default: <current_working_directory>/build.",
    )
    parser.add_argument(
        "-d",
        "--dist_dir_path",
        metavar="DIST_DIR_PATH",
        type=Path,
        default=(Path.cwd() / DIST),
        help="Optional path to the dist directory. Default: <current_working_directory>/dist.",
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
    _temp_log_dir = Path(mkdtemp())
    _setup_logging(_temp_log_dir, args.verbosity)
    _log_arguments(args)
    with suppress(Exception):
        build_agent_plugin(args.plugin_path, args.build_dir_path, args.dist_dir_path)

    logger.info(f"Copying log file to {args.build_dir_path}")
    import shutil
    shutil.copy(_temp_log_dir / AGENT_PLUGIN_BUILDER_LOG_FILENAME, args.build_dir_path)


def _log_arguments(args):
    arg_string = ", ".join([f"{key}: {value}" for key, value in vars(args).items()])
    logger.info(f"Agent Plugin Builder started with arguments: {arg_string}")


def _setup_logging(build_dir_path: Path, verbosity):
    reset_logger()
    setup_logging(build_dir_path, verbosity)
