import json
import logging
import shutil
import tarfile
from importlib import import_module
from pathlib import Path
from typing import Callable

import yaml
from monkeytypes import AgentPluginManifest

from .build_options import (
    AgentPluginBuildOptions,
    PlatformDependencyPackagingMethod,
    parse_agent_plugin_build_options,
)
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


def build_agent_plugin(
    plugin_path: Path,
    build_dir_path: Path,
    dist_dir_path: Path,
    agent_plugin_manifest: AgentPluginManifest,
    build_options_overrides: AgentPluginBuildOptions,
    on_build_dir_created: Callable[[Path], None] | None = None,
):
    """
    Build the agent plugin by copying the plugin code to the build directory and generating the
    Agent Plugin archive.

    :param plugin_path: Path to the plugin code.
        If the directory does not exist, an error will be raised
    :param build_dir_path: Path to the build directory.
        If the directory does not exist, it will be created else it will be cleared
    :param dist_dir_path: Path to the dist directory.
        If the directory does not exist, it will be created
    :param agent_plugin_manifest: Agent Plugin manifest.
    :param build_options_overrides: Build options to override the default build options.
        Also overrides any values loaded from the build options file.
    :param on_build_dir_created: Callback function to be called after the build directory is
        created. The function will be called with the build directory path as an argument.
    :raises FileNotFoundError: If the plugin path does not exist.
    :raises shutil.Error: If there is an error preparing the build directory.
    """

    if not plugin_path.exists():
        logger.error(f"Plugin path {plugin_path} does not exist")
        raise FileNotFoundError(f"Plugin path {plugin_path} does not exist")

    if build_dir_path.exists():
        try:
            logger.info(f"Clearing build directory: {build_dir_path}")
            shutil.rmtree(build_dir_path)
        except shutil.Error as err:
            logger.error(f"Unable to clear build directory: {build_dir_path}")
            raise err

    try:
        logger.info(f"Copying plugin code to build directory: {plugin_path} -> {build_dir_path}")
        shutil.copytree(plugin_path, build_dir_path, dirs_exist_ok=True)
    except shutil.Error as err:
        logger.error(
            f"Unable to copy plugin code to build directory: {plugin_path} -> {build_dir_path}"
        )
        raise err

    if on_build_dir_created:
        on_build_dir_created(build_dir_path)

    build_options = _override_build_options(
        build_options=parse_agent_plugin_build_options(build_dir_path),
        overrides=build_options_overrides,
        new_defaults=_get_default_build_options(),
    )
    logger.debug(f"Using build options: {build_options.model_dump()}")
    create_agent_plugin_archive(build_dir_path, dist_dir_path, agent_plugin_manifest, build_options)


def get_agent_plugin_manifest(build_dir_path: Path) -> AgentPluginManifest:
    """
    Get the Agent Plugin manifest from the build directory.

    :param build_dir_path: Path to the build directory.
    :raises FileNotFoundError: If the manifest file does not exist.
    :raises yaml.YAMLError: If the manifest file is not a valid YAML file.
    :return: The Agent Plugin manifest.
    """
    manifest_file_path = _get_plugin_manifest_filename(build_dir_path)

    logger.info(f"Reading plugin manifest file: {manifest_file_path}")
    with manifest_file_path.open("r") as f:
        return AgentPluginManifest(**yaml.safe_load(f))


def _get_default_build_options() -> AgentPluginBuildOptions:
    return AgentPluginBuildOptions()


def _override_build_options(
    build_options: AgentPluginBuildOptions,
    overrides: AgentPluginBuildOptions,
    new_defaults: AgentPluginBuildOptions,
) -> AgentPluginBuildOptions:
    logger.debug(f"Build options default overrides: {new_defaults.model_dump(exclude_unset=True)}")
    logger.debug(f"Build options from file: {build_options.model_dump(exclude_unset=True)}")
    logger.debug(f"Build options overrides: {overrides.model_dump(exclude_unset=True)}")
    build_options_dict = build_options.model_dump(exclude_defaults=True, exclude_unset=True)
    overrides_dict = overrides.model_dump(exclude_defaults=True, exclude_unset=True)
    new_defaults_dict = new_defaults.model_dump(exclude_unset=True)

    options_dict = new_defaults_dict
    options_dict.update(build_options_dict)
    options_dict.update(overrides_dict)
    return AgentPluginBuildOptions(**options_dict)


def create_agent_plugin_archive(
    build_dir_path: Path,
    dist_dir_path: Path,
    agent_plugin_manifest: AgentPluginManifest,
    build_options: AgentPluginBuildOptions,
):
    """
    Create the Agent Plugin tar archive.

    :param build_dir_path: Path to the build directory.
    :param dist_dir_path: Path to the dist directory.
    :param source_dirname: Name of the plugin source directory.
    :param agent_plugin_manifest: Agent Plugin manifest.
    """

    dependency_method = build_options.platform_dependencies
    generate_vendor_directories(
        build_dir_path, build_options.source_dir, agent_plugin_manifest, dependency_method
    )
    generate_plugin_config_schema(build_dir_path, build_options.source_dir, agent_plugin_manifest)
    create_source_archive(build_dir_path, build_options.source_dir)
    plugin_archive = create_plugin_archive(build_dir_path, agent_plugin_manifest)
    _copy_plugin_archive_to_dist(plugin_archive, dist_dir_path)


