import logging
import shutil
import tarfile
from pathlib import Path

from monkeytypes import AgentPluginManifest

from .agent_plugin_build_options import AgentPluginBuildOptions, SourceDirName
from .plugin_manifest import get_plugin_manifest_file_path
from .plugin_schema_generation import CONFIG_SCHEMA, generate_plugin_config_schema
from .vendor_dir_generation import generate_vendor_directories

logger = logging.getLogger(__name__)

EXCLUDE_SOURCE_FILES = [
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".git",
    ".gitignore",
    ".DS_Store",
]
SOURCE = "source"


def create_agent_plugin_archive(
    agent_plugin_build_options: AgentPluginBuildOptions,
    agent_plugin_manifest: AgentPluginManifest,
):
    """
    Create the Agent Plugin tar archive.

    :param agent_plugin_build_options: Agent Plugin build options.
    :param agent_plugin_manifest: Agent Plugin manifest.
    """

    generate_vendor_directories(
        agent_plugin_build_options,
        agent_plugin_manifest,
    )
    generate_plugin_config_schema(
        agent_plugin_build_options.build_dir_path,
        agent_plugin_build_options.source_dir_name,
        agent_plugin_manifest,
    )
    create_source_archive(
        agent_plugin_build_options.build_dir_path, agent_plugin_build_options.source_dir_name
    )
    plugin_archive_path = create_plugin_archive(
        agent_plugin_build_options.build_dir_path, agent_plugin_manifest
    )
    _copy_plugin_archive_to_dist(plugin_archive_path, agent_plugin_build_options.dist_dir_path)


def _copy_plugin_archive_to_dist(plugin_filepath: Path, dist_dir_path: Path):
    if not dist_dir_path.exists():
        logger.info(f"Creating dist directory: {dist_dir_path}")
        dist_dir_path.mkdir(exist_ok=True)

    destination_filepath = dist_dir_path / plugin_filepath.name
    logger.info(f"Copying plugin archive: {plugin_filepath} -> {destination_filepath}")
    shutil.copy2(plugin_filepath, destination_filepath)


def create_source_archive(build_dir_path: Path, source_dir_name: SourceDirName) -> Path:
    """
    Create the source archive for the plugin.

    :param build_dir_path: Path to the build directory.
    :param source_dir_name: Name of the plugin source directory.
    :return: Path to the source archive.
    """
    source_archive = build_dir_path / f"{SOURCE}.tar.gz"
    source_build_dir_path = build_dir_path / source_dir_name

    logger.info(f"Creating source archive: {source_archive} ")
    with tarfile.open(str(source_archive), "w:gz") as tar:
        for item in source_build_dir_path.iterdir():
            tar.add(item, arcname=item.name, filter=_source_archive_filter)

    return source_archive


def _source_archive_filter(file_info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    if any(exclude in file_info.name for exclude in EXCLUDE_SOURCE_FILES):
        return None
    return file_info


def create_plugin_archive(
    build_dir_path: Path,
    agent_plugin_manifest: AgentPluginManifest,
) -> Path:
    """
    Create the Agent Plugin archive.

    :param build_dir_path: Path to the build directory.
    :param agent_plugin_manifest: Agent Plugin manifest.
    :return: Path to the plugin archive.
    """

    plugin_archive = build_dir_path / _get_plugin_archive_name(agent_plugin_manifest)
    if plugin_archive.exists():
        logger.info(f"Removing existing plugin archive: {plugin_archive}")
        plugin_archive.unlink()

    source_archive = build_dir_path / f"{SOURCE}.tar.gz"
    config_schema_file = build_dir_path / CONFIG_SCHEMA
    agent_plugin_manifest_file = get_plugin_manifest_file_path(build_dir_path)

    logger.info(f"Creating plugin archive: {plugin_archive}")
    with tarfile.open(str(plugin_archive), "w") as tar:
        tar.add(source_archive, arcname=source_archive.name)
        tar.add(config_schema_file, arcname=config_schema_file.name)
        tar.add(agent_plugin_manifest_file, arcname=agent_plugin_manifest_file.name)

    logger.info(f"Plugin archive created: {plugin_archive}")
    return plugin_archive


def _get_plugin_archive_name(agent_plugin_manifest: AgentPluginManifest) -> str:
    return f"{agent_plugin_manifest.name}-{agent_plugin_manifest.plugin_type.value.lower()}.tar"
