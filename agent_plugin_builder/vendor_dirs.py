from pathlib import Path

import subprocess
import docker

from monkeytypes import OperatingSystem

from .compare_package_lists import all_equal, load_package_names

AGENT_PLUGIN_IMAGE = "infectionmonkey/agent-builder:latest"
PLUGIN_BUILDER_IMAGE = "infectionmonkey/plugin-builder:latest"
LINUX_IMAGE_PYENV_INIT_COMMANDS = [
    'export PYENV_ROOT="$HOME/.pyenv"',
    'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"',
    'eval "$(pyenv init -)"',
]


def check_if_common_vendor_dir_possible(build_dir: Path, uid, gid) -> bool:
    requirements_file = build_dir / "requirements.txt"
    command = ["pipenv", "requirements"]
    with requirements_file.open("w") as f:
        subprocess.check_call(command, cwd=str(build_dir), stdout=f)

    client = docker.from_env()
    linux_commands = [
        'export PYENV_ROOT="$HOME/.pyenv"',
        'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"',
        'eval "$(pyenv init -)"',
        "cd /plugin && pip install --dry-run -r requirements.txt --report linux.json",
        f"chown -R {uid}:{gid} /plugin/linux.json",
    ]
    windows_commands = (
        "cd /plugin && wine pip install --dry-run -r requirements.txt --report "
        f"windows.json && chown {uid}:{gid} /plugin/windows.json"
    )

    full_linux_command = "/bin/bash -c '" + " && ".join(linux_commands) + "'"
    client.containers.run(
        AGENT_PLUGIN_IMAGE,
        command=full_linux_command,
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )
    client.containers.run(
        PLUGIN_BUILDER_IMAGE,
        command=f'/bin/bash -c "{windows_commands}"',
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )

    linux_packages_path = build_dir / "linux.json"
    windows_packages_path = build_dir / "windows.json"

    linux_packages = load_package_names(linux_packages_path)
    windows_packages = load_package_names(windows_packages_path)

    linux_packages_path.unlink()
    windows_packages_path.unlink()

    response = all_equal([linux_packages, windows_packages])

    return response


def generate_common_vendor_dir(build_dir: Path, uid, gid):
    client = docker.from_env()
    commands = LINUX_IMAGE_PYENV_INIT_COMMANDS + [
        "cd /plugin && pip install -r requirements.txt -t src/vendor",
        f"chown -R {uid}:{gid} /plugin/src/vendor",
    ]

    full_command = "/bin/bash -c '" + " && ".join(commands) + "'"

    client.containers.run(
        AGENT_PLUGIN_IMAGE,
        command=full_command,
        volumes={str(build_dir): {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )


def generate_vendor_dirs(build_dir: Path, operating_system: OperatingSystem, uid, gid):
    if operating_system == OperatingSystem.LINUX:
        generate_linux_vendor_dir(build_dir, uid, gid)
    elif operating_system == OperatingSystem.WINDOWS:
        generate_windows_vendor_dir(build_dir, uid, gid)


def generate_linux_vendor_dir(build_dir: Path, uid, gid):
    client = docker.from_env()
    commands = LINUX_IMAGE_PYENV_INIT_COMMANDS + [
        "cd /plugin && pip install -r requirements.txt -t src/vendor-linux",
        f"chown -R {uid}:{gid} /plugin/src/vendor-linux",
    ]

    full_command = "/bin/bash -c '" + " && ".join(commands) + "'"
    client.containers.run(
        AGENT_PLUGIN_IMAGE,
        command=full_command,
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )


def generate_windows_vendor_dir(build_dir: Path, uid, gid):
    client = docker.from_env()
    commands = (
        f"cd /plugin && wine pip install -r requirements.txt -t src/vendor-windows && "
        f"chown -R {uid}:{gid} /plugin/src/vendor-windows"
    )

    client.containers.run(
        PLUGIN_BUILDER_IMAGE,
        command=f'/bin/bash -c "{commands}"',
        volumes={build_dir: {"bind": "/plugin", "mode": "rw"}},
        remove=True,
    )


def generate_requirements_file(build_dir: Path):
    if (build_dir / "poetry.lock").exists():
        command = ["poetry", "export", "-f", "requirements.txt", "-o", "requirements.txt"]
        subprocess.check_call(command, cwd=str(build_dir))
    elif (build_dir / "Pipfile.lock").exists():
        command = ["pipenv", "requirements"]
        with (build_dir / "requirements.txt").open("w") as f:
            subprocess.check_call(command, cwd=str(build_dir), stdout=f)
