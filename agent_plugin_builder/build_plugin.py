import argparse
import json
import shutil
import tarfile
from importlib import import_module
from pathlib import Path

import yaml
from monkeytypes import AgentPluginManifest

from .build_options import PlatformDependencyPackagingMethod, parse_agent_plugin_build_options
from .vendor_dirs import (
    check_if_common_vendor_dir_possible,
    generate_common_vendor_dir,
    generate_requirements_file,
    generate_vendor_dirs,
)


def main():
    parser = argparse.ArgumentParser(description="Build plugin")
    parser.add_argument("plugin_path", metavar="PLUGIN_PATH", type=Path, help="Path to the plugin)")
    parser.add_argument(
        "-b",
        "--build_dir_path",
        metavar="BUILD_DIR_PATH",
        type=Path,
        default=(Path.cwd() / "build"),
        help="Optional Path to the build directory. Default: <current_working_directory>/build.",
    )
    parser.add_argument(
        "-d",
        "--dist_dir_path",
        metavar="DIST_DIR_PATH",
        type=Path,
        default=(Path.cwd() / "dist"),
        help="Optional Path to the dist directory. Default: <current_working_directory>/dist.",
    )
    args = parser.parse_args()

    if not args.plugin_path.exists():
        raise FileNotFoundError(f"Plugin path {args.plugin_path} does not exist")

    build_agent_plugin(args.plugin_path, args.build_dir_path, args.dist_dir_path)


def build_agent_plugin(
    plugin_path: Path,
    plugin_build_dir: Path = (Path.cwd() / "build"),
    dist_dir: Path = (Path.cwd() / "dist"),
):
    agent_plugin_manifest = get_agent_plugin_manifest(plugin_path)

    if not plugin_build_dir.exists():
        plugin_build_dir.mkdir(exist_ok=True)

    shutil.copytree(plugin_path, plugin_build_dir, dirs_exist_ok=True)

    create_agent_plugin_archive(plugin_build_dir, agent_plugin_manifest)


def get_agent_plugin_manifest(plugin_path: Path) -> AgentPluginManifest:
    manifest_file_path = plugin_path / "manifest.yaml"
    if not manifest_file_path.exists():
        manifest_file_path = plugin_path / "manifest.yml"

    with manifest_file_path.open("r") as f:
        return AgentPluginManifest(**yaml.safe_load(f))


def create_agent_plugin_archive(
    build_dir: Path, manifest: AgentPluginManifest, dist_dir: Path = (Path.cwd() / "dist")
):
    build_options = parse_agent_plugin_build_options(build_dir)
    dependency_method = build_options.platform_dependencies
    generate_vendor_directories(build_dir, manifest, dependency_method)
    generate_plugin_config_schema(build_dir, manifest)
    create_source_archive(build_dir)
    create_plugin_archive(build_dir, manifest, dist_dir)


def generate_vendor_directories(
    plugin_dir: Path,
    agent_plugin_manifest: AgentPluginManifest,
    dependency_method: PlatformDependencyPackagingMethod,
):
    import os

    UID = os.getuid()
    GID = os.getgid()

    generate_requirements_file(plugin_dir)
    if dependency_method == PlatformDependencyPackagingMethod.COMMON:
        generate_common_vendor_dir(plugin_dir, UID, GID)
    elif dependency_method == PlatformDependencyPackagingMethod.SEPARATE:
        for os_type in agent_plugin_manifest.supported_operating_systems:
            generate_vendor_dirs(plugin_dir, os_type, UID, GID)
    else:
        if len(agent_plugin_manifest.supported_operating_systems) > 1:
            common_dir_possible = check_if_common_vendor_dir_possible(plugin_dir, UID, GID)
            if common_dir_possible:
                generate_common_vendor_dir(plugin_dir, UID, GID)
            else:
                for os_type in agent_plugin_manifest.supported_operating_systems:
                    generate_vendor_dirs(plugin_dir, os_type, UID, GID)


def generate_plugin_config_schema(plugin_path: Path, agent_plugin_manifest: AgentPluginManifest):
    plugin_options_file_path = (
        plugin_path / "src" / f"{agent_plugin_manifest.name.lower()}_options.py"
    )
    plugin_config_schema_file_path = plugin_path / "config-schema.json"
    plugin_options_model_name = f"{agent_plugin_manifest.name}Options"

    if plugin_config_schema_file_path.exists():
        print(
            "\033[0m\033[91m"
            "Skipping generating config-schema."
            " Reason: config_schema.json already exists"
            " \033[0m",
        )
        return

    config_schema = {"type": "object"}
    if plugin_options_file_path.exists():
        plugin_options_filename = plugin_options_file_path.stem
        import sys

        sys.path.append(str(plugin_path / "src"))
        options = getattr(import_module(plugin_options_filename), plugin_options_model_name)
        config_schema = {"properties": options.model_json_schema()["properties"]}

    schema_contents = json.dumps(config_schema)
    with plugin_config_schema_file_path.open("w") as f:
        f.write(schema_contents)


def create_source_archive(build_dir: Path) -> Path:
    source_arcname = "source"
    source_archive = build_dir / f"{source_arcname}.tar.gz"
    source_build_dir_path = build_dir / "src"
    with tarfile.open(str(source_archive), "w:gz") as tar:
        tar.add(source_build_dir_path, arcname=source_arcname, filter=_source_archive_filter)

    return source_archive


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
    build_dir: Path,
    agent_plugin_manifest: AgentPluginManifest,
    plugin_dist_dir: Path = (Path.cwd() / "dist"),
) -> Path:
    if not plugin_dist_dir.exists():
        plugin_dist_dir.mkdir(exist_ok=True)
    plugin_archive = (
        plugin_dist_dir
        / f"{agent_plugin_manifest.name}_{agent_plugin_manifest.plugin_type.value}.tar"
    )
    if plugin_archive.exists():
        plugin_archive.unlink()

    source_archive = build_dir / "source.tar.gz"
    config_schema_file = build_dir / "config-schema.json"
    agent_plugin_manifest_file = build_dir / "manifest.yaml"
    if not agent_plugin_manifest_file.exists():
        agent_plugin_manifest_file = build_dir / "manifest.yml"

    with tarfile.open(str(plugin_archive), "w") as tar:
        tar.add(source_archive, arcname=source_archive.name)
        tar.add(config_schema_file, arcname=config_schema_file.name)
        tar.add(agent_plugin_manifest_file, arcname=agent_plugin_manifest_file.name)

    return plugin_archive
