import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from monkeytypes import AgentPluginManifest

from agent_plugin_builder import generate_plugin_config_schema
from agent_plugin_builder.plugin_schema_generation import CONFIG_SCHEMA


def test_generate_plugin_config_schema__schema_exists(
    monkeypatch, agent_plugin_manifest: AgentPluginManifest
):
    monkeypatch.setattr("agent_plugin_builder.plugin_schema_generation.Path.exists", lambda _: True)

    assert (
        generate_plugin_config_schema(
            Path("build_dir_path"), "source_dir_name", agent_plugin_manifest
        )
        is None
    )


def test_generate_plugin_config_schema__default_schema(
    monkeypatch, tmpdir: str, agent_plugin_manifest: AgentPluginManifest
):
    monkeypatch.setattr(
        "agent_plugin_builder.plugin_schema_generation.Path.exists", lambda _: False
    )
    expected_schema = '{"type": "object"}'
    build_dir_path = Path(tmpdir)

    generate_plugin_config_schema(build_dir_path, "source_dir_name", agent_plugin_manifest)

    assert (build_dir_path / CONFIG_SCHEMA).read_text() == expected_schema


def test_generate_plugin_config_schema__from_options(
    data_for_tests_dir: Path, tmpdir: str, agent_plugin_manifest: AgentPluginManifest
):
    expected_schema = {
        "properties": {
            "agent_binary_download_timeout": {
                "default": 60.0,
                "description": "The maximum time (in seconds) to wait for a successfully exploit",
                "exclusiveMinimum": 0.0,
                "title": "Agent Binary Download Timeout",
                "type": "number",
            }
        }
    }
    build_dir_path = Path(tmpdir)
    (build_dir_path / "source_dir_name").mkdir()
    (build_dir_path / "source_dir_name" / "plugin_options.py").write_text(
        (data_for_tests_dir / "plugin_options.py").read_text()
    )

    generate_plugin_config_schema(build_dir_path, "source_dir_name", agent_plugin_manifest)

    assert (build_dir_path / CONFIG_SCHEMA).read_text() == json.dumps(expected_schema)


def test_generate_plugin_config_schema__exception(
    monkeypatch, agent_plugin_manifest: AgentPluginManifest
):
    monkeypatch.setattr(
        "agent_plugin_builder.plugin_schema_generation.json.dumps",
        MagicMock(side_effect=Exception),
    )

    with pytest.raises(Exception):
        generate_plugin_config_schema(
            Path("build_dir_path"), "source_dir_name", agent_plugin_manifest
        )
