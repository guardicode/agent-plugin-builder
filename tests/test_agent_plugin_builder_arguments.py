from unittest.mock import MagicMock

import pytest

from agent_plugin_builder.agent_plugin_builder_arguments import (
    HASHES_METAVAR,
    PLATFORM_DEPENDENCIES_METAVAR,
    SOURCE_DIR_METAVAR,
    VERBOSITY_DEST,
    CustomArgumentsFormatter,
)


@pytest.fixture
def formatter() -> CustomArgumentsFormatter:
    return CustomArgumentsFormatter(prog="test")


def test_get_help_string_source_dir(formatter: CustomArgumentsFormatter):
    action = MagicMock()
    action.help = "source directory"
    action.default = None
    action.metavar = SOURCE_DIR_METAVAR

    expected_help_str = "source directory(Default: <plugin_name>_<plugin_type>: Ex. ssh_exploiter)"
    assert formatter._get_help_string(action) == expected_help_str


def test_get_help_string_platform_dependencies(formatter: CustomArgumentsFormatter):
    action = MagicMock()
    action.help = "platform dependencies"
    action.default = MagicMock(value="default_value")
    action.metavar = PLATFORM_DEPENDENCIES_METAVAR

    expected_help_str = "platform dependencies(Default: default_value)"
    assert formatter._get_help_string(action) == expected_help_str


def test_get_help_string_hashes(formatter: CustomArgumentsFormatter):
    action = MagicMock()
    action.help = "hashes"
    action.default = True
    action.metavar = HASHES_METAVAR

    expected_help_str = "hashes(Default: Verify dependencies integrity)"
    assert formatter._get_help_string(action) == expected_help_str


def test_get_help_string_verbosity(formatter: CustomArgumentsFormatter):
    action = MagicMock()
    action.help = "verbosity level"
    action.default = -1
    action.metavar = None
    action.dest = VERBOSITY_DEST

    expected_help_str = "verbosity level(Default: INFO)"
    assert formatter._get_help_string(action) == expected_help_str


def test_get_help_string_default(formatter: CustomArgumentsFormatter):
    action = MagicMock()
    action.help = "some argument"
    action.default = "default_value"
    action.metavar = None
    action.dest = "some_argument"

    expected_help_str = "some argument(Default: default_value)"
    assert formatter._get_help_string(action) == expected_help_str
