from argparse import ArgumentDefaultsHelpFormatter, BooleanOptionalAction, RawTextHelpFormatter
from pathlib import Path
from typing import Any

from .build_options import BUILD, DIST, PlatformDependencyPackagingMethod

SOURCE_DIR_METAVAR = "SOURCE_DIR"
PLATFORM_DEPENDENCIES_METAVAR = "PLATFORM_DEPENDENCIES"
HASHES_METAVAR = "HASHES"
VERBOSITY_DEST = "verbosity"


class CustomArgumentsFormatter(ArgumentDefaultsHelpFormatter, RawTextHelpFormatter):
    def _get_help_string(self, action):
        help_str = action.help or ""
        default = action.default

        # Custom replacements based on metavar
        if action.metavar == SOURCE_DIR_METAVAR:
            default_str = "<plugin_name>_<plugin_type>: Ex. ssh_exploiter"
            help_str += "(Default: <plugin_name>_<plugin_type>: Ex. ssh_exploiter)"
        elif action.metavar == PLATFORM_DEPENDENCIES_METAVAR:
            default_str = action.default.value
        elif action.metavar == HASHES_METAVAR:
            default_str = "Verify dependencies integrity"
        else:
            if action.dest == VERBOSITY_DEST:
                default_str = "INFO"
            else:
                default_str = default

        if "%(default)" not in help_str and default is not None:
            if action.dest != "help":
                help_str += "(Default: %(default)s)"

        return help_str % dict(default=default_str)


ARGUMENTS: list[dict[str, Any]] = [
    {
        "name": ["plugin_path"],
        "kwargs": {
            "metavar": "PLUGIN_PATH",
            "type": Path,
            "help": "Path to the plugin",
        },
    },
    {
        "name": ["-b", "--build-dir-path"],
        "kwargs": {
            "metavar": "BUILD_DIR_PATH",
            "type": Path,
            "default": (Path.cwd() / BUILD),
            "help": "Optional path to the build directory.\n",
        },
    },
    {
        "name": ["-d", "--dist-dir-path"],
        "kwargs": {
            "metavar": "DIST_DIR_PATH",
            "type": Path,
            "default": (Path.cwd() / DIST),
            "help": "Optional path to the dist directory.\n",
        },
    },
    {
        "name": ["-s", "--source-dir"],
        "kwargs": {
            "metavar": SOURCE_DIR_METAVAR,
            "type": str,
            "default": None,
            "help": "Optional name of the source directory.\n",
        },
    },
    {
        "name": ["-pd", "--platform-dependencies"],
        "kwargs": {
            "metavar": PLATFORM_DEPENDENCIES_METAVAR,
            "type": PlatformDependencyPackagingMethod,
            "default": PlatformDependencyPackagingMethod.AUTODETECT,
            "help": """Since plugin dependencies must be vendored, this setting determines how
the plugin builder should package dependencies for its supported platforms.

Options:
    common: All dependencies are packaged once, and shared across all platforms. This
            should only be used if all dependencies are known to be platform-independent.
    separate: Some or all dependencies are platform-dependent, and are therefore packaged
            separately for each supported platform. This is the most reliable option,
            however, it results in a larger plugin file, since dependencies are
            duplicated for each platform.
    autodetect: The plugin builder will attempt to detect the best method to use.
""",
        },
    },
    {
        "name": ["--verify"],
        "kwargs": {
            "metavar": HASHES_METAVAR,
            "action": BooleanOptionalAction,
            "help": """Some plugins may have dependencies for which we can"t verify the hashes.

Options:
    --verify: will include hashes to verify the integrity of the plugin dependencies
    --no-verify: will exclude hashes which will not verify the integrity of the plugin
    dependencies. This is not a recommended option for security reasons.
""",
            "default": True,
        },
    },
    {
        "name": ["-v", "--verbose"],
        "kwargs": {
            "dest": VERBOSITY_DEST,
            "action": "count",
            "default": -1,
            "help": """Verbosity (between 1-5 occurrences with more leading to
more verbose logging).

Logging levels with occurrences:
    CRITICAL=1
    ERROR=2
    WARN=3
    INFO=4
    DEBUG=5
""",
        },
    },
]
