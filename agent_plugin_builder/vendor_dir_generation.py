import json
import logging
from os import getgid, getuid
from pathlib import Path
from shlex import quote
from typing import Final, Sequence

from monkeytypes import AgentPluginManifest, OperatingSystem

import docker

from .agent_plugin_build_options import AgentPluginBuildOptions, SourceDirName
from .platform_dependency_packaging_method import PlatformDependencyPackagingMethod

logger = logging.getLogger(__name__)


class CommandRunError(Exception):
    """Raised when a command fails to run."""

    pass


LINUX_PLUGIN_BUILDER_IMAGE: Final = "infectionmonkey/agent-builder:latest"
WINDOWS_PLUGIN_BUILDER_IMAGE: Final = "infectionmonkey/plugin-builder:latest"
LINUX_PACKAGE_LIST_FILE: Final = "linux_packages.json"
WINDOWS_PACKAGE_LIST_FILE: Final = "windows_packages.json"
LINUX_VENV_COMMANDS: Final = [
    'export PIP_CACHE_DIR="$(mktemp -d)"',
    'export VENV_DIR="$(mktemp -d)"',
    "python --version",
    'python -m venv "$VENV_DIR"',
    'source "$VENV_DIR/bin/activate"',
]
LINUX_BUILD_PACKAGE_LIST_COMMANDS: Final = " && ".join(
    [
        *LINUX_VENV_COMMANDS,
        "cd /plugin",
        "pip install --dry-run -r requirements.txt --report {filename}",
    ]
)
LINUX_BUILD_VENDOR_DIR_COMMANDS: Final = " && ".join(
    [
        *LINUX_VENV_COMMANDS,
        "cd /plugin",
        "pip install -r requirements.txt -t {vendor_path}",
    ]
)
WINDOWS_IMAGE_INIT_COMMAND: Final = ". /opt/mkuserwineprefix"
WINDOWS_BUILD_PACKAGE_LIST_COMMANDS: Final = " && ".join(
    [
        WINDOWS_IMAGE_INIT_COMMAND,
        "cd /plugin",
        "wine pip install --dry-run -r requirements.txt --report {filename}",
    ]
)
WINDOWS_BUILD_VENDOR_DIR_COMMANDS: Final = " && ".join(
    [
        WINDOWS_IMAGE_INIT_COMMAND,
        "cd /plugin",
        "wine pip install -r requirements.txt -t {source_dir_name}/vendor-windows",
    ]
)


def generate_vendor_directories(
    agent_plugin_build_options: AgentPluginBuildOptions,
    agent_plugin_manifest: AgentPluginManifest,
):
    """
    Generate the vendor directories for the plugin.

    If the plugin supports multiple operating systems and the dependency_method is AUTODETECT, the
    function will try to generate a common vendor directory. If a common vendor directory is not
    possible, it will generate separate vendor directories for each supported operating system.

    :param agent_plugin_build_options: Agent Plugin build options.
    :param agent_plugin_manifest: Agent Plugin manifest.
    """
    logger.info(
        f"Generating vendor directories for plugin: {agent_plugin_manifest.name}, "
        f"dependency_method: {agent_plugin_build_options.platform_dependencies}"
    )
    generate_requirements_file(
        agent_plugin_build_options.build_dir_path, agent_plugin_build_options.verify_hashes
    )
    if agent_plugin_build_options.platform_dependencies == PlatformDependencyPackagingMethod.COMMON:
        generate_common_vendor_dir(
            agent_plugin_build_options.build_dir_path, agent_plugin_build_options.source_dir_name
        )
    elif (
        agent_plugin_build_options.platform_dependencies
        == PlatformDependencyPackagingMethod.SEPARATE
    ):
        for os_type in agent_plugin_manifest.supported_operating_systems:
            generate_vendor_dirs(
                agent_plugin_build_options.build_dir_path,
                agent_plugin_build_options.source_dir_name,
                os_type,
            )
    else:
        if len(agent_plugin_manifest.supported_operating_systems) > 1:
            common_dir_possible = should_use_common_vendor_dir(
                agent_plugin_build_options.build_dir_path
            )
            if common_dir_possible:
                generate_common_vendor_dir(
                    agent_plugin_build_options.build_dir_path,
                    agent_plugin_build_options.source_dir_name,
                )
            else:
                for os_type in agent_plugin_manifest.supported_operating_systems:
                    generate_vendor_dirs(
                        agent_plugin_build_options.build_dir_path,
                        agent_plugin_build_options.source_dir_name,
                        os_type,
                    )


def should_use_common_vendor_dir(build_dir_path: Path) -> bool:
    """
    Check if a common vendor directory is possible by comparing the package lists generated
    from a dry run of the requirements installation on Linux and Windows.

    :param build_dir_path: Path to the build directory.
    :return: True if a common vendor directory is possible, False otherwise.
    :raises FileNotFoundError: If the requirements file is not found.
    """
    if not (build_dir_path / "requirements.txt").exists():
        raise FileNotFoundError("requirements.txt not found in the build directory")

    command = _build_bash_command(
        LINUX_BUILD_PACKAGE_LIST_COMMANDS.format(filename=quote(LINUX_PACKAGE_LIST_FILE))
    )
    output = _run_command_in_docker_container(LINUX_PLUGIN_BUILDER_IMAGE, command, build_dir_path)
    _log_container_output(output, "Linux Requirements")

    command = _build_bash_command(
        WINDOWS_BUILD_PACKAGE_LIST_COMMANDS.format(filename=quote(WINDOWS_PACKAGE_LIST_FILE))
    )
    output = _run_command_in_docker_container(WINDOWS_PLUGIN_BUILDER_IMAGE, command, build_dir_path)
    _log_container_output(output, "Windows Requirements")

    linux_packages = _load_package_names(build_dir_path / LINUX_PACKAGE_LIST_FILE)
    windows_packages = _load_package_names(build_dir_path / WINDOWS_PACKAGE_LIST_FILE)

    response = linux_packages == windows_packages
    if response:
        logger.info("Common vendor directory is possible")
    else:
        logger.info("Common vendor directory is not possible")

    return response


