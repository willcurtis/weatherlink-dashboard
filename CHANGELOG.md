# Changelog

All notable changes to this project will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.0] - 2026-08-01

### Added

- Finder-launchable macOS application and drag-to-Applications DMG build.
- Branded first-launch credential setup stored outside the application bundle.
- Automated Apple Silicon and Intel release packages through GitHub Actions.
- Optional Developer ID signing and Apple notarization using repository secrets.

### Changed

- Configuration discovery now supports a platform application-data file and explicit path override.

## [0.3.1] - 2026-08-01

### Fixed

- Restored the rounded bottom borders and corners on gauge and compass cards.

### Documentation

- Added a screenshot of the branded dashboard to the README.

## [0.3.0] - 2026-08-01

### Changed

- Reworked the dashboard with The Tech Shed logo and brand palette.
- Added a professional branded header, application icon, bordered data cards, and unified controls.
- Restyled charts, gauges, compass, live status, and footer for a cohesive visual hierarchy.

## [0.2.2] - 2026-08-01

### Fixed

- Dashboard footer is visible immediately without requiring a window resize.

## [0.2.1] - 2026-08-01

### Added

- Dashboard footer showing the installed application version.
- Clickable `© 2026 The Tech Shed` link to the GitHub repository.

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

[Unreleased]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/willcurtis/weatherlink-dashboard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/willcurtis/weatherlink-dashboard/releases/tag/v0.1.0