def generate_vendor_directories(
    build_dir_path: Path,
    source_dirname: str,
    agent_plugin_manifest: AgentPluginManifest,
    dependency_method: PlatformDependencyPackagingMethod,
):
    """
    Generate the vendor directories for the plugin.

    If the plugin supports multiple operating systems and the dependency_method is AUTODETECT, the
    function will try to generate a common vendor directory. If a common vendor directory is not
    possible, it will generate separate vendor directories for each supported operating system.

    :param build_dir_path: Path to the build directory.
    :param source_dirname: Name of the plugin source directory.
    :param agent_plugin_manifest: Agent Plugin manifest.
    :param dependency_method: Platform dependency packaging method of the vendor directories.
    """
    import os

    UID = os.getuid()
    GID = os.getgid()

    logger.info(
        f"Generating vendor directories for plugin: {agent_plugin_manifest.name}, "
        f"dependency_method: {dependency_method}"
    )
    generate_requirements_file(build_dir_path)
    if dependency_method == PlatformDependencyPackagingMethod.COMMON:
        generate_common_vendor_dir(build_dir_path, source_dirname, UID, GID)
    elif dependency_method == PlatformDependencyPackagingMethod.SEPARATE:
        for os_type in agent_plugin_manifest.supported_operating_systems:
            generate_vendor_dirs(build_dir_path, source_dirname, os_type, UID, GID)
    else:
        if len(agent_plugin_manifest.supported_operating_systems) > 1:
            common_dir_possible = check_if_common_vendor_dir_possible(build_dir_path, UID, GID)
            if common_dir_possible:
                generate_common_vendor_dir(build_dir_path, source_dirname, UID, GID)
            else:
                for os_type in agent_plugin_manifest.supported_operating_systems:
                    generate_vendor_dirs(build_dir_path, source_dirname, os_type, UID, GID)


def generate_plugin_config_schema(
    build_dir_path: Path, source_dirname: str, agent_plugin_manifest: AgentPluginManifest
):
    """
    Generate the config-schema file for the plugin. The schema is generated
    based on the plugin's options model.

    :param build_dir_path: Path to the build directory.
    :param source_dirname: Name of the plugin source directory.
    :param agent_plugin_manifest: Agent Plugin manifest.
    """
    plugin_options_file_path = (
        build_dir_path / source_dirname / f"{agent_plugin_manifest.name.lower()}_options.py"
    )
    plugin_config_schema_file_path = build_dir_path / CONFIG_SCHEMA
    plugin_options_model_name = f"{agent_plugin_manifest.name}Options"

    if plugin_config_schema_file_path.exists():
        logger.info(f"Skipping generating config-schema. Reason: {CONFIG_SCHEMA} already exists")
        return

    config_schema = {"type": "object"}
    if plugin_options_file_path.exists():
        plugin_options_filename = plugin_options_file_path.stem
        import sys

        sys.path.append(str(build_dir_path / source_dirname))
        options = getattr(import_module(plugin_options_filename), plugin_options_model_name)
        config_schema = {"properties": options.model_json_schema()["properties"]}

    logger.info(f"Generating config-schema for plugin: {agent_plugin_manifest.name}")
    schema_contents = json.dumps(config_schema)
    with plugin_config_schema_file_path.open("w") as f:
        f.write(schema_contents)


def create_source_archive(build_dir_path: Path, source_dirname: str) -> Path:
    """
    Create the source archive for the plugin.

    :param build_dir_path: Path to the build directory.
    :param source_dirname: Name of the plugin source directory.
    :return: Path to the source archive.
    """
    source_archive = build_dir_path / f"{SOURCE}.tar.gz"
    source_build_dir_path = build_dir_path / source_dirname

    logger.info(f"Creating source archive: {source_archive} ")
    with tarfile.open(str(source_archive), "w:gz") as tar:
        for item in source_build_dir_path.iterdir():
            tar.add(item, arcname=item.name, filter=_source_archive_filter)

    return source_archive


def _source_archive_filter(file_info: tarfile.TarInfo) -> tarfile.TarInfo | None:
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
    agent_plugin_manifest_file = _get_plugin_manifest_filename(build_dir_path)

    logger.info(f"Creating plugin archive: {plugin_archive}")
    with tarfile.open(str(plugin_archive), "w") as tar:
        tar.add(source_archive, arcname=source_archive.name)
        tar.add(config_schema_file, arcname=config_schema_file.name)
        tar.add(agent_plugin_manifest_file, arcname=agent_plugin_manifest_file.name)

    logger.info(f"Plugin archive created: {plugin_archive}")
    return plugin_archive


def _get_plugin_archive_name(agent_plugin_manifest: AgentPluginManifest) -> str:
    return f"{agent_plugin_manifest.name}-{agent_plugin_manifest.plugin_type.value.lower()}.tar"


def _get_plugin_manifest_filename(build_dir_path: Path) -> Path:
    agent_plugin_manifest_file = build_dir_path / f"{MANIFEST}.yaml"
    if agent_plugin_manifest_file.exists():
        return agent_plugin_manifest_file

    return build_dir_path / f"{MANIFEST}.yml"


def _copy_plugin_archive_to_dist(plugin_filepath: Path, dist_dir_path: Path):
    if not dist_dir_path.exists():
        logger.info(f"Creating dist directory: {dist_dir_path}")
        dist_dir_path.mkdir(exist_ok=True)

    destination_filepath = dist_dir_path / plugin_filepath.name
    logger.info(f"Copying plugin archive: {plugin_filepath} -> {destination_filepath}")
    shutil.copy2(plugin_filepath, destination_filepath)
