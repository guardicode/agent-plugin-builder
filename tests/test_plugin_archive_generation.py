import shutil
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

TEST_SOURCE_DIR_NAME = "test_source_dir"
TEST_BUILD_DIR_NAME = "test_build_dir"

PLUGIN_ARCHIVE_NAME = "Plugin-exploiter.tar"
MOCK_SOURCE_DIR_NAME = "mock_exploiter"
MOCK_AGENT_PLUGIN_MANIFEST = AgentPluginManifest(
    name="Mock",
    plugin_type=AgentPluginType.EXPLOITER,
    supported_operating_systems=(OperatingSystem.LINUX,),
    target_operating_systems=(OperatingSystem.LINUX,),
    title="Mock Exploiter",
    version="0.1.0",
    safe=True,
)


def list_tar_contents(tar_gz_path: Path) -> list[str]:
    """
    List the contents of a .tar.gz archive.

    :param tar_gz_path: Path to the .tar.gz file.
    :return: List of file names in the archive.
    """
    with tarfile.open(tar_gz_path, "r") as tar:
        return tar.getnames()


@pytest.fixture
def agent_plugin_build_options_plugin(tmpdir: str, data_for_tests_dir: Path):
    plugin_dir_path_data = data_for_tests_dir / "mock-exploiter"
    plugin_dir_path = Path(tmpdir) / "mock-exploiter"
    plugin_dir_path.mkdir()
    shutil.copytree(plugin_dir_path_data, plugin_dir_path, dirs_exist_ok=True)
    build_dir_path = plugin_dir_path / "build"
    build_dir_path.mkdir()
    shutil.copytree(plugin_dir_path, build_dir_path, dirs_exist_ok=True)
    dist_dir_path = plugin_dir_path / "dist"
    dist_dir_path.mkdir()

    def make_agent_plugin_build_options(platform_dependencies: PlatformDependencyPackagingMethod):
        return AgentPluginBuildOptions(
            plugin_dir_path=plugin_dir_path,
            build_dir_path=build_dir_path,
            dist_dir_path=dist_dir_path,
            source_dir_name=MOCK_SOURCE_DIR_NAME,
            platform_dependencies=platform_dependencies,
            verify_hashes=False,
        )

    return make_agent_plugin_build_options


@pytest.mark.parametrize(
    "platform_dependencies, expected_source_tar_contents",
    [
        (
            PlatformDependencyPackagingMethod.COMMON,
            [
                "vendor",
                "__init__.py",
                "plugin.py",
                "mock_options.py",
            ],
        ),
        (
            PlatformDependencyPackagingMethod.SEPARATE,
            [
                "vendor-linux",
                "__init__.py",
                "plugin.py",
                "mock_options.py",
            ],
        ),
        (
            PlatformDependencyPackagingMethod.AUTODETECT,
            [
                "vendor-linux",
                "__init__.py",
                "plugin.py",
                "mock_options.py",
            ],
        ),
    ],
)
@pytest.mark.integration
def test_create_agent_plugin_archive(
    agent_plugin_build_options_plugin,
    platform_dependencies: PlatformDependencyPackagingMethod,
    expected_source_tar_contents: list[str],
):
    agent_plugin_build_options = agent_plugin_build_options_plugin(platform_dependencies)

    create_agent_plugin_archive(agent_plugin_build_options, MOCK_AGENT_PLUGIN_MANIFEST)

    source_archive_path = agent_plugin_build_options.build_dir_path / f"{SOURCE}.tar.gz"
    plugin_archive_path = agent_plugin_build_options.dist_dir_path / "Mock-exploiter.tar"
    assert list_tar_contents(source_archive_path) == expected_source_tar_contents
    assert plugin_archive_path.exists()
    assert list_tar_contents(plugin_archive_path) == [
        f"{SOURCE}.tar.gz",
        CONFIG_SCHEMA,
        f"{MANIFEST}.yaml",
    ]


