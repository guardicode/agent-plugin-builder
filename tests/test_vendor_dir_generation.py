from pathlib import Path
from unittest.mock import MagicMock

import pytest
from monkeytypes import OperatingSystem

from agent_plugin_builder import (
    generate_common_vendor_dir,
    generate_requirements_file,
    generate_vendor_dirs,
    generate_windows_vendor_dir,
    should_use_common_vendor_dir,
)
from agent_plugin_builder.vendor_dir_generation import (
    LINUX_BUILD_VENDOR_DIR_COMMANDS,
    LINUX_PLUGIN_BUILDER_IMAGE,
    WINDOWS_BUILD_VENDOR_DIR_COMMANDS,
    WINDOWS_PLUGIN_BUILDER_IMAGE,
    CommandRunError,
)

# Sample package lists
LINUX_PACKAGES = {"package1", "package2", "package3"}
WINDOWS_PACKAGES_SAME = {"package1", "package2", "package3"}
WINDOWS_PACKAGES_DIFF = {"package1", "package2", "package4"}

# Sample paths
BUILD_DIR_PATH = Path("/non_existing/build/dir")
LINUX_PACKAGE_FILE_PATH = BUILD_DIR_PATH / "linux_packages.json"
WINDOWS_PACKAGE_FILE_PATH = BUILD_DIR_PATH / "windows_packages.json"


@pytest.fixture
def mock_docker(monkeypatch):
    mock_container = MagicMock()
    mock_container.return_value.containers.run.return_value = b""
    monkeypatch.setattr("docker.from_env", mock_container)

    return mock_container


@pytest.fixture
def mock_load_package_names(monkeypatch):
    def _mock_load_package_names(file_path):
        if file_path == LINUX_PACKAGE_FILE_PATH:
            return LINUX_PACKAGES
        elif file_path == WINDOWS_PACKAGE_FILE_PATH:
            return WINDOWS_PACKAGES_SAME
        else:
            return set()

    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation._load_package_names",
        MagicMock(side_effect=_mock_load_package_names),
    )


@pytest.fixture
def mock_load_package_names_diff(monkeypatch):
    def _mock_load_package_names(file_path):
        if file_path == LINUX_PACKAGE_FILE_PATH:
            return LINUX_PACKAGES
        elif file_path == WINDOWS_PACKAGE_FILE_PATH:
            return WINDOWS_PACKAGES_DIFF
        else:
            return set()

    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation._load_package_names",
        MagicMock(side_effect=_mock_load_package_names),
    )


@pytest.fixture
def mock_run_command(monkeypatch):
    mock_run_command = MagicMock(return_value=0)
    monkeypatch.setattr("agent_plugin_builder.vendor_dir_generation._run_command", mock_run_command)
    return mock_run_command


@pytest.fixture
def write_requirements_file(tmpdir, data_for_tests_dir):
    def inner(filename):
        build_dir_path = Path(tmpdir)
        data_requirements = (data_for_tests_dir / filename).read_text()
        (build_dir_path / "requirements.txt").write_text(data_requirements)

        return build_dir_path

    return inner


@pytest.fixture
def write_poetry_lock(tmpdir, data_for_tests_dir):
    def inner():
        build_dir_path = Path(tmpdir)
        poetry_data = (data_for_tests_dir / "poetry.lock").read_text()
        (build_dir_path / "poetry.lock").write_text(poetry_data)

        pyproject_data = (data_for_tests_dir / "pyproject.toml").read_text()
        (build_dir_path / "pyproject.toml").write_text(pyproject_data)

        return build_dir_path

    return inner


@pytest.mark.integration
def test_should_use_common_vendor_dir__not_possible(write_requirements_file):
    build_dir_path = write_requirements_file("requirements_common_not_possible.txt")

    assert not should_use_common_vendor_dir(build_dir_path)


@pytest.mark.integration
def test_should_use_common_vendor_dir__possible(write_requirements_file):
    build_dir_path = write_requirements_file("requirements_common_possible.txt")

    assert should_use_common_vendor_dir(build_dir_path)


def test_should_use_common_vendor_dir__nonexisting_requirements_file(tmpdir):
    assert not (BUILD_DIR_PATH / "requirements.txt").exists()
    with pytest.raises(FileNotFoundError):
        should_use_common_vendor_dir(BUILD_DIR_PATH)


def test_should_use_common_vendor_dir_same_packages(
    monkeypatch, mock_docker, mock_load_package_names
):
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.Path.exists", MagicMock(return_value=True)
    )
    result = should_use_common_vendor_dir(BUILD_DIR_PATH)

    assert result is True


def test_should_use_common_vendor_dir_diff_packages(
    monkeypatch, mock_docker, mock_load_package_names_diff
):
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.Path.exists", MagicMock(return_value=True)
    )
    result = should_use_common_vendor_dir(BUILD_DIR_PATH)

    assert result is False


def test_generate_vendor_dirs(monkeypatch):
    source_dir_name = "source_dir"
    mock_generate_linux_vendor_dir = MagicMock()
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.generate_common_vendor_dir",
        mock_generate_linux_vendor_dir,
    )
    mock_generate_windows_vendor_dir = MagicMock()
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.generate_windows_vendor_dir",
        mock_generate_windows_vendor_dir,
    )

    generate_vendor_dirs(BUILD_DIR_PATH, source_dir_name, OperatingSystem.LINUX)
    mock_generate_linux_vendor_dir.assert_called_once()

    generate_vendor_dirs(BUILD_DIR_PATH, source_dir_name, OperatingSystem.WINDOWS)
    mock_generate_windows_vendor_dir.assert_called_once()


