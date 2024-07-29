from pathlib import Path

import pytest
from monkeytypes import AgentPluginManifest, AgentPluginType, OperatingSystem

from agent_plugin_builder import get_agent_plugin_manifest, get_plugin_manifest_file_path

EXPECTED_YAML_MANIFEST = AgentPluginManifest(
    name="plugin_name_yaml",
    plugin_type=AgentPluginType.EXPLOITER,
    supported_operating_systems=(OperatingSystem.WINDOWS, OperatingSystem.LINUX),
    target_operating_systems=(OperatingSystem.WINDOWS, OperatingSystem.LINUX),
    title="plugin_title_yaml",
    version="1.0.0",
    description="plugin_description_yaml",
    link_to_documentation="https://plugin_yaml_documentation.com",
    safe=True,
)

EXPECTED_YML_MANIFEST = AgentPluginManifest(
    name="plugin_name_yml",
    plugin_type=AgentPluginType.PAYLOAD,
    supported_operating_systems=(OperatingSystem.WINDOWS,),
    target_operating_systems=(OperatingSystem.WINDOWS,),
    title="plugin_title_yml",
    version="1.0.1",
    description="plugin_description_yml",
    link_to_documentation="https://plugin_yml_documentation.com",
    safe=False,
)


@pytest.mark.parametrize(
    "manifest_name, expected_manifest",
    [("manifest.yaml", EXPECTED_YAML_MANIFEST), ("manifest.yml", EXPECTED_YML_MANIFEST)],
)
def test_get_agent_plugin_manifest(
    monkeypatch, manifest_name, expected_manifest, data_for_tests_dir
):
    monkeypatch.setattr(
        "agent_plugin_builder.plugin_manifest.get_plugin_manifest_file_path",
        lambda _: data_for_tests_dir / manifest_name,
    )

    assert get_agent_plugin_manifest(data_for_tests_dir) == expected_manifest


@pytest.mark.parametrize(
    "path_exists, expected_manifest_name", [(True, "manifest.yaml"), (False, "manifest.yml")]
)
def test_get_plugin_manifest_file_path(monkeypatch, path_exists, expected_manifest_name):
    monkeypatch.setattr("agent_plugin_builder.plugin_manifest.Path.exists", lambda _: path_exists)
    build_dir_path = Path("build_dir_path")

    assert get_plugin_manifest_file_path(build_dir_path) == build_dir_path / expected_manifest_name