@pytest.mark.integration
def test_create_agent_plugin_archive__dist_dir_created(
    agent_plugin_build_options_plugin: AgentPluginBuildOptions,
    agent_plugin_manifest: AgentPluginManifest,
):
    agent_plugin_build_options = agent_plugin_build_options_plugin(
        PlatformDependencyPackagingMethod.COMMON
    )
    agent_plugin_build_options.dist_dir_path.rmdir()

    create_agent_plugin_archive(agent_plugin_build_options, MOCK_AGENT_PLUGIN_MANIFEST)

    assert agent_plugin_build_options.dist_dir_path.exists()
    assert agent_plugin_build_options.dist_dir_path.is_dir()


def test_create_agent_plugin_archive__empty_plugin(
    monkeypatch,
    agent_plugin_build_options: AgentPluginBuildOptions,
    agent_plugin_manifest: AgentPluginManifest,
):
    with pytest.raises(FileNotFoundError):
        create_agent_plugin_archive(agent_plugin_build_options, agent_plugin_manifest)


def test_create_source_archive(tmpdir: str):
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / TEST_BUILD_DIR_NAME
    build_dir_path.mkdir()
    source_dir_path = build_dir_path / TEST_SOURCE_DIR_NAME
    source_dir_path.mkdir()

    (source_dir_path / "testfile.py").touch()
    for exclude_file in EXCLUDE_SOURCE_FILES:
        (source_dir_path / exclude_file).touch()

    source_archive_path = create_source_archive(build_dir_path, TEST_SOURCE_DIR_NAME)

    assert source_archive_path.exists()
    assert source_archive_path.name == f"{SOURCE}.tar.gz"
    actual_tar_files = list_tar_contents(source_archive_path)
    assert actual_tar_files == ["testfile.py"]
    assert EXCLUDE_SOURCE_FILES not in actual_tar_files


def test_create_plugin_archive(tmpdir: str, agent_plugin_manifest: AgentPluginManifest):
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / TEST_BUILD_DIR_NAME
    build_dir_path.mkdir()
    (build_dir_path / CONFIG_SCHEMA).touch()
    source_archive_path = build_dir_path / f"{SOURCE}.tar.gz"
    source_archive_path.touch()
    agent_plugin_manifest_file = build_dir_path / f"{MANIFEST}.yml"
    agent_plugin_manifest_file.touch()

    plugin_archive_path = create_plugin_archive(build_dir_path, agent_plugin_manifest)

    assert plugin_archive_path.exists()
    assert plugin_archive_path.name == PLUGIN_ARCHIVE_NAME
    assert list_tar_contents(plugin_archive_path) == [
        f"{SOURCE}.tar.gz",
        CONFIG_SCHEMA,
        f"{MANIFEST}.yml",
    ]


def test_create_source_archive__os_error(monkeypatch, tmpdir: str):
    monkeypatch.setattr(tarfile, "open", MagicMock(side_effect=OSError("Test OSError")))
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / TEST_BUILD_DIR_NAME
    build_dir_path.mkdir()
    source_dir_path = build_dir_path / TEST_SOURCE_DIR_NAME
    source_dir_path.mkdir()

    (source_dir_path / "testfile.py").touch()

    with pytest.raises(OSError):
        create_source_archive(build_dir_path, TEST_SOURCE_DIR_NAME)


def test_create_plugin_archive__removes_existing_archive(
    monkeypatch, tmpdir: str, agent_plugin_manifest: AgentPluginManifest
):
    monkeypatch.setattr(tarfile, "open", MagicMock())
    temp_dir = Path(tmpdir)
    build_dir_path = temp_dir / TEST_BUILD_DIR_NAME
    build_dir_path.mkdir()
    (build_dir_path / PLUGIN_ARCHIVE_NAME).touch()

    assert (build_dir_path / PLUGIN_ARCHIVE_NAME).exists()

    plugin_archive_path = create_plugin_archive(build_dir_path, agent_plugin_manifest)

    assert not plugin_archive_path.exists()
