import json
import logging
import tarfile
from argparse import ArgumentParser
from importlib import import_module
from pathlib import Path

import yaml
from monkeytypes import AgentPluginManifest

from .build_options import PlatformDependencyPackagingMethod, parse_agent_plugin_build_options
from .setup_build_plugin_logging import reset_logger, setup_logging
from .vendor_dirs import (
    check_if_common_vendor_dir_possible,
    generate_common_vendor_dir,
    generate_requirements_file,
    generate_vendor_dirs,
)

logger = logging.getLogger(__name__)


BUILD = "build"
DIST = "dist"
CONFIG_SCHEMA = "config-schema.json"
SOURCE = "source"
MANIFEST = "manifest"


def main():
    parser = ArgumentParser(description="Build plugin")
    parser.add_argument("plugin_path", metavar="PLUGIN_PATH", type=Path, help="Path to the plugin)")
    parser.add_argument(
        "-b",
        "--build_dir_path",
        metavar="BUILD_DIR_PATH",
        type=Path,
        default=(Path.cwd() / BUILD),
        help="Optional Path to the build directory. Default: <current_working_directory>/build.",
    )
    parser.add_argument(
        "-d",
        "--dist_dir_path",
        metavar="DIST_DIR_PATH",
        type=Path,
        default=(Path.cwd() / BUILD),
        help="Optional Path to the dist directory. Default: <current_working_directory>/dist.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=-1,
        help="Verbosity (between 1-5 occurrences with more leading to more "
        "verbose logging). CRITICAL=1, ERROR=2, WARN=3, INFO=4, "
        "DEBUG=5. Default(0 or more than 5 occurences)  level: INFO.",
    )
    args = parser.parse_args()
    _setup_logging(args.build_dir_path, args.verbosity)
    build_agent_plugin(args.plugin_path, args.build_dir_path, args.dist_dir_path)


def _setup_logging(build_dir_path: Path, verbosity):
    reset_logger()

    if not build_dir_path.exists():
        logger.info(f"Creating build directory: {build_dir_path}")
        build_dir_path.mkdir(exist_ok=True)

    setup_logging(build_dir_path, verbosity)


def build_agent_plugin(
    plugin_path: Path,
    build_dir_path: Path = (Path.cwd() / BUILD),
    dist_dir_path: Path = (Path.cwd() / DIST),
):
    if not plugin_path.exists():
        logger.error(f"Plugin path {plugin_path} does not exist")
        raise FileNotFoundError(f"Plugin path {plugin_path} does not exist")

    if not build_dir_path.exists():
        logger.info(f"Creating build directory: {build_dir_path}")
        build_dir_path.mkdir(exist_ok=True)

    import shutil

    logger.info(f"Copying plugin code to build directory: {plugin_path} -> {build_dir_path}")
    shutil.copytree(plugin_path, build_dir_path, dirs_exist_ok=True)

    agent_plugin_manifest = get_agent_plugin_manifest(build_dir_path)
    create_agent_plugin_archive(build_dir_path, agent_plugin_manifest, dist_dir_path)


def get_agent_plugin_manifest(build_dir_path: Path) -> AgentPluginManifest:
    manifest_file_path = _get_plugin_manifest_filename(build_dir_path)

    logger.info(f"Reading plugin manifest file: {manifest_file_path}")
    with manifest_file_path.open("r") as f:
        return AgentPluginManifest(**yaml.safe_load(f))


def create_agent_plugin_archive(
    build_dir_path: Path,
    agent_plugin_manifest: AgentPluginManifest,
    dist_dir_path: Path = (Path.cwd() / DIST),
):
    build_options = parse_agent_plugin_build_options(build_dir_path)
    dependency_method = build_options.platform_dependencies
    generate_vendor_directories(build_dir_path, agent_plugin_manifest, dependency_method)
    generate_plugin_config_schema(build_dir_path, agent_plugin_manifest)
    create_source_archive(build_dir_path)
    create_plugin_archive(build_dir_path, agent_plugin_manifest, dist_dir_path)


