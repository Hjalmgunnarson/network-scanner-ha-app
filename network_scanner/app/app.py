import os
import time
import json
import threading
import ipaddress

from fastapi import FastAPI, Body, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .storage import load_json, save_json
from .scanner import scan_network
from .mDNS import mdns_cache, start_mdns
from .backup import create_backup, import_backup


# ---------------- CONFIG ----------------

OPTIONS_FILE = "/data/options.json"
DEFAULT_TARGET_IP = "192.168.0.0/24"
DEFAULT_SCAN_INTERVAL = 30  # seconden

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.environ.get("APP_DATA_DIR", "/data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(DATA_DIR, exist_ok=True)

NAMES_FILE = os.path.join(DATA_DIR, "names.json")
SEEN_FILE = os.path.join(DATA_DIR, "seen_devices.json")

def get_target_ip():
    """
    Lees target_ip uit Home Assistant add-on options.
    Valt terug op DEFAULT_TARGET_IP als options.json ontbreekt of ongeldig is.
    """
    try:
        with open(OPTIONS_FILE, "r") as f:
            options = json.load(f)

        target_ip = options.get("target_ip", DEFAULT_TARGET_IP)

        # Valideer CIDR, bijvoorbeeld 192.168.0.0/24
        ipaddress.ip_network(target_ip, strict=False)

        return target_ip

    except Exception as e:
        print(f"[config] Could not read target_ip from {OPTIONS_FILE}: {e}")
        print(f"[config] Falling back to default target_ip: {DEFAULT_TARGET_IP}")
        return DEFAULT_TARGET_IP

def get_scan_interval():
    """
    Lees scan_interval uit Home Assistant add-on options.
    Valt terug op DEFAULT_SCAN_INTERVAL als options.json ontbreekt of ongeldig is.
    """
    try:
        with open(OPTIONS_FILE, "r") as f:
            options = json.load(f)

        interval = int(options.get("scan_interval", DEFAULT_SCAN_INTERVAL))

        # Extra veiligheid naast config.yaml schema
        if interval < 5:
            interval = 5

        if interval > 3600:
            interval = 3600

        return interval

    except Exception as e:
        print(f"[config] Could not read scan_interval from {OPTIONS_FILE}: {e}")
        print(f"[config] Falling back to default scan_interval: {DEFAULT_SCAN_INTERVAL}")
        return DEFAULT_SCAN_INTERVAL
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
    """
    Voert één scan uit en slaat het resultaat op in scan_state.
    /scan leest straks alleen deze cache.
    """
    target_ip = get_target_ip()

    with scan_lock:
        scan_state["last_started"] = time.time()
        scan_state["scanning"] = True
        scan_state["error"] = None

    try:
        print(f"[scanner] Starting scan for {target_ip}")

        names = load_json(NAMES_FILE)
        seen = load_json(SEEN_FILE)

        if not isinstance(names, dict):
            names = {}

        if not isinstance(seen, dict):
            seen = {}

        data, seen = scan_network(target_ip, names, seen, mdns_cache)

        if data is None:
            data = []

        save_json(SEEN_FILE, seen)

        with scan_lock:
            scan_state["data"] = data
            scan_state["last_finished"] = time.time()
            scan_state["scanning"] = False
            scan_state["error"] = None

        print(f"[scanner] Scan completed: {len(data)} devices")

    except Exception as e:
        with scan_lock:
            scan_state["scanning"] = False
            scan_state["error"] = str(e)

        print(f"[scanner] Scan failed: {e}")

def scanner_loop():
    """
    Background scanner.
    Draait continu zolang de add-on draait.
    """
    print("[scanner] Background scanner started")

    while True:
        run_scan_once()

        # Wacht SCAN_INTERVAL seconden, tenzij handmatig een scan wordt aangevraagd.
        interval = get_scan_interval()

        print(f"[scanner] Waiting {interval} seconds until next scan")

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

    print("[startup] mDNS and scanner threads started")


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
    names = load_json(NAMES_FILE)

    if name:
        names[mac] = name
    else:
        names.pop(mac, None)

    save_json(NAMES_FILE, names)
    return {"ok": True}


@app.post("/delete")
def delete(data: dict = Body(...)):
    mac = data.get("mac")

    if not mac:
        return {"ok": False, "error": "missing mac"}

    names = load_json(NAMES_FILE)
    seen = load_json(SEEN_FILE)

    # Verwijder eventuele custom name
    if isinstance(names, dict):
        names.pop(mac, None)
        save_json(NAMES_FILE, names)

    # Verwijder uit seen_devices als het een dict is
    if isinstance(seen, dict):
        seen.pop(mac, None)
        save_json(SEEN_FILE, seen)

    # Verwijder ook direct uit memory-cache zodat UI meteen klopt
    with scan_lock:
        scan_state["data"] = [
            d for d in scan_state["data"]
            if len(d) < 3 or d[2] != mac
        ]

    return {"ok": True}


@app.post("/clear")
def clear():
    save_json(SEEN_FILE, {})

    with scan_lock:
        scan_state["data"] = []

    return {"ok": True}


@app.get("/mdns")
def get_mdns():
    return mdns_cache

@app.get("/export")
def export_data():

    backup = create_backup(
        NAMES_FILE,
        SEEN_FILE,
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

    try:
        raw = await file.read()

        data = json.loads(raw.decode("utf-8"))

        result = import_backup(
            data,
            NAMES_FILE,
            SEEN_FILE,
            merge=False,
        )
        
        # Trigger direct een nieuwe achtergrondscan
        scan_now_event.set()
        return result

    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Invalid JSON syntax: {str(e)}"
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": str(e)
            },
        )
    
# ---------------- UI ----------------

@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(TEMPLATE_DIR, "index.html")) as f:
        return HTMLResponse(f.read())