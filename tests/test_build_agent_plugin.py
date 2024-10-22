import shutil
from unittest.mock import MagicMock

import pytest
from monkeytypes import AgentPluginManifest

from agent_plugin_builder import AgentPluginBuildOptions, build_agent_plugin_archive


def test_build_agent_plugin_archive__plugin_dir_not_found(
    agent_plugin_build_options: AgentPluginBuildOptions, agent_plugin_manifest: AgentPluginManifest
):
    agent_plugin_build_options.dist_dir_path.rmdir()
    agent_plugin_build_options.build_dir_path.rmdir()
    agent_plugin_build_options.plugin_dir_path.rmdir()

    with pytest.raises(FileNotFoundError):
        build_agent_plugin_archive(agent_plugin_build_options, agent_plugin_manifest)


def test_build_agent_plugin_archive__build_dir_not_found(
    agent_plugin_build_options: AgentPluginBuildOptions, agent_plugin_manifest: AgentPluginManifest
):
    agent_plugin_build_options.dist_dir_path.rmdir()
    agent_plugin_build_options.build_dir_path.rmdir()

    with pytest.raises(FileNotFoundError):
        build_agent_plugin_archive(agent_plugin_build_options, agent_plugin_manifest)


@pytest.mark.parametrize("shutil_method", ["rmtree", "copytree"])
def test_build_agent_plugin_archive__exceptions(
    monkeypatch,
    agent_plugin_build_options: AgentPluginBuildOptions,
    shutil_method: str,
    agent_plugin_manifest: AgentPluginManifest,
):
    monkeypatch.setattr(f"shutil.{shutil_method}", MagicMock(side_effect=shutil.Error))

    with pytest.raises(shutil.Error):
        build_agent_plugin_archive(agent_plugin_build_options, agent_plugin_manifest)


def test_build_agent_plugin_archive__on_build_created(
    monkeypatch,
    agent_plugin_build_options: AgentPluginBuildOptions,
    agent_plugin_manifest: AgentPluginManifest,
):
    mock_create_agent_plugin_archive = MagicMock(return_value=None)
    monkeypatch.setattr(
        "agent_plugin_builder.build_agent_plugin.create_agent_plugin_archive",
        mock_create_agent_plugin_archive,
    )
    on_build_dir_created = MagicMock()

    build_agent_plugin_archive(
        agent_plugin_build_options, agent_plugin_manifest, on_build_dir_created=on_build_dir_created
    )

    on_build_dir_created.assert_called_once_with(agent_plugin_build_options.build_dir_path)
    mock_create_agent_plugin_archive.assert_called_once_with(
        agent_plugin_build_options, agent_plugin_manifest
    )
