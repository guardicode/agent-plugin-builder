from pathlib import Path
from typing import Iterable, Sequence

import pytest


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