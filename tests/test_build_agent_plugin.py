import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from monkeytypes import AgentPluginManifest

from agent_plugin_builder import (
    AgentPluginBuildOptions,
    PlatformDependencyPackagingMethod,
    build_agent_plugin_archive,
)

AGENT_PLUGIN_MANIFEST = AgentPluginManifest(
    name="testplugin",
    plugin_type="Exploiter",
    supported_operating_systems=["linux"],
    target_operating_systems=["linux"],
    title="Test Plugin",
    version="1.0.0",
    link_to_documentation="https://example.com",
)


@pytest.fixture
def agent_plugin_build_options(tmpdir):
    plugin_dir_path = Path(tmpdir / "plugin-dir")
    plugin_dir_path.mkdir()
    (plugin_dir_path / "build").mkdir()
    (plugin_dir_path / "dist").mkdir()

    return AgentPluginBuildOptions(
        plugin_dir_path=plugin_dir_path,
        build_dir_path=(plugin_dir_path / "build"),
        dist_dir_path=(plugin_dir_path / "dist"),
        source_dir_name="plugin_dir",
        platform_dependencies=PlatformDependencyPackagingMethod.AUTODETECT,
        verify_hashes=False,
    )


def test_build_agent_plugin_archive__plugin_dir_not_found(agent_plugin_build_options):
    agent_plugin_build_options.dist_dir_path.rmdir()
    agent_plugin_build_options.build_dir_path.rmdir()
    agent_plugin_build_options.plugin_dir_path.rmdir()

    with pytest.raises(FileNotFoundError):
        build_agent_plugin_archive(agent_plugin_build_options, AGENT_PLUGIN_MANIFEST)


def test_build_agent_plugin_archive__build_dir_not_found(agent_plugin_build_options):
    agent_plugin_build_options.dist_dir_path.rmdir()
    agent_plugin_build_options.build_dir_path.rmdir()

    with pytest.raises(FileNotFoundError):
        build_agent_plugin_archive(agent_plugin_build_options, AGENT_PLUGIN_MANIFEST)


@pytest.mark.parametrize("shutil_method", ["rmtree", "copytree"])
def test_build_agent_plugin_archive__exceptions(
    monkeypatch, agent_plugin_build_options, shutil_method
):
    monkeypatch.setattr(f"shutil.{shutil_method}", MagicMock(side_effect=shutil.Error))

    with pytest.raises(shutil.Error):
        build_agent_plugin_archive(agent_plugin_build_options, AGENT_PLUGIN_MANIFEST)


def test_build_agent_plugin_archive__on_build_created(monkeypatch, agent_plugin_build_options):
    mock_create_agent_plugin_archive = MagicMock(return_value=None)
    monkeypatch.setattr(
        "agent_plugin_builder.build_agent_plugin.create_agent_plugin_archive",
        mock_create_agent_plugin_archive,
    )
    on_build_dir_created = MagicMock()

    build_agent_plugin_archive(
        agent_plugin_build_options, AGENT_PLUGIN_MANIFEST, on_build_dir_created=on_build_dir_created
    )

    on_build_dir_created.assert_called_once_with(agent_plugin_build_options.build_dir_path)
    mock_create_agent_plugin_archive.assert_called_once_with(
        agent_plugin_build_options, AGENT_PLUGIN_MANIFEST
    )
