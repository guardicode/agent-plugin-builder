import logging
from pathlib import Path

import pytest

import agent_plugin_builder.setup_build_plugin_logging as agent_plugin_builder_logger


@pytest.fixture(autouse=True)
def reset_logger():
    yield

    agent_plugin_builder_logger.reset_logger()


@pytest.mark.parametrize(
    "log_level, test_string",
    [
        (-1, "SomeString"),
        (0, "critical"),
        (3, "info"),
        (4, "debug"),
        (5, "SomeOtherString"),
    ],
)
def test_setup_build_plugin_logging_file_log_default_level(tmpdir, log_level, test_string):
    DATA_DIR = Path(tmpdir)
    LOG_FILE = DATA_DIR / agent_plugin_builder_logger.AGENT_PLUGIN_BUILDER_LOG_FILENAME
    TEST_STRING = f"Build plugin logging test (File; Log level: {test_string})"

    agent_plugin_builder_logger.setup_logging(log_level)
    agent_plugin_builder_logger.add_file_handler(DATA_DIR)

    logger = logging.getLogger("TestLogger")
    logger.debug(TEST_STRING)

    assert LOG_FILE.is_file()
    with open(LOG_FILE, "r") as f:
        line = f.readline()
        assert TEST_STRING in line  # File Log level is always debug


def test_setup_build_plugin_logging_console_log_level_debug(capsys, tmpdir):
    LOG_LEVEL = 4
    TEST_STRING = "Build plugin logging test (Console; Log level: debug)"

    agent_plugin_builder_logger.setup_logging(LOG_LEVEL)

    logger = logging.getLogger("TestLogger")
    logger.debug(TEST_STRING)

    captured = capsys.readouterr()
    assert TEST_STRING in captured.out


@pytest.mark.parametrize("log_level", [-1, 3, 7])
def test_setup_build_plugin_logging_console_log_default_level(capsys, tmpdir, log_level):
    TEST_STRING = "Build plugin logging test (Console; Log level: debug)"

    agent_plugin_builder_logger.setup_logging(log_level)

    logger = logging.getLogger("TestLogger")
    logger.debug(TEST_STRING)

    captured = capsys.readouterr()
    # Console log level for out of logging scope level occurrences is always info
    # E.x. -vvvvvvvv argument
    assert TEST_STRING not in captured.out
