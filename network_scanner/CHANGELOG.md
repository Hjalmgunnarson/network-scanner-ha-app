# Changelog

## 2.0.1

### Fixed

- Increased range for forget interval to 7 days.
- Adjusted size of export, import and delete all buttons.

## 2.0.0

### Added

- Added Home Assistant device tracker support for tracked devices.
- Added save functionality for devices.
- Added filter options for saved, tracked, and online devices.
- Added UI buttons for useful debug endpoints.
- Added automatic cleanup for devices that are unnamed, unsaved, and untracked after the configured interval.
- Added file locking for persistent JSON storage to improve reliability during concurrent updates.

### Changed

- Refactored device naming storage from `names` to `user_config`.
- Refactored render logic and applied small frontend fixes.
- Replaced `print` statements with structured logging.
- Updated the UI for the save button and related device actions.
- Moved from Lucide to Material Design icons.

## 1.0.2

### Added

- When a new device is detected, an event is fired to the HA event API

## 1.0.1

### Fixed

- Improved mobile card layout
- Fixed MAC label rendering on mobile

## 1.0.0

- Initial public release
- Periodic ARP scanning
- mDNS listener for ESPHome
- Search and filtering
- Import/export support
- Persistent storage
- Editable device names
- Dark mode support