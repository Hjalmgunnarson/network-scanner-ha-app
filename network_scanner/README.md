# Network Scanner

Lightweight Home Assistant add-on for discovering and tracking devices on your local network.

Network Scanner combines periodic ARP scanning with passive mDNS listening for ESPHome devices, providing a fast and reliable overview of active devices on your network.

Sure, you could use your routers page of clients or an app on your phone. But this is pretty convenient.

---

## Features

- 🔎 Periodic ARP network scanning
- 📡 Passive mDNS listener for ESPHome devices
- 💾 Persistent storage of discovered devices
- ✏️ Editable device names
- 🆕 Mark devices as “known” simply by naming them
- 🔍 Fast search and filtering
- ↕️ Sorting by IP address, name, first seen, and last seen
- 📤 Export device database to JSON backup
- 📥 Import backups
- 🌙 Dark mode with automatic theme support
- ⚡ Background scanning for responsive UI
- 🧹 Delete individual devices or clear scan history

---

## Why rename devices?

Unnamed devices are considered “new” devices.

Assigning a custom name to a device is the way to acknowledge and permanently recognize devices on your network.

Example:

- `192.168.0.45` → appears as new
- Rename to `Living Room ESP32`
- Device is now treated as known and easier to track

This makes it very easy to maintain an overview of trusted devices over time.

---

## How it works

### ARP Scanning

The add-on periodically scans the configured IP range using ARP requests to detect active devices on the network.

### mDNS Listener

In parallel, a passive mDNS listener listens for network announcements from ESPHome and other multicast-enabled devices.

This allows devices to appear even between scan intervals.

### Persistent Storage

Discovered devices and custom names are stored locally so they survive restarts and updates.

---

## Configuration

IP range and scan interval are configurable.
