import time
from scapy.all import ARP, Ether, srp
from netaddr import EUI

import socket

OFFLINE_TIMEOUT = 241

# ---------------- HELPERS ----------------

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ""


def is_random_mac(mac):
    try:
        first_byte = int(mac.split(":")[0], 16)
        return (first_byte & 2) != 0
    except:
        return False

def get_vendor(mac):
    if is_random_mac(mac):
        return "Random MAC Address"
    try:
        return EUI(mac).oui.registration().org
    except:
        return "Unknown"

def scan_network(target_ip, names, seen, mdns_cache):
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

        seen[mac].update({
            "ip": ip,
            "vendor": get_vendor(mac),
            "last_seen": now
        })

    devices = []
    for mac, d in seen.items():
        last_seen = d.get("last_seen", 0)
        now_online = (now - last_seen) < OFFLINE_TIMEOUT
        hostname = get_hostname(ip)

        custom_name = names.get(mac)
        display_name = custom_name or hostname or mdns_cache.get(d.get("ip", ""), "")

        devices.append((
            d.get("ip",""),
            display_name,
            mac,
            d.get("vendor",""),
            now_online,
            last_seen,
            d.get("first_seen",0),
            custom_name
        ))

    return devices, seen