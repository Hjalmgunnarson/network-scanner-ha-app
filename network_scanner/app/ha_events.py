import json
import os
import time
from urllib import request, error
from datetime import datetime, timezone

EVENT_TYPE = "network_scanner_new_device_detected"
SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN")
HA_EVENT_URL = f"http://supervisor/core/api/events/{EVENT_TYPE}"


if SUPERVISOR_TOKEN:
    print("[ha-events] SUPERVISOR_TOKEN obtained; Home Assistant event API enabled")
else:
    print("[ha-events] SUPERVISOR_TOKEN not found; Home Assistant events disabled")


def fire_new_device_detected_event(mac, ip, seen_at):

    if not SUPERVISOR_TOKEN:
        print("[ha-events] Cannot fire event: SUPERVISOR_TOKEN is missing")
        return False


    seen_at_iso = datetime.fromtimestamp(seen_at, timezone.utc).isoformat()
    payload = {
        "mac": mac,
        "ip": ip,
        "seen_at": seen_at_iso,
        "source": "network_scanner",
    }

    body = json.dumps(payload).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
        "Content-Type": "application/json",
    }

    req = request.Request(
        HA_EVENT_URL,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=5) as response:
            status = response.status

        if 200 <= status < 300:
            print(
                f"[ha-events] Event fired: {EVENT_TYPE} "
                f"mac={mac} ip={ip} seen_at={seen_at_iso}"
            )
            return True

        print(
            f"[ha-events] Failed to fire event: HTTP {status} "
            f"mac={mac} ip={ip}"
        )
        return False

    except error.HTTPError as e:
        try:
            response_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            response_body = ""

        print(
            f"[ha-events] Failed to fire event: HTTP {e.code} "
            f"mac={mac} ip={ip} response={response_body}"
        )
        return False

    except Exception as e:
        print(
            f"[ha-events] Failed to fire event: {e} "
            f"mac={mac} ip={ip}"
        )
        return False
