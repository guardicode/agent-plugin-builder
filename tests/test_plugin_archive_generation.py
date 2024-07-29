import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from monkeytypes import AgentPluginManifest, AgentPluginType, OperatingSystem

from agent_plugin_builder import (
    AgentPluginBuildOptions,
    PlatformDependencyPackagingMethod,
    create_agent_plugin_archive,
    create_plugin_archive,
    create_source_archive,
)
from agent_plugin_builder.plugin_archive_generation import EXCLUDE_SOURCE_FILES, SOURCE
from agent_plugin_builder.plugin_manifest import MANIFEST
from agent_plugin_builder.plugin_schema_generation import CONFIG_SCHEMA

AGENT_PLUGIN_MANIFEST = AgentPluginManifest(
    name="Plugin",
    plugin_type=AgentPluginType.EXPLOITER,
    supported_operating_systems=(OperatingSystem.WINDOWS, OperatingSystem.LINUX),
    target_operating_systems=(OperatingSystem.WINDOWS, OperatingSystem.LINUX),
    title="plugin_title",
    version="1.0.0",
    description="plugin_description",
    link_to_documentation="https://plugin_documentation.com",
    safe=True,
)

PLUGIN_ARCHIVE_NAME = "Plugin-exploiter.tar"


def list_tar_contents(tar_gz_path):
    """
    List the contents of a .tar.gz archive.

    :param tar_gz_path: Path to the .tar.gz file.
    :return: List of file names in the archive.
    """
    with tarfile.open(tar_gz_path, "r") as tar:
        return tar.getnames()


@pytest.fixture
def agent_plugin_build_options(tmpdir):
    temp_dir = Path(tmpdir)
    plugin_dir_path = temp_dir / "plugin_dir_path"
    plugin_dir_path.mkdir()
    build_dir_path = temp_dir / "build_dir_path"
    build_dir_path.mkdir()
    dist_dir_path = temp_dir / "dist_dir_path"
    dist_dir_path.mkdir()

    return AgentPluginBuildOptions(
        plugin_dir_path=plugin_dir_path,
        build_dir_path=build_dir_path,
        dist_dir_path=dist_dir_path,
        source_dir_name="source_dir_name",
        platform_dependencies=PlatformDependencyPackagingMethod.COMMON,
        verify_hashes=False,
    )


def test_create_agent_plugin_archive__empty_plugin(monkeypatch, agent_plugin_build_options):
    with pytest.raises(FileNotFoundError):
        create_agent_plugin_archive(agent_plugin_build_options, AGENT_PLUGIN_MANIFEST)


def test_create_source_archive(tmpdir):
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / "build_dir_path"
    build_dir_path.mkdir()
    source_dir_name = "source_dir_name"
    source_dir_path = build_dir_path / source_dir_name
    source_dir_path.mkdir()

    (source_dir_path / "testfile.py").touch()
    for exclude_file in EXCLUDE_SOURCE_FILES:
        (source_dir_path / exclude_file).touch()

    source_archive_path = create_source_archive(build_dir_path, source_dir_name)

    assert source_archive_path.exists()
    assert source_archive_path.name == f"{SOURCE}.tar.gz"
    actual_tar_files = list_tar_contents(source_archive_path)
    assert actual_tar_files == ["testfile.py"]
    assert EXCLUDE_SOURCE_FILES not in actual_tar_files


def test_create_plugin_archive(tmpdir):
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / "build_dir_path"
    build_dir_path.mkdir()
    (build_dir_path / CONFIG_SCHEMA).touch()
    source_archive_path = build_dir_path / f"{SOURCE}.tar.gz"
    source_archive_path.touch()
    agent_plugin_manifest_file = build_dir_path / f"{MANIFEST}.yml"
    agent_plugin_manifest_file.touch()

    plugin_archive_path = create_plugin_archive(build_dir_path, AGENT_PLUGIN_MANIFEST)

    assert plugin_archive_path.exists()
    assert plugin_archive_path.name == PLUGIN_ARCHIVE_NAME
    assert list_tar_contents(plugin_archive_path) == [
        f"{SOURCE}.tar.gz",
        CONFIG_SCHEMA,
        f"{MANIFEST}.yml",
    ]


def test_create_source_archive__os_error(monkeypatch, tmpdir):
    monkeypatch.setattr(tarfile, "open", MagicMock(side_effect=OSError("Test OSError")))
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / "build_dir_path"
    build_dir_path.mkdir()
    source_dir_name = "source_dir_name"
    source_dir_path = build_dir_path / source_dir_name
    source_dir_path.mkdir()

    (source_dir_path / "testfile.py").touch()

    with pytest.raises(OSError):
        create_source_archive(build_dir_path, source_dir_name)


def test_create_plugin_archive__removes_existing_archive(monkeypatch, tmpdir):
    monkeypatch.setattr(tarfile, "open", MagicMock())
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / "build_dir_path"
    build_dir_path.mkdir()
    (build_dir_path / PLUGIN_ARCHIVE_NAME).touch()

    assert (build_dir_path / PLUGIN_ARCHIVE_NAME).exists()

    plugin_archive_path = create_plugin_archive(build_dir_path, AGENT_PLUGIN_MANIFEST)

    assert not plugin_archive_path.exists()
