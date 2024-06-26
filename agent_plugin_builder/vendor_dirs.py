import logging
from pathlib import Path
from shlex import quote
from typing import Final

from monkeytypes import OperatingSystem

import docker

from .compare_package_lists import all_equal, load_package_names

logger = logging.getLogger(__name__)


AGENT_PLUGIN_IMAGE: Final = "infectionmonkey/agent-builder:latest"
PLUGIN_BUILDER_IMAGE: Final = "infectionmonkey/plugin-builder:latest"
LINUX_IMAGE_PYENV_INIT_COMMANDS: Final = [
    'export PYENV_ROOT="$HOME/.pyenv"',
    'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"',
    'eval "$(pyenv init -)"',
]
LINUX_BUILD_PACKAGE_LIST_COMMANDS: Final = " && ".join(
    [
        *LINUX_IMAGE_PYENV_INIT_COMMANDS,
        "cd /plugin",
        "pip install --dry-run -r requirements.txt --report linux.json",
        "chown {uid}:{gid} /plugin/linux.json",
    ]
)
LINUX_BUILD_VENDOR_DIR_COMMANDS: Final = " && ".join(
    [
        *LINUX_IMAGE_PYENV_INIT_COMMANDS,
        "cd /plugin",
        "pip install -r requirements.txt -t src/{vendor_dir}",
        "chown -R {uid}:{gid} /plugin/src/{vendor_dir}",
    ]
)
WINDOWS_IMAGE_INIT_COMMAND: Final = ". /opt/mkuserwineprefix"
WINDOWS_BUILD_PACKAGE_LIST_COMMANDS: Final = " && ".join(
    [
        WINDOWS_IMAGE_INIT_COMMAND,
        "cd /plugin",
        "wine pip install --dry-run -r requirements.txt --report windows.json",
        "chown {uid}:{gid} /plugin/windows.json",
    ]
)
WINDOWS_BUILD_VENDOR_DIR_COMMANDS: Final = " && ".join(
    [
        WINDOWS_IMAGE_INIT_COMMAND,
        "cd /plugin",
        "wine pip install -r requirements.txt -t src/vendor-windows",
        "chown -R {uid}:{gid} /plugin/src/vendor-windows",
    ]
)


def check_if_common_vendor_dir_possible(build_dir: Path, uid: int, gid: int) -> bool:
    """
    Check if a common vendor directory is possible by comparing the package lists generated
    from a dry run of the requirements installation on Linux and Windows.

    :param build_dir: Path to the build directory.
    :param uid: User ID to set on the vendor directory.
    :param gid: Group ID to set on the vendor directory.
    """
    generate_requirements_file(build_dir)

    client = docker.from_env()

    linux_container = client.containers.run(
        AGENT_PLUGIN_IMAGE,
        command=_build_bash_command(
            LINUX_BUILD_PACKAGE_LIST_COMMANDS.format(uid=quote(str(uid)), gid=quote(str(gid)))
        ),
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )
    logger.debug(f"Linux container logs: {linux_container}")
    _log_container_output(linux_container, "Linux Dry Run requirements, ")

    windows_container = client.containers.run(
        PLUGIN_BUILDER_IMAGE,
        command=_build_bash_command(
            WINDOWS_BUILD_PACKAGE_LIST_COMMANDS.format(uid=quote(str(uid)), gid=quote(str(gid)))
        ),
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )
    _log_container_output(windows_container, "Windows Dry Run requirements, ")

    linux_packages_path = build_dir / "linux.json"
    windows_packages_path = build_dir / "windows.json"

    linux_packages = load_package_names(linux_packages_path)
    windows_packages = load_package_names(windows_packages_path)

    linux_packages_path.unlink()
    windows_packages_path.unlink()

    response = all_equal([linux_packages, windows_packages])
    if response:
        logger.info("Common vendor directory is possible")
    else:
        logger.info("Common vendor directory is not possible")

    return response


def _build_bash_command(command: str) -> str:
    return f"/bin/bash -c {quote(command)}"


