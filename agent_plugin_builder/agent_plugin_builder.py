import logging
from argparse import ArgumentParser

from monkeytypes import AgentPluginManifest

from .agent_plugin_builder_arguments import ARGUMENTS, CustomArgumentsFormatter
from .build_options import parse_agent_plugin_build_options
from .build_plugin import build_agent_plugin, get_agent_plugin_manifest
from .setup_build_plugin_logging import add_file_handler, reset_logger, setup_logging

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(description="Build plugin", formatter_class=CustomArgumentsFormatter)
    for argument in ARGUMENTS:
        parser.add_argument(*argument["name"], **argument["kwargs"])

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
