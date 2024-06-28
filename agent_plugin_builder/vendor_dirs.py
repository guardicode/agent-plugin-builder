import json
import logging
from pathlib import Path
from shlex import quote
from typing import Final

from monkeytypes import OperatingSystem

import docker

logger = logging.getLogger(__name__)


LINUX_PLUGIN_BUILDER_IMAGE: Final = "infectionmonkey/agent-builder:latest"
WINDOWS_PLUGIN_BUILDER_IMAGE: Final = "infectionmonkey/plugin-builder:latest"
LINUX_PACKAGE_LIST_FILE: Final = "linux_packages.json"
WINDOWS_PACKAGE_LIST_FILE: Final = "windows_packages.json"
LINUX_IMAGE_PYENV_INIT_COMMANDS: Final = [
    'export PYENV_ROOT="$HOME/.pyenv"',
    'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"',
    'eval "$(pyenv init -)"',
]
LINUX_BUILD_PACKAGE_LIST_COMMANDS: Final = " && ".join(
    [
        *LINUX_IMAGE_PYENV_INIT_COMMANDS,
        "cd /plugin",
        "pip install --dry-run -r requirements.txt --report {filename}",
        "chown {uid}:{gid} /plugin/{filename}",
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
        "wine pip install --dry-run -r requirements.txt --report {filename}",
        "chown {uid}:{gid} /plugin/{filename}",
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
    :return: True if a common vendor directory is possible, False otherwise.
    """
    generate_requirements_file(build_dir)

    command = _build_bash_command(
        LINUX_BUILD_PACKAGE_LIST_COMMANDS.format(
            uid=quote(str(uid)), gid=quote(str(gid)), filename=quote(LINUX_PACKAGE_LIST_FILE)
        )
    )
    output = _run_container_with_plugin_dir(LINUX_PLUGIN_BUILDER_IMAGE, command, build_dir)
    _log_container_output(output, "Linux Requirements")

    command = _build_bash_command(
        WINDOWS_BUILD_PACKAGE_LIST_COMMANDS.format(
            uid=quote(str(uid)), gid=quote(str(gid)), filename=quote(WINDOWS_PACKAGE_LIST_FILE)
        )
    )
    output = _run_container_with_plugin_dir(WINDOWS_PLUGIN_BUILDER_IMAGE, command, build_dir)
    _log_container_output(output, "Windows Requirements")

    linux_packages = load_package_names(build_dir / LINUX_PACKAGE_LIST_FILE)
    windows_packages = load_package_names(build_dir / WINDOWS_PACKAGE_LIST_FILE)

    response = linux_packages == windows_packages
    if response:
        logger.info("Common vendor directory is possible")
    else:
        logger.info("Common vendor directory is not possible")

    return response


def load_package_names(file_path: Path) -> set[str]:
    """
    Load the package names from a pip installation report file.

    :param file_path: Path to the report file.
    :return: Set of package names.
    """
    with file_path.open("r") as f:
        packages_dict = json.load(f)
        return {p["download_info"]["url"].split("/")[-1] for p in packages_dict["install"]}


def _build_bash_command(command: str) -> str:
    return f"/bin/bash -c {quote(command)}"


def _run_container_with_plugin_dir(image: str, command: str, plugin_dir: Path) -> bytes:
    """
    Run a container with the plugin directory mounted.

    :param image: Docker image to run.
    :param command: Command to run in the container.
    :param plugin_dir: Path to the plugin directory.
    :return: Output of the container.
    """

    client = docker.from_env()  # type: ignore [attr-defined]
    volumes = {str(plugin_dir): {"bind": "/plugin", "mode": "rw"}}
    return client.containers.run(image, command=command, volumes=volumes, remove=True)


def generate_common_vendor_dir(build_dir: Path, uid: int, gid: int):
    """
    Generate a common vendor directory by installing the requirements in a Linux container.

    :param build_dir: Path to the build directory.
    :param uid: User ID to set on the vendor directory.
    :param gid: Group ID to set on the vendor directory.
    """
    command = _build_bash_command(
        LINUX_BUILD_VENDOR_DIR_COMMANDS.format(
            uid=quote(str(uid)), gid=quote(str(gid)), vendor_dir=quote("vendor")
        )
    )
    output = _run_container_with_plugin_dir(LINUX_PLUGIN_BUILDER_IMAGE, command, build_dir)
    _log_container_output(output, "Common Vendor Directory")


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
    command = _build_bash_command(
        LINUX_BUILD_VENDOR_DIR_COMMANDS.format(
            uid=quote(str(uid)), gid=quote(str(gid)), vendor_dir=quote("vendor-linux")
        )
    )
    output = _run_container_with_plugin_dir(LINUX_PLUGIN_BUILDER_IMAGE, command, build_dir)
    _log_container_output(output, "Linux Vendor directory")


def generate_windows_vendor_dir(build_dir: Path, uid: int, gid: int):
    """
    Generate the Windows vendor directory by installing the requirements in a Linux Container
    with Wine installed.

    :param build_dir: Path to the build directory.
    :param uid: User ID to set on the vendor directory.
    :param gid: Group ID to set on the vendor directory.
    """
    command = _build_bash_command(
        WINDOWS_BUILD_VENDOR_DIR_COMMANDS.format(uid=quote(str(uid)), gid=quote(str(gid)))
    )
    output = _run_container_with_plugin_dir(WINDOWS_PLUGIN_BUILDER_IMAGE, command, build_dir)
    _log_container_output(output, "Windows Vendor Directory")


def _log_container_output(container_logs: bytes, prefix: str = ""):
    logger.debug(f"{prefix} Container logs: {container_logs.decode('utf-8')}")


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

    if (build_dir / "requirements.txt").exists():
        logger.info("Requirements file generated")
