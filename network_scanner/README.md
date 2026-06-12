# Network Scanner

Network Scanner is a lightweight Home Assistant app for discovering, reviewing, saving, and optionally tracking devices on your local network.

The app combines active ARP scanning with passive mDNS listening. It provides insight into local devices, including IP address, MAC address, online/offline status, vendor, first seen time, and last seen time.

Network Scanner can also push discovery events and selected device tracker state updates to Home Assistant.

## Screenshot

![Network Scanner dashboard](docs/network_scanner_app.png)

## Features

- Periodic ARP network scanning
- Passive mDNS listener
- Device overview with:
  - IP address
  - MAC address
  - online/offline status
  - vendor
  - first seen timestamp
  - last seen timestamp
- Automatic display names based custom name or available network information
- Save devices so they are remembered
- Automatically forget unsaved and untracked devices after the configured forget interval
- Uses HA API to push discovery events and state updates
- Search, filter and sort devices
- Export and import backup files
- Dark and Light theme mode topped with automatic theme support
- Background scanning for a responsive UI
- Delete individual devices or clear complete scan history
- Debug links for scan results, scan status, and mDNS cache

## Device names

Devices can have a display name from multiple sources:

1. A custom name set by the user
2. mDNS information
3. hostname / reverse DNS information
4. empty or unknown if no name source is available

A custom name is stored in the user configuration and survives restarts and imports.

## Saving devices

A device can be marked as saved.

Saved devices are stored in the user configuration and remain visible, even if they are offline or have not been seen recently.

Devices that are not saved and not tracked will be forgotten automatically after the configured forget interval. This keeps the device list clean while allowing important devices to be kept permanently.

## Tracking devices

A device can be marked as tracked.

Tracked devices are pushed to Home Assistant as `device_tracker` state updates. This allows Home Assistant to maintain online/offline history for selected devices. 

Tracking is optional. Devices that are not tracked are still visible in the Network Scanner UI, but they will not receive Home Assistant `device_tracker` state updates.

For complete online/offline history in Home Assistant, devices should be marked as tracked so that Network Scanner can push state updates to Home Assistant.

## How it works

### ARP scanning

The app periodically scans the configured IP range using ARP requests. Devices that respond are marked as online and their `last_seen` timestamp is updated.

### mDNS listener

In parallel, the app listens for mDNS announcements. This helps enrich device information and can provide useful display names for devices that advertise themselves on the local network.

### User configuration

The user configuration contains:

```json
{
  "7a:13:c9:4e:82:bd": {
    "name": "Example device",
    "saved": true,
    "tracked": false
  }
}
```

Scanner data and user configuration are stored separately so that runtime scan data does not overwrite user preferences.

### Scanner data

Scanner data contains runtime discovery information such as:

```json
{
  "7a:13:c9:4e:82:bd": {
    "ip": "192.168.0.45",
    "vendor": "Example vendor",
    "first_seen": 1781000000,
    "last_seen": 1781091000
  }
}
```

## Home Assistant integration

Network Scanner can integrate with Home Assistant in two ways:

1. By firing a discovery event when a new device is detected.
2. By pushing state updates for selected tracked devices to Home Assistant `device_tracker` entities.

Discovery events are useful for notifications and automations.

Device tracker state updates are useful when Home Assistant should maintain online/offline history for specific devices.

## Home Assistant discovery event

When Network Scanner discovers a device that has not been seen before, it can fire a Home Assistant event.

Event type:

```text
network_scanner_new_device_detected
```

Example event payload:

```json
{
  "mac": "a6_4d_9b_2e_71_c8",
  "ip": "192.168.0.45",
  "seen_at": "2026-06-12T10:15:30+02:00",
  "source": "network_scanner"
}
```

The MAC address is formatted with underscores.

### Listening for discovery events in Home Assistant

You can listen for this event manually or create all kinds of automations. To listen manually:

1. Open Home Assistant.
2. Go to **Developer Tools**.
3. Open the **Events** tab.
4. Listen to:

```text
network_scanner_new_device_detected
```

5. Connect a new device to the network, or delete an existing discovered device from Network Scanner so it can be discovered again.

## Home Assistant device tracker updates

