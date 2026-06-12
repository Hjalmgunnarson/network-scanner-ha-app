import json
import os
import logging
from urllib import request, error
from datetime import datetime

logger = logging.getLogger(__name__)

NEW_DEVICE_EVENT_POSTFIX = "events/network_scanner_new_device_detected"
SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN")
HA_BASE_URL = "http://supervisor/core/api/"


if SUPERVISOR_TOKEN:
    logger.info("SUPERVISOR_TOKEN obtained; Home Assistant API enabled")
else:
    logger.error("SUPERVISOR_TOKEN not found; Home Assistant disabled")

def mac_with_underscores(mac: str) -> str:
    return mac.lower().replace(":", "_")

def mac_to_entity_id(mac):
    return f"device_tracker.network_scanner_{mac_with_underscores(mac)}"

def formatTime(seen_at):
    return datetime.fromtimestamp(seen_at).astimezone().isoformat()


def post(url_postfix, payload):

    if not SUPERVISOR_TOKEN:
        logger.error("Cannot fire event: SUPERVISOR_TOKEN is missing")
        return False
    
    full_url = f"{HA_BASE_URL}{url_postfix}"

    body = json.dumps(payload).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
        "Content-Type": "application/json",
    }

    req = request.Request(
        full_url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=5) as response:
            status = response.status

        if 200 <= status < 300:
            logger.info(
                f"Posted: {full_url} "
                f"{body}"
            )
            return True

        logger.error(
            f"Failed to fire event: {full_url} "
            f"status: {status}, {body}"
        )
        return False

    except error.HTTPError as e:
        try:
            response_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            response_body = ""

        logger.error(
            f"Failed to fire event: HTTP {e.code} "
            f"{url_postfix}{body} response={response_body}"
        )
        return False

    except Exception as e:
        logger.error(
            f"Failed to fire event: {e} "
            f"{url_postfix}{body}"
        )
        return False

def post_new_device_detected_event(mac, ip, seen_at):

    seen_at_iso = formatTime(seen_at)
    payload = {
        "mac": mac_with_underscores(mac),
        "ip": ip,
        "seen_at": seen_at_iso,
        "source": "network_scanner",
    }

    return post(NEW_DEVICE_EVENT_POSTFIX, payload)

def post_device_tracker_state(mac, ip, last_seen, is_home, time_of_scan, custom_name):

    entity_id = mac_to_entity_id(mac)
    state = "home" if is_home else "not_home"
    last_seen_iso = formatTime(last_seen)
    time_of_scan_iso = formatTime(time_of_scan)
    payload = {
        "state": state,
        "attributes": {
            "source_type": "router",
            "mac": mac_with_underscores(mac),
            "ip": ip,
            "last_seen": last_seen_iso,
            "last_update": time_of_scan_iso,
            "managed_by": "network_scanner_addon",
            "name": custom_name
        },
    }

    return post(
        url_postfix=f"states/{entity_id}",
        payload=payload,
    )