def generate_vendor_directories(
    build_dir_path: Path,
    agent_plugin_manifest: AgentPluginManifest,
    dependency_method: PlatformDependencyPackagingMethod,
):
    import os

    UID = os.getuid()
    GID = os.getgid()

    logger.info(
        f"Generating vendor directories for plugin: {agent_plugin_manifest.name}, "
        f"dependency_method: {dependency_method}"
    )
    generate_requirements_file(build_dir_path)
    if dependency_method == PlatformDependencyPackagingMethod.COMMON:
        generate_common_vendor_dir(build_dir_path, UID, GID)
    elif dependency_method == PlatformDependencyPackagingMethod.SEPARATE:
        for os_type in agent_plugin_manifest.supported_operating_systems:
            generate_vendor_dirs(build_dir_path, os_type, UID, GID)
    else:
        if len(agent_plugin_manifest.supported_operating_systems) > 1:
            common_dir_possible = check_if_common_vendor_dir_possible(build_dir_path, UID, GID)
            if common_dir_possible:
                generate_common_vendor_dir(build_dir_path, UID, GID)
            else:
                for os_type in agent_plugin_manifest.supported_operating_systems:
                    generate_vendor_dirs(build_dir_path, os_type, UID, GID)


def generate_plugin_config_schema(build_dir_path: Path, agent_plugin_manifest: AgentPluginManifest):
    plugin_options_file_path = (
        build_dir_path / "src" / f"{agent_plugin_manifest.name.lower()}_options.py"
    )
    plugin_config_schema_file_path = build_dir_path / CONFIG_SCHEMA
    plugin_options_model_name = f"{agent_plugin_manifest.name}Options"

    if plugin_config_schema_file_path.exists():
        logger.info("Skipping generating config-schema. Reason: {CONFIG_SCHEMA} already exists")
        return

    config_schema = {"type": "object"}
    if plugin_options_file_path.exists():
        plugin_options_filename = plugin_options_file_path.stem
        import sys

        sys.path.append(str(build_dir_path / "src"))
        options = getattr(import_module(plugin_options_filename), plugin_options_model_name)
        config_schema = {"properties": options.model_json_schema()["properties"]}

    logger.info(f"Generating config-schema for plugin: {agent_plugin_manifest.name}")
    schema_contents = json.dumps(config_schema)
    with plugin_config_schema_file_path.open("w") as f:
        f.write(schema_contents)


def create_source_archive(build_dir_path: Path):
    source_archive = build_dir_path / f"{SOURCE}.tar.gz"
    source_build_dir_path = build_dir_path / "src"

    logger.info(f"Creating source archive: {source_archive} ")
    with tarfile.open(str(source_archive), "w:gz") as tar:
        tar.add(source_build_dir_path, arcname=SOURCE, filter=_source_archive_filter)


def _source_archive_filter(file_info: tarfile.TarInfo):
    EXCLUDE_FILES = [
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".git",
        ".gitignore",
        ".DS_Store",
    ]

    if any(exclude in file_info.name for exclude in EXCLUDE_FILES):
        return None
    return file_info


def create_plugin_archive(
    build_dir_path: Path,
    agent_plugin_manifest: AgentPluginManifest,
    dist_dir_path: Path = (Path.cwd() / DIST),
):
    if not dist_dir_path.exists():
        logger.info(f"Creating dist directory: {dist_dir_path}")
        dist_dir_path.mkdir(exist_ok=True)

    plugin_archive = (
        dist_dir_path
        / f"{agent_plugin_manifest.name}_{agent_plugin_manifest.plugin_type.value.lower()}.tar"
    )
    if plugin_archive.exists():
        logger.info(f"Removing existing plugin archive: {plugin_archive}")
        plugin_archive.unlink()

    source_archive = build_dir_path / f"{SOURCE}.tar.gz"
    config_schema_file = build_dir_path / CONFIG_SCHEMA
    agent_plugin_manifest_file = _get_plugin_manifest_filename(build_dir_path)

    logger.info(f"Creating plugin archive: {plugin_archive}")
    with tarfile.open(str(plugin_archive), "w") as tar:
        tar.add(source_archive, arcname=source_archive.name)
        tar.add(config_schema_file, arcname=config_schema_file.name)
        tar.add(agent_plugin_manifest_file, arcname=agent_plugin_manifest_file.name)

    logger.info(f"Plugin archive created: {plugin_archive}")


def _get_plugin_manifest_filename(build_dir_path: Path) -> Path:
    agent_plugin_manifest_file = build_dir_path / f"{MANIFEST}.yaml"
    if agent_plugin_manifest_file.exists():
        return agent_plugin_manifest_file

    return build_dir_path / f"{MANIFEST}.yml"
