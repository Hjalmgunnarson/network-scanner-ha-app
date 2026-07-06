import time
from scapy.all import ARP, Ether, srp
from netaddr import EUI

import socket

from .device_config import DeviceConfig
from .app_config import get_offline_interval, get_forget_interval
from .ha_requests import post_new_device_detected_event, post_device_tracker_state

# ---------------- HELPERS ----------------
offline_interval = get_offline_interval()
forget_interval = get_forget_interval()

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except OSError:
        return ""

def is_random_mac(mac):
    try:
        first_byte = int(mac.split(":")[0], 16)
        return (first_byte & 2) != 0
    except OSError:
        return False

def get_vendor(mac):
    if is_random_mac(mac):
        return "Random MAC Address"
    try:
        return EUI(mac).oui.registration().org
    except OSError:
        return "Unknown"

def scan_network(target_ip, user_config, seen, mdns_cache):
    arp = ARP(pdst=target_ip)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=4, verbose=0)[0]
    now = time.time()

    for _, r in result:
        ip = r.psrc
        mac = r.hwsrc

        if mac not in seen:
            seen[mac] = {"first_seen": now}
            
            post_new_device_detected_event(
                mac=mac,
                ip=ip,
                seen_at=now,
            )

        seen[mac].update({
            "ip": ip,
            "vendor": get_vendor(mac),
            "last_seen": now
        })

    devices = []

    for mac, d in list(seen.items()):
        ip = d.get("ip", "")
        last_seen = d.get("last_seen", 0)

        now_online = (now - last_seen) < offline_interval
        stale = (now - last_seen) > forget_interval

        raw_device_config = user_config.get(mac)

        # Niet saved, niet tracked, en te lang niet gezien:
        # verwijderen uit seen en overslaan.
        if raw_device_config is None and stale:
            seen.pop(mac, None)
            continue

        device_config = DeviceConfig.from_json(raw_device_config)

        hostname = get_hostname(ip)
        mdns_name = mdns_cache.get(ip, "")

        if raw_device_config is not None:
            display_name = device_config.name
        else:
            display_name = mdns_name or hostname

        saved = device_config.saved
        tracked = device_config.tracked

        devices.append({
            "ip": ip,
            "name": display_name,
            "mac": mac,
            "vendor": d.get("vendor", ""),
            "online": now_online,
            "last_seen": last_seen,
            "first_seen": d.get("first_seen", 0),
            "saved": saved,
            "tracked": tracked,
        })

        if tracked:
            post_device_tracker_state(
                mac,
                ip,
                last_seen,
                now_online,
                now,
                display_name,
            )

    return devices, seen