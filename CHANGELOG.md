# Changelog

All notable changes to this project will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-08-01

### Added

- Opt-in Raspberry Pi installer switch for a systemd-managed kiosk service.
- Fullscreen `--kiosk` launch mode with Escape and F11 controls.
- Automatic service restart after application failures.

### Fixed

- Kiosk startup now inherits Wayland or XWayland from the logged-in desktop session.
- Manual refresh no longer creates additional recurring API polling timers.

## [0.1.0] - 2026-08-01

### Added

- Modern dark-mode desktop dashboard built with CustomTkinter.
- WeatherLink v2 station discovery, current conditions, and 24-hour history support.
- Temperature, wind, pressure, humidity, rain, UV, and solar visualizations.
- Metric and imperial unit modes.
- Environment-file configuration with no embedded credentials.
- Automated tests for configuration, normalization, and unit conversion.

[Unreleased]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/willcurtis/weatherlink-dashboard/releases/tag/v0.1.0