def generate_common_vendor_dir(build_dir: Path, uid: int, gid: int):
    """
    Generate a common vendor directory by installing the requirements in a Linux container.

    :param build_dir: Path to the build directory.
    :param uid: User ID to set on the vendor directory.
    :param gid: Group ID to set on the vendor directory.
    """
    client = docker.from_env()

    linux_container = client.containers.run(
        AGENT_PLUGIN_IMAGE,
        command=_build_bash_command(
            LINUX_BUILD_VENDOR_DIR_COMMANDS.format(
                uid=quote(str(uid)), gid=quote(str(gid)), vendor_dir=quote("vendor")
            )
        ),
        volumes={str(build_dir): {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )
    _log_container_output(linux_container, "Common vendor directory, ")


def generate_vendor_dirs(build_dir: Path, operating_system: OperatingSystem, uid: int, gid: int):
    """
    Generate the vendor directories for the plugin.

    :param build_dir: Path to the build directory.
    :param operating_system: Operating system to generate the vendor directories for.
    :param uid: User ID to set on the vendor directory.
    :param gid: Group ID to set on the vendor directory.
    """
    if operating_system == OperatingSystem.LINUX:
        generate_linux_vendor_dir(build_dir, uid, gid)
    elif operating_system == OperatingSystem.WINDOWS:
        generate_windows_vendor_dir(build_dir, uid, gid)


def generate_linux_vendor_dir(build_dir: Path, uid: int, gid: int):
    """
    Generate the Linux vendor directory by installing the requirements in a Linux container.

    :param build_dir: Path to the build directory.
    :param uid: User ID to set on the vendor directory.
    :param gid: Group ID to set on the vendor directory.
    """
    client = docker.from_env()
    linux_container = client.containers.run(
        AGENT_PLUGIN_IMAGE,
        command=_build_bash_command(
            LINUX_BUILD_VENDOR_DIR_COMMANDS.format(
                uid=quote(str(uid)), gid=quote(str(gid)), vendor_dir=quote("vendor-linux")
            )
        ),
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )
    _log_container_output(linux_container, "Linux vendor directory, ")


def generate_windows_vendor_dir(build_dir: Path, uid: int, gid: int):
    """
    Generate the Windows vendor directory by installing the requirements in a Linux Container
    with Wine installed.

    :param build_dir: Path to the build directory.
    :param uid: User ID to set on the vendor directory.
    :param gid: Group ID to set on the vendor directory.
    """
    client = docker.from_env()

    windows_container = client.containers.run(
        PLUGIN_BUILDER_IMAGE,
        command=_build_bash_command(
            WINDOWS_BUILD_VENDOR_DIR_COMMANDS.format(uid=quote(str(uid)), gid=quote(str(gid)))
        ),
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )
    _log_container_output(windows_container, "Windows vendor directory, ")


def _log_container_output(container_logs: bytes, prefix: str = ""):
    logger.debug(f"{prefix}Container logs: {container_logs.decode('utf-8')}")


def generate_requirements_file(build_dir: Path):
    """
    Generate the requirements file from the lock file depending on the lock file present.

    :param build_dir: Path to the build directory.
    """
    import subprocess

    logger.info("Generating requirements file")
    if (build_dir / "poetry.lock").exists():
        command = ["poetry", "export", "-f", "requirements.txt", "-o", "requirements.txt"]
        process = subprocess.Popen(
            command, cwd=str(build_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        with process.stdout as stdout:  # type: ignore [union-attr]
            for line in iter(stdout.readline, b""):
                logger.debug(line)

        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)
    elif (build_dir / "Pipfile.lock").exists():
        command = ["pipenv", "requirements"]
        with (build_dir / "requirements.txt").open("w") as f:
            process = subprocess.Popen(
                command, cwd=str(build_dir), stdout=f, stderr=subprocess.PIPE
            )
            with process.stderr as stderr:  # type: ignore [union-attr]
                for line in iter(stderr.readline, b""):
                    logger.debug(line)

        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

    if (build_dir / "requirements.txt").exists():
        logger.info("Requirements file generated")
