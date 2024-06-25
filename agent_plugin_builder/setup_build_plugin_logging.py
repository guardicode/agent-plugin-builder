import logging
import logging.handlers
import sys
from pathlib import Path

AGENT_PLUGIN_BUILDER_LOG_FILENAME = "agent_plugin_builder.log"
CONSOLE_FORMAT = "%(asctime)s - %(message)s"
FILE_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s"
FILE_MAX_BYTES = 10485760
FILE_ENCODING = "utf8"
FILE_BACKUP_COUNT = 10
LOG_LEVELS = {
    0: logging.CRITICAL,
    1: logging.ERROR,
    2: logging.WARN,
    3: logging.INFO,
    4: logging.DEBUG,
}


def setup_logging(data_dir: Path, verbosity: int):
    """
    Set up the logger

    :param data_dir: The data directory
    :param log_level: A number representing log levels. If lower than 0 or higher than 4,
                      it will be set to logging.INFO, else it will be set to the
                      corresponding log level.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    log_file_path = _get_log_file_path(data_dir)

    _add_file_handler(logger, logging.Formatter(FILE_FORMAT), log_file_path)

    _add_console_handler(logger, logging.Formatter(CONSOLE_FORMAT), verbosity)


def _get_log_file_path(data_dir: Path) -> Path:
    return data_dir / AGENT_PLUGIN_BUILDER_LOG_FILENAME


def _add_file_handler(logger: logging.Logger, formatter: logging.Formatter, file_path: Path):
    fh = logging.handlers.RotatingFileHandler(
        file_path, maxBytes=FILE_MAX_BYTES, backupCount=FILE_BACKUP_COUNT, encoding=FILE_ENCODING
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(fh)


def _add_console_handler(logger: logging.Logger, formatter: logging.Formatter, verbosity: int):
    ch = logging.StreamHandler(stream=sys.stdout)

    if verbosity < 0 or verbosity > 5:
        log_level = logging.INFO
    else:
        log_level = LOG_LEVELS[min(verbosity, max(LOG_LEVELS.keys()))]
    ch.setLevel(log_level)

    ch.setFormatter(formatter)

    logger.addHandler(ch)


def reset_logger():
    logger = logging.getLogger()

    for handler in logger.handlers:
        logger.removeHandler(handler)
