import os
import time
import threading
import logging

from fastapi import FastAPI, Body, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .storage import load_json, save_json, update_json_file, user_config_file_lock, seen_file_lock
from .scanner import scan_network
from .mDNS import mdns_cache, start_mdns
from .backup import create_backup, import_backup
from .app_config import get_target_ip, get_scan_interval, get_log_level
from .device_config import DeviceConfig

# ---------------- CONFIG ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.environ.get("APP_DATA_DIR", "/data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(DATA_DIR, exist_ok=True)

USER_CONFIG_FILE = os.path.join(DATA_DIR, "user_config.json")
SEEN_FILE = os.path.join(DATA_DIR, "seen_devices.json")

interval = get_scan_interval()
target_ip = get_target_ip()

logging.basicConfig(
    level=get_log_level(),
    format="%(levelname)s %(asctime)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------- APP ----------------

app = FastAPI()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------- BACKGROUND SCAN STATE ----------------

scan_lock = threading.Lock()

scan_state = {
    "data": [],
    "last_started": None,
    "last_finished": None,
    "scanning": False,
    "error": None,
}

scan_now_event = threading.Event()
_background_started = False


def run_scan_once():

    with scan_lock:
        scan_state["last_started"] = time.time()
        scan_state["scanning"] = True
        scan_state["error"] = None

    try:
        logger.debug(f"Starting scan for {target_ip}")

        with user_config_file_lock:
            user_config = load_json(USER_CONFIG_FILE)

        with seen_file_lock:
            seen = load_json(SEEN_FILE)

        if not isinstance(user_config, dict):
            user_config = {}

        if not isinstance(seen, dict):
            seen = {}

        data, seen = scan_network(target_ip, user_config, seen, mdns_cache)

        if data is None:
            data = []

        with seen_file_lock:
            save_json(SEEN_FILE, seen)

        with scan_lock:
            scan_state["data"] = data
            scan_state["last_finished"] = time.time()
            scan_state["scanning"] = False
            scan_state["error"] = None

        logger.debug(f"Scan completed: {len(data)} devices")

    except Exception as e:
        with scan_lock:
            scan_state["scanning"] = False
            scan_state["error"] = str(e)

        logger.exception("Scan failed")

def scanner_loop():

    logger.debug(" Background scanner started")

    while True:
        run_scan_once()

        # Wacht SCAN_INTERVAL seconden, tenzij handmatig een scan wordt aangevraagd.
        
        logger.debug(f"Waiting {interval} seconds until next scan")

        scan_now_event.wait(interval)
        scan_now_event.clear()


@app.on_event("startup")
def startup():
    """
    Start background services één keer bij app startup.
    """
    global _background_started

    if _background_started:
        return

    _background_started = True

    threading.Thread(target=start_mdns, daemon=True).start()
    threading.Thread(target=scanner_loop, daemon=True).start()

    logger.debug("mDNS and scanner threads started")

def update_cached_device(mac, updates):
    with scan_lock:
        for device in scan_state["data"]:
            if device.get("mac") == mac:
                device.update(updates)


def update_device_config(mac, mutator):
    def updater(user_config):
        device_config = DeviceConfig.from_json(user_config.get(mac))

        mutator(device_config)

        if not device_config.name and not device_config.saved and not device_config.tracked:
            user_config.pop(mac, None)
        else:
            user_config[mac] = device_config.to_json()

        return user_config

    update_json_file(USER_CONFIG_FILE, user_config_file_lock, updater)


# ---------------- API ----------------

@app.get("/scan")
def scan():
    """
    Geeft direct de laatst bekende scanresultaten terug.
    Dit endpoint start zelf géén scan meer.
    """
    with scan_lock:
        return scan_state["data"]


@app.get("/scan/status")
def scan_status():
    """
    Debug/status endpoint voor frontend of browser console.
    """
    with scan_lock:
        return {
            "last_started": scan_state["last_started"],
            "last_finished": scan_state["last_finished"],
            "scanning": scan_state["scanning"],
            "error": scan_state["error"],
            "count": len(scan_state["data"]),
        }


@app.post("/scan/now")
def scan_now():
    """
    Vraag de background scanner om eerder wakker te worden.
    De scan draait alsnog op de achtergrond.
    """
    scan_now_event.set()
    return {"ok": True}

@app.post("/name")
def set_name(mac: str = Body(...), name: str = Body(...)):
    
    update_device_config(
        mac,
        lambda device_config: setattr(device_config, "name", name),
    )

    update_cached_device(
        mac,
        {"name": name},
    )

    return {"ok": True}

@app.post("/save")
def set_saved(mac: str = Body(...), saved: bool = Body(...)):

    update_device_config(
        mac,
        lambda device_config: setattr(device_config, "saved", saved),
    )

    update_cached_device(
        mac,
        {"saved": saved},
    )

    return {
        "ok": True,
        "mac": mac,
        "saved": saved,
    }

@app.post("/track")
def set_tracked(mac: str = Body(...), tracked: bool = Body(...)):

    update_device_config(
        mac,
        lambda device_config: setattr(device_config, "tracked", tracked),
    )

    update_cached_device(
        mac,
        {"tracked": tracked},
    )

    return {
        "ok": True,
        "mac": mac,
        "tracked": tracked,
    }

@app.post("/delete")
def delete(data: dict = Body(...)):
    mac = data.get("mac")

    if not mac:
        return {"ok": False, "error": "missing mac"}

    def updater_user_config(user_config):
        user_config.pop(mac, None)
        return user_config

    update_json_file(USER_CONFIG_FILE, user_config_file_lock, updater_user_config)

    def updater_seen(seen):
        seen.pop(mac, None)
        return seen
    update_json_file(SEEN_FILE, seen_file_lock, updater_seen)

    # Verwijder ook direct uit memory-cache zodat UI meteen klopt
    with scan_lock:
        scan_state["data"] = [
            device for device in scan_state["data"]
            if device.get("mac") != mac
        ]

    return {"ok": True}


@app.post("/clear")
def clear():

    def updater(seen):
        return {}
    
    update_json_file(SEEN_FILE, seen_file_lock, updater)
    
    with scan_lock:
        scan_state["data"] = []

    return {"ok": True}


@app.get("/mdns")
def get_mdns():
    return mdns_cache

@app.get("/export")
def export_data():

    backup = create_backup(
        USER_CONFIG_FILE,
        SEEN_FILE,
        user_config_file_lock,
        seen_file_lock,
    )

    export_path = os.path.join(
        DATA_DIR,
        "network-scanner-backup.json"
    )

    save_json(export_path, backup)

    return FileResponse(
        export_path,
        media_type="application/json",
        filename="network-scanner-backup.json",
    )

@app.post("/import")
async def import_data(file: UploadFile = File(...)):
    raw = await file.read()

    result = import_backup(
        raw,
        USER_CONFIG_FILE,
        SEEN_FILE,
        user_config_file_lock,
        seen_file_lock,
        merge=False,
    )

    if not result.get("ok"):
        return JSONResponse(
            status_code=400,
            content=result,
        )

    # Trigger direct een nieuwe achtergrondscan
    scan_now_event.set()

    return result
    
# ---------------- UI ----------------

@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(TEMPLATE_DIR, "index.html")) as f:
        return HTMLResponse(f.read())