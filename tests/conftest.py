from pathlib import Path
from typing import Iterable, Sequence

import pytest
from monkeytypes import AgentPluginManifest, AgentPluginType, OperatingSystem

from agent_plugin_builder import AgentPluginBuildOptions, PlatformDependencyPackagingMethod
from agent_plugin_builder.agent_plugin_build_options import BUILD, DIST


def pytest_addoption(parser):
    parser.addoption(
        "--skip-integration",
        action="store_true",
        default=False,
        help="Skip integration tests that require a docker environment.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: Mark that a test is an integration tests. These tests require docker.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: Sequence[pytest.Function]):
    if config.getoption("--skip-integration"):
        _mark_skipped_integration(items)


def _mark_skipped_integration(items: Iterable[pytest.Function]):
    skip_integration = pytest.mark.skip(reason="Skipped because --skip-integration was set")
    _mark_skipped_tests("integration", skip_integration, items)


def _mark_skipped_tests(
    keyword: str, marker: pytest.MarkDecorator, items: Iterable[pytest.Function]
):
    for item in items:
        if keyword in item.keywords:
            item.add_marker(marker)


@pytest.fixture(scope="session")
def data_for_tests_dir(pytestconfig):
    return Path(pytestconfig.rootdir) / "tests" / "data_for_tests"


@pytest.fixture
def agent_plugin_manifest():
    return AgentPluginManifest(
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


@pytest.fixture
def agent_plugin_build_options(tmpdir) -> AgentPluginBuildOptions:
    plugin_dir_name = "plugin-dir"
    plugin_dir_path = Path(tmpdir / plugin_dir_name)
    plugin_dir_path.mkdir()
    source_dir_name = "source_dir_name"
    (plugin_dir_path / BUILD).mkdir()
    (plugin_dir_path / DIST).mkdir()

    return AgentPluginBuildOptions(
        plugin_dir_path=plugin_dir_path,
        build_dir_path=(plugin_dir_path / BUILD),
        dist_dir_path=(plugin_dir_path / DIST),
        source_dir_name=source_dir_name,
        platform_dependencies=PlatformDependencyPackagingMethod.AUTODETECT,
        verify_hashes=False,
    )
