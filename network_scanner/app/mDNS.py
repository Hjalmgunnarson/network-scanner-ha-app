import time
from zeroconf import Zeroconf, ServiceBrowser
import logging

logger = logging.getLogger(__name__)

mdns_cache = {}

class MDNSListener:

    def remove_service(self, *args):
        pass

    def update_service(self, *args):
        pass

    def add_service(self, zeroconf, type, name):
        try:
            info = zeroconf.get_service_info(type, name)
            if info and info.addresses:
                ip = ".".join(map(str, info.addresses[0]))
                mdns_cache[ip] = name.split(".")[0]
        except:
            pass


def start_mdns():
    logger.debug(f"Starting listener")
    try:
        zc = Zeroconf()
        listener = MDNSListener()

        services = [
            # ✅ jouw bestaande
            "_http._tcp.local.",
            "_printer._tcp.local.",
            "_esphome._tcp.local.",
            "_esphomelib._tcp.local.",

            # ✅ NETWERK / HOSTNAMES (zeer nuttig)
            "_workstation._tcp.local.",
            "_smb._tcp.local.",
            "_ssh._tcp.local.",

            # ✅ SMART HOME + MEDIA
            "_googlecast._tcp.local.",
            "_hap._tcp.local.",         # Apple HomeKit
            "_airplay._tcp.local.",
            "_raop._tcp.local.",

            # ✅ IOT / DIY
            "_arduino._tcp.local.",
            "_mqtt._tcp.local.",

            # ✅ PRINTER / SCANNER (breder dan alleen jouw huidige)
            "_ipp._tcp.local.",
            "_ippusb._tcp.local.",
            "_scanner._tcp.local.",

            # ✅ NAS / STORAGE / DISCOVERY
            "_afpovertcp._tcp.local.",  # Apple file sharing
            "_nfs._tcp.local.",

            # ✅ EXTRA HANDIG (vaak verrassend hits)
            "_ftp._tcp.local.",
            "_telnet._tcp.local.",
        ]

        for s in services:
            try:
                ServiceBrowser(zc, s, listener)
            except:
                pass

        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("💥 mDNS CRASH:", e)
