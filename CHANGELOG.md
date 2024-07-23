# Changelog
All notable changes to this project will be documented in this
file.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
the [PEP 440 version scheme](https://peps.python.org/pep-0440/#version-scheme).

## [0.5.0] - 2024-07-22
### Added
- `--platform-dependencies` CLI option. #8
- `--verify/--no-verify` CLI option. #8

### Removed
- Plugin's build.yml configuration scripts. #8

### Changed
- Default value for `--platform-dependencies` CLI option to "autodetect". #9

## [0.4.0] - 2024-07-18
### Fixed
- Project unusability due to outdated dependency. #6

## [0.3.0] - 2024-07-18
### Security
- Commands do not run as the root user inside containers. #5

## [0.2.0] - 2024-07-15
### Fixed
- Improper handling of the `--source-dir` CLI option. #4