def test_generate_vendor_dirs__nonexisting_os():
    with pytest.raises(ValueError):
        generate_vendor_dirs(BUILD_DIR_PATH, "source_dir", "nonexisting_os")


@pytest.mark.integration
def test_generate_common_vendor_dir_integration(write_requirements_file):
    build_dir_path = write_requirements_file("requirements_common_possible.txt")
    generate_common_vendor_dir(build_dir_path, "source_dir", "vendor")

    assert (build_dir_path / "source_dir" / "vendor").exists()
    assert len(list((build_dir_path / "source_dir" / "vendor").iterdir())) > 0


@pytest.mark.parametrize("vendor_dir_name", ["vendor", "vendor-linux"])
def test_generate_common_vendor_dir(monkeypatch, mock_docker, vendor_dir_name):
    source_dir_name = "source_dir"
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.getuid", MagicMock(return_value=1002)
    )
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.getgid", MagicMock(return_value=1030)
    )
    generate_common_vendor_dir(BUILD_DIR_PATH, source_dir_name, vendor_dir_name)

    mock_docker.return_value.containers.run.assert_called_once()
    expected_vendor_path = f"{source_dir_name}/{vendor_dir_name}"
    mock_docker.return_value.containers.run.assert_called_with(
        LINUX_PLUGIN_BUILDER_IMAGE,
        command=(
            "/bin/bash -l -c "
            f"'{LINUX_BUILD_VENDOR_DIR_COMMANDS.format(vendor_path=f'{expected_vendor_path}')}'"
        ),
        volumes={str(BUILD_DIR_PATH): {"bind": "/plugin", "mode": "rw"}},
        remove=True,
        user="1002:1030",
    )


@pytest.mark.integration
def test_generate_windows_vendor_dir_integration(write_requirements_file):
    build_dir_path = write_requirements_file("requirements_common_not_possible.txt")
    generate_windows_vendor_dir(build_dir_path, "source_dir")

    assert (build_dir_path / "source_dir" / "vendor-windows").exists()
    assert len(list((build_dir_path / "source_dir" / "vendor-windows").iterdir())) > 0


def test_generate_windows_vendor_dir(monkeypatch, mock_docker):
    source_dir_name = "source_dir"
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.getuid", MagicMock(return_value=1202)
    )
    monkeypatch.setattr(
        "agent_plugin_builder.vendor_dir_generation.getgid", MagicMock(return_value=1230)
    )
    generate_windows_vendor_dir(BUILD_DIR_PATH, source_dir_name)

    mock_docker.return_value.containers.run.assert_called_once()
    mock_docker.return_value.containers.run.assert_called_with(
        WINDOWS_PLUGIN_BUILDER_IMAGE,
        command=(
            "/bin/bash -l -c "
            f"'{WINDOWS_BUILD_VENDOR_DIR_COMMANDS.format(source_dir_name=f'{source_dir_name}')}'"
        ),
        volumes={str(BUILD_DIR_PATH): {"bind": "/plugin", "mode": "rw"}},
        remove=True,
        user="1202:1230",
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "verify_hashes, expected_requirements",
    [
        (True, "requirements_with_hashes.txt"),
        (False, "requirements_without_hashes.txt"),
    ],
)
def test_generate_requirements_file__integration_hashes(
    data_for_tests_dir, write_poetry_lock, verify_hashes, expected_requirements
):
    build_dir_path = write_poetry_lock()

    generate_requirements_file(build_dir_path, verify_hashes=verify_hashes)

    assert (build_dir_path / "requirements.txt").exists()
    assert (build_dir_path / "requirements.txt").read_text() == (
        data_for_tests_dir / expected_requirements
    ).read_text()


@pytest.mark.parametrize(
    "verify_hashes, expected_command",
    [
        (True, ["poetry", "export", "-f", "requirements.txt", "-o", "requirements.txt"]),
        (
            False,
            [
                "poetry",
                "export",
                "-f",
                "requirements.txt",
                "-o",
                "requirements.txt",
                "--without-hashes",
            ],
        ),
    ],
)
def test_generate_requirements_file(monkeypatch, mock_run_command, verify_hashes, expected_command):
    def mock_exists(path):
        if path.name == "poetry.lock":
            return True
        if path.name == "requirements.txt":
            return True
        return False

    monkeypatch.setattr(Path, "exists", mock_exists)
    generate_requirements_file(BUILD_DIR_PATH, verify_hashes)

    mock_run_command.assert_called_once_with(
        BUILD_DIR_PATH,
        expected_command,
    )


def test_generate_requirements_file_no_lock_file(monkeypatch, mock_run_command):
    def mock_exists(path):
        return path.name != "poetry.lock"

    monkeypatch.setattr(Path, "exists", mock_exists)

    with pytest.raises(FileNotFoundError):
        generate_requirements_file(BUILD_DIR_PATH, verify_hashes=True)

    mock_run_command.assert_not_called()


def test_generate_requirements_file_no_requiremenet_file(monkeypatch, mock_run_command):
    def mock_exists(path):
        return path.name != "requirements.txt"

    monkeypatch.setattr(Path, "exists", mock_exists)

    with pytest.raises(FileNotFoundError):
        generate_requirements_file(BUILD_DIR_PATH, verify_hashes=True)

    mock_run_command.assert_called_once()


def test_generate_requirements_file_command_error(monkeypatch, mock_run_command):
    mock_run_command = MagicMock(return_value=2)
    monkeypatch.setattr("agent_plugin_builder.vendor_dir_generation._run_command", mock_run_command)

    def mock_exists(path):
        return path.name == "poetry.lock"

    monkeypatch.setattr(Path, "exists", mock_exists)

    with pytest.raises(CommandRunError):
        generate_requirements_file(BUILD_DIR_PATH, verify_hashes=True)
