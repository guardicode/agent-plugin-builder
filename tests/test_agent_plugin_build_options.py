import copy
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest

from agent_plugin_builder import AgentPluginBuildOptions, PlatformDependencyPackagingMethod
from agent_plugin_builder.agent_plugin_build_options import parse_agent_plugin_build_options

PLUGIN_DIR = tempfile.mkdtemp(prefix="plugin_dir_path_")
BUILD_DIR = tempfile.mkdtemp(prefix="build_dir_path_")
DIST_DIR = tempfile.mkdtemp(prefix="dist_dir_path_")
SOURCE_DIR_NAME = "source_dir_name"
PLATFORM_DEPENDENCIES = "common"
VERIFY_HASHES = False

AGENT_PLUGIN_BUILD_OPTIONS_DICT_IN: dict[str, Any] = {
    "plugin_dir_path": PLUGIN_DIR,
    "build_dir_path": BUILD_DIR,
    "dist_dir_path": DIST_DIR,
    "source_dir_name": SOURCE_DIR_NAME,
    "platform_dependencies": PLATFORM_DEPENDENCIES,
    "verify_hashes": VERIFY_HASHES,
}

AGENT_PLUGIN_BUILD_OPTIONS_DICT_OUT: dict[str, Any] = copy.deepcopy(
    AGENT_PLUGIN_BUILD_OPTIONS_DICT_IN
)

AGENT_PLUGIN_BUILD_OPTIONS_DICT = {
    "plugin_dir_path": Path(PLUGIN_DIR),
    "build_dir_path": Path(BUILD_DIR),
    "dist_dir_path": Path(DIST_DIR),
    "source_dir_name": SOURCE_DIR_NAME,
    "platform_dependencies": PlatformDependencyPackagingMethod.COMMON,
    "verify_hashes": VERIFY_HASHES,
}

AGENT_PLUGIN_BUILD_OPTIONS_OBJECT = AgentPluginBuildOptions(
    plugin_dir_path=Path(PLUGIN_DIR),
    build_dir_path=Path(BUILD_DIR),
    dist_dir_path=Path(DIST_DIR),
    source_dir_name=SOURCE_DIR_NAME,
    platform_dependencies=PlatformDependencyPackagingMethod.COMMON,
    verify_hashes=VERIFY_HASHES,
)

AGENT_PLUGIN_BUILD_OPTIONS_NAMESPACE = Namespace(
    plugin_dir_path=Path(PLUGIN_DIR),
    build_dir_path=Path(BUILD_DIR),
    dist_dir_path=Path(DIST_DIR),
    source_dir_name=SOURCE_DIR_NAME,
    platform_dependencies=PlatformDependencyPackagingMethod.COMMON,
    verify=VERIFY_HASHES,
    verbosity=5,
)

INVALID_AGENT_PLUGIN_BUILD_OPTIONS_NAMESPACE = Namespace(
    plugin_dir_path=Path(PLUGIN_DIR),
    build_dir_path=Path(BUILD_DIR),
    dist_dir_path=Path(DIST_DIR),
    source_dir_name=SOURCE_DIR_NAME,
    platform_dependencies=PlatformDependencyPackagingMethod.COMMON,
    verify=VERIFY_HASHES,
    verbosity=5,
    invalid="invalid",
)


def test_agent_plugin_builder_options__serialization():
    assert AGENT_PLUGIN_BUILD_OPTIONS_OBJECT.to_json_dict() == AGENT_PLUGIN_BUILD_OPTIONS_DICT_OUT


def test_agent_plugin_builder_options__deserialization():
    assert (
        AgentPluginBuildOptions(**AGENT_PLUGIN_BUILD_OPTIONS_DICT_IN)
        == AGENT_PLUGIN_BUILD_OPTIONS_OBJECT
    )


@pytest.mark.parametrize(
    "source_dir_name",
    [
        "../../test_dir12341234",
        "/test_dir12341234",
        "test_dir/../../../12341234",
        "../../../",
        "..",
        ".",
        "$HOME",
        "~/",
        "!!",
        "!#",
        "!$",
        "name with spaces",
        "name; malicious command",
        "`shell_injection`",
        "$(shell_injection)",
        "bash -c shell_injection",
    ],
)
def test_agent_plugin_builder_options__source_dir_name__invalid(source_dir_name: str):
    with pytest.raises(ValueError):
        AgentPluginBuildOptions(
            plugin_dir_path=Path(PLUGIN_DIR),
            build_dir_path=Path(BUILD_DIR),
            dist_dir_path=Path(DIST_DIR),
            source_dir_name=source_dir_name,
            platform_dependencies=PlatformDependencyPackagingMethod.COMMON,
            verify_hashes=VERIFY_HASHES,
        )


@pytest.mark.parametrize(
    "plugin_dir_path",
    [
        "/path/to/nonexistent/dir",
        "C:\inva|id\path",  # noqa: W605
        "/home/user\invalid/path",  # noqa: W605
        "../../etc/passwd",
        '.."',
        "%2e%2e%2f",
        "..%252f",
        "'; rm -rf /; echo '",
        "ln -s /etc/passwd /home/user/fakepath",
        "/home/user/.hiddenfolder",
        "\\remote\share\path",  # noqa: W605
        "CON",
        "PRN",
    ],
)
def test_agent_plugin_builder_options__plugin_dir_path__invalid(plugin_dir_path: str):
    with pytest.raises(ValueError):
        AgentPluginBuildOptions(
            plugin_dir_path=Path(plugin_dir_path),
            build_dir_path=Path(BUILD_DIR),
            dist_dir_path=Path(DIST_DIR),
            source_dir_name=SOURCE_DIR_NAME,
            platform_dependencies=PlatformDependencyPackagingMethod.COMMON,
            verify_hashes=VERIFY_HASHES,
        )


@pytest.mark.parametrize(
    "platform_dependencies",
    [
        "",
        None,
        "invalid",
        "123123",
        "COMMON",
        "AUTODETECT",
        "../etc/passwd",
    ],
)
def test_agent_plugin_builder_options__platform_dependencies__invalid(
    platform_dependencies: str | None,
):
    with pytest.raises(ValueError):
        AgentPluginBuildOptions(
            plugin_dir_path=Path(PLUGIN_DIR),
            build_dir_path=Path(BUILD_DIR),
            dist_dir_path=Path(DIST_DIR),
            source_dir_name=SOURCE_DIR_NAME,
            platform_dependencies=platform_dependencies,
            verify_hashes=VERIFY_HASHES,
        )


def test_parse_agent_plugin_builder_options():
    assert (
        parse_agent_plugin_build_options(AGENT_PLUGIN_BUILD_OPTIONS_NAMESPACE)
        == AGENT_PLUGIN_BUILD_OPTIONS_OBJECT
    )


def test_parse_agent_plugin_builder_options__invalid():
    with pytest.raises(ValueError):
        parse_agent_plugin_build_options(INVALID_AGENT_PLUGIN_BUILD_OPTIONS_NAMESPACE)
