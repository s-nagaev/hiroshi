# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.3] - 2024-04-17

### Changed

- Reply message logic: prompt construction logic is fixed.
- Now, the provider list contains only providers explicitly marked as `working`


## [0.2.2] - 2024-04-16

### Changed

- Concatenate reply message text to the main prompt.

## [0.2.1] - 2024-04-01

### Added:
- Functionality for periodically report application operational status to the monitoring system by invoking a specific 
webhook.

## [0.2.0] - 2024-02-25

### Added:
- Implemented chatbot behavior in group chats: Hiroshi, once added to a group chat, now maintains a unified 
conversation history and possesses a single context when communicating with chat participants within the group.
- Introduced GROUP_ADMINS setting, which allows the definition of chat-bot administrators in groups. Chat-bot 
administrators have exclusive permission to set the provider and execute the /reset command within the group.

### Fixed:
- Fixed an error that prevented the use of Redis for storing bot data (due to incompatibility with the previously 
used library with python 3.11).


## [0.1.3] - 2024-02-24

### Changed

- The code has been slightly updated for compatibility with the new version of g4f.


## [0.1.2] - 2024-02-08

### Added 

- GitHub Action for building an artifact on a schedule with an updated version of g4f

### Changed

- Dependencies updated.


## [0.1.1] - 2023-11-24

### Changed

- Gpt4free upgraded to 0.1.8.8

## [0.1.0] - 2023-11-08

### Added

- Basic functionality.
- Session management.
- Dockerfile.
- Flake8 and Mypy setups.
- GitHub Action for linters.

[Unreleased]: https://github.com/s-nagaev/hiroshi/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/s-nagaev/hiroshi/tree/v0.1.3
[0.1.2]: https://github.com/s-nagaev/hiroshi/tree/v0.1.2
[0.1.1]: https://github.com/s-nagaev/hiroshi/tree/v0.1.1
[0.1.0]: https://github.com/s-nagaev/hiroshi/tree/v0.1.0