def _load_package_names(file_path: Path) -> set[str]:
    """
    Load the Plugin's packages names from a pip installation report file.

    :param file_path: Path to the report file.
    :return: Set of package names.
    """
    with file_path.open("r") as f:
        packages_dict = json.load(f)
        return {p["download_info"]["url"].split("/")[-1] for p in packages_dict["install"]}


def _build_bash_command(command: str) -> str:
    return f"/bin/bash -l -c {quote(command)}"


def _run_command_in_docker_container(image: str, command: str, plugin_dir_path: Path) -> bytes:
    """
    Run a container with the plugin directory mounted.

    :param image: Docker image to run.
    :param command: Command to run in the container.
    :param plugin_dir_path: Path to the plugin directory.
    :return: Output of the container.
    """
    client = docker.from_env()  # type: ignore [attr-defined]
    volumes = {str(plugin_dir_path): {"bind": "/plugin", "mode": "rw"}}

    uid = getuid()
    gid = getgid()

    return client.containers.run(
        image, command=command, volumes=volumes, remove=True, user=f"{uid}:{gid}"
    )


def generate_vendor_dirs(
    build_dir_path: Path, source_dir_name: SourceDirName, operating_system: OperatingSystem
):
    """
    Generate the vendor directories for the plugin.

    :param build_dir_path: Path to the build directory.
    :param source_dir_name: Name of the source directory.
    :param operating_system: Operating system to generate the vendor directories for.
    """
    if operating_system == OperatingSystem.LINUX:
        generate_common_vendor_dir(build_dir_path, source_dir_name, "vendor-linux")
    elif operating_system == OperatingSystem.WINDOWS:
        generate_windows_vendor_dir(build_dir_path, source_dir_name)
    else:
        raise ValueError(f"Unsupported operating system: {operating_system}")


def generate_common_vendor_dir(
    build_dir_path: Path, source_dir_name: SourceDirName, vendor_dir_name: str = "vendor"
):
    """
    Generate a common vendor directory by installing the requirements in a Linux container.

    :param build_dir_path: Path to the build directory.
    :param source_dir_name: Name of the source directory.
    :param vendor_dir_name: Name of the vendor directory.
    """
    command = _build_bash_command(
        LINUX_BUILD_VENDOR_DIR_COMMANDS.format(
            vendor_path=quote(f"{source_dir_name}/{vendor_dir_name}"),
        )
    )
    output = _run_command_in_docker_container(LINUX_PLUGIN_BUILDER_IMAGE, command, build_dir_path)
    _log_container_output(output, "Common Vendor Directory")


def generate_windows_vendor_dir(build_dir_path: Path, source_dir_name: SourceDirName):
    """
    Generate the Windows vendor directory by installing the requirements in a Linux Container
    with Wine installed.

    :param build_dir_path: Path to the build directory.
    """
    command = _build_bash_command(
        WINDOWS_BUILD_VENDOR_DIR_COMMANDS.format(source_dir_name=quote(source_dir_name))
    )
    output = _run_command_in_docker_container(WINDOWS_PLUGIN_BUILDER_IMAGE, command, build_dir_path)
    _log_container_output(output, "Windows Vendor Directory")


def _log_container_output(container_logs: bytes, prefix: str = ""):
    logger.debug(f"{prefix} Container logs: {container_logs.decode('utf-8')}")


def generate_requirements_file(build_dir_path: Path, verify_hashes: bool = True):
    """
    Generate the requirements file from the lock file depending on the lock file present.

    :param build_dir_path: Path to the build directory.
    :param verify_hashes: Verify plugin's dependency hashes.
    :raises FileNotFoundError: If the lock or requierements file is not found.
    :raises CommandRunError: If the command fails to run.
    """
    logger.info("Generating requirements file")
    if (build_dir_path / "poetry.lock").exists():
        command = [
            "poetry",
            "export",
            "-f",
            "requirements.txt",
            "-o",
            "requirements.txt",
        ]
        if not verify_hashes:
            logger.warning(
                "WARNING: Plugins dependencies are not going to be verified. "
                "This can allow supply-chain attacks to go unnoticed. A malicious actor "
                "could slip bad code into the installation via one of unverified dependencies.",
            )
            command.append("--without-hashes")

        return_code = _run_command(build_dir_path, command)
        if return_code != 0:
            logger.error("Requirements file generation failed")
            raise CommandRunError("Requirements file generation failed")
    else:
        logger.warning("Poetry lock file not found")
        raise FileNotFoundError("poetry.lock not found")

    if (build_dir_path / "requirements.txt").exists():
        logger.info("Requirements file generated")
    else:
        logger.error("Requirements file not generated")
        raise FileNotFoundError("requirements.txt not found in the build directory")


def _run_command(build_dir_path: Path, command: Sequence[str]):
    """
    Run a command in the shell.

    :param build_dir_path: Path to the build directory.
    :param command: Command to run.
    """
    import subprocess

    logger.debug(f"Running command: {' '.join(command)}")
    process = subprocess.Popen(
        command, cwd=str(build_dir_path), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    with process.stdout as stdout:  # type: ignore [union-attr]
        for line in iter(stdout.readline, b""):
            logger.debug(line.decode("utf-8").strip())

    return process.wait()