Network Scanner can push online/offline state updates to Home Assistant for devices that are marked as tracked.

Tracked devices are updated through the Home Assistant REST API state endpoint:

```text
/api/states/<entity_id>
```

Network Scanner uses entity IDs in this format:

```text
device_tracker.network_scanner_<MAC_WITH_UNDERSCORES>
```

Example MAC address:

```text
a6:4d:9b:2e:71:c8
```

Resulting entity ID:

```text
device_tracker.network_scanner_a6_4d_9b_2e_71_c8
```

### State values

Network Scanner reports device tracker state as:

```text
home
not_home
```

A tracked device is reported as `home` when Network Scanner considers the device online.

A tracked device is reported as `not_home` when the device has not been seen within the configured offline interval.

### State update payload

Example JSON payload for an offline device:

```json
{
  "state": "not_home",
  "attributes": {
    "source_type": "router",
    "mac": "a6_4d_9b_2e_71_c8",
    "ip": "192.168.0.45",
    "last_seen": "2026-06-12T10:15:30+02:00",
    "last_update": "2026-06-12T10:16:00+02:00",
    "managed_by": "network_scanner_addon",
    "name": "Example device"
  }
}
```

For complete online/offline history in Home Assistant, mark the device as tracked in Network Scanner so state updates are pushed to Home Assistant.

## Template device tracker entity

Posting to `/api/states/<entity_id>` updates Home Assistant state, but it does not by itself create a fully registry-backed entity.

For a better Home Assistant experience, create a template `device_tracker` entity with a stable `unique_id`.

The template entity acts as a registry-backed shell.

### Important

The entity ID created for Home Assistant must match the entity ID used by Network Scanner.

Network Scanner uses this pattern:

```text
device_tracker.network_scanner_<MAC_WITH_UNDERSCORES>
```

The MAC address must be formatted with underscores in:

- the template `name`

It is highly advised to use the same pattern for the unique_id, so that the device can be edited from the UI. This allows you to give is a friendly name.

- the template `unique_id`

Example MAC address:

```text
a6:4d:9b:2e:71:c8
```

Expected entity ID:

```text
device_tracker.network_scanner_a6_4d_9b_2e_71_c8
```

Example template device tracker configuration:

```yaml
- device_tracker:
    - name: "Network Scanner a6_4d_9b_2e_71_c8"
      unique_id: "network_scanner_a6_4d_9b_2e_71_c8"
      in_zones: "{{ ['zone.home'] }}"
```

## Configuration

Example app configuration:

```yaml
target_ip: "192.168.0.0/24"
scan_interval: 30
offline_interval: 360
forget_interval: 2880
log_level: info
```

Options:

| Option | Description |
|---|---|
| `target_ip` | Target subnet to scan |
| `scan_interval` | Scan interval |
| `offline_interval` | Time before a device is considered offline |
| `forget_interval` | Time before unsaved and untracked devices are automatically forgotten |
| `log_level` | Logging verbosity |

Intervals are in seconds

## Import and export

Network Scanner can export its stored data to a JSON backup file and import that file again later.

The backup contains:

- user configuration
- known scan history

This is useful for:

- reinstalling the app
- moving to a fresh Home Assistant installation
- keeping a backup of saved devices
- restoring device state after testing

### Backup structure

Current backups use:

```json
{
  "version": 2,
  "exported_at": 1781091000,
  "user_config": {
    "7a:13:c9:4e:82:bd": {
      "name": "Example device",
      "saved": true,
      "tracked": false
    }
  },
  "seen_devices": {
    "7a:13:c9:4e:82:bd": {
      "ip": "192.168.0.45",
      "vendor": "Example vendor",
      "first_seen": 1781000000,
      "last_seen": 1781091000
    }
  }
}
```

Legacy backups using `names` can be imported and normalized to the current `user_config` format.

## Debug endpoints

The app exposes useful debug endpoints:

```text
/scan
/scan/status
/mdns
```

The UI includes buttons that open these endpoints directly from inside the app interface. See the botom of the dashboard.

## Privacy

All scanning is performed locally.

No cloud services are used.

No external telemetry is collected.

Device information remains inside the app and Home Assistant environment.
