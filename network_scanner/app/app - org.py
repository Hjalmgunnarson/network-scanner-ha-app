import json
import os
import time
import threading
import requests

from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse, JSONResponse

from scapy.all import ARP, Ether, srp
from zeroconf import Zeroconf, ServiceBrowser
from netaddr import EUI

# ---------------- CONFIG ----------------
TARGET_IP = "192.168.0.0/24"
CACHE_TTL = 10
NAMES_FILE = "data/names.json"
SEEN_FILE = "data/seen_devices.json"

app = FastAPI()

cache = {"data": [], "timestamp": 0}
mdns_cache = {}

# ---------------- HELPERS ----------------
def get_vendor(mac):
    try:
        return EUI(mac).oui.registration().org
    except:
        return "Onbekend"

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- MDNS ----------------
class MDNSListener:
    def add_service(self, zeroconf, type, name):
        try:
            info = zeroconf.get_service_info(type, name)
            if info and info.addresses:
                ip = ".".join(map(str, info.addresses[0]))
                mdns_cache[ip] = name.split(".")[0]
        except:
            pass

def start_mdns():
    zc = Zeroconf()
    listener = MDNSListener()
    for s in ["_http._tcp.local.",
              "_printer._tcp.local.",
              "_esphome._tcp.local.",
              "_esphomelib._tcp.local."]:
        try:
            ServiceBrowser(zc, s, listener)
        except:
            pass
    while True:
        time.sleep(1)

threading.Thread(target=start_mdns, daemon=True).start()

# ---------------- SCAN ----------------
def scan_network():
    names = load_json(NAMES_FILE)
    seen = load_json(SEEN_FILE)

    arp = ARP(pdst=TARGET_IP)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=2, verbose=0)[0]
    now = time.time()

    for _, r in result:
        ip = r.psrc
        mac = r.hwsrc

        if mac not in seen:
            seen[mac] = {"first_seen": now}

        seen[mac].update({
            "ip": ip,
            "vendor": get_vendor(mac),
            "name": names.get(mac) or mdns_cache.get(ip, ""),
            "last_seen": now
        })

    devices = []
    for mac, d in seen.items():
        ip = d.get("ip", "")
        name = names.get(mac) or d.get("name", "")
        vendor = d.get("vendor", "")
        last_seen = d.get("last_seen", 0)
        first_seen = d.get("first_seen", 0)
        online = (now - last_seen) < 30

        devices.append((ip, name, mac, vendor, online, last_seen, first_seen))

    save_json(SEEN_FILE, seen)
    return devices

# ---------------- API ----------------
@app.get("/scan")
def scan():
    now = time.time()
    if now - cache["timestamp"] > CACHE_TTL:
        cache["data"] = scan_network()
        cache["timestamp"] = now
    return JSONResponse(cache["data"])

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
def delete(mac: str = Body(...)):
    seen = load_json(SEEN_FILE)
    names = load_json(NAMES_FILE)
    seen.pop(mac, None)
    names.pop(mac, None)
    save_json(SEEN_FILE, seen)
    save_json(NAMES_FILE, names)
    return {"ok": True}

@app.post("/clear")
def clear():
    save_json(SEEN_FILE, {})
    return {"ok": True}

# ---------------- UI ----------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<html>
<head>
<title>Network Scanner</title>
<style>
body { font-family: Arial; padding:20px; }
table { border-collapse: collapse; width:100%; }
th, td { border:1px solid #ddd; padding:6px; }
th { background:#eee; cursor:pointer; }
button { margin-right:5px; }
</style>
</head>
<body>

<h2>🔎 Network Scanner</h2>

<button onclick="load()">🔄 Refresh</button>
<button onclick="clearAll()">🧹 Clear All</button>

<p id="status">⏳ Ready</p>

<table id="table"></table>

<script>

let currentData = [];
let sortKey = null;
let sortAsc = true;
let spinnerInterval;
let spinnerState = 0;
let spinnerChars = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"];

function startSpinner() {
    const el = document.getElementById("status");

    spinnerState = 0;

    spinnerInterval = setInterval(() => {
        el.innerText = spinnerChars[spinnerState % spinnerChars.length] + " Scannen...";
        spinnerState++;
    }, 100);
}

function stopSpinner() {
    clearInterval(spinnerInterval);

    document.getElementById("status").innerText =
        `✅ ${currentData.length} devices`;
}

function formatDateTime(ts){
    return new Date(ts*1000).toLocaleString();
}

function getArrow(k){
    if(sortKey!==k) return "";
    return sortAsc ? " ↑" : " ↓";
}

function sortData(data){
    if(!sortKey) return data;

    return [...data].sort((a,b)=>{
        let A=a[sortKey], B=b[sortKey];

        if(sortKey===0){
            let a4=Number((A||"").split(".")[3]||0);
            let b4=Number((B||"").split(".")[3]||0);
            return sortAsc ? a4-b4 : b4-a4;
        }

        if(sortKey===5||sortKey===6){
            return sortAsc ? A-B : B-A;
        }

        return sortAsc
            ? String(A).localeCompare(String(B))
            : String(B).localeCompare(String(A));
    });
}

function setSort(k){
    if(sortKey===k){ sortAsc=!sortAsc; }
    else{ sortKey=k; sortAsc=true; }
    render();
}

function render(){
    let t=document.getElementById("table");

    t.innerHTML = `
<tr>
<th onclick="setSort(0)">IP${getArrow(0)}</th>
<th onclick="setSort(1)">Name${getArrow(1)}</th>
<th>MAC</th>
<th>Vendor</th>
<th>Status</th>
<th onclick="setSort(5)">Last Seen${getArrow(5)}</th>
<th onclick="setSort(6)">First Seen${getArrow(6)}</th>
<th>Actions</th>
</tr>
`;

    let data=sortData(currentData);

    data.forEach(d=>{
        let online=d[4];
        let style=online?"":"opacity:0.5;";

        t.innerHTML+=`
<tr style="${style}">
<td>${d[0]}</td>
<td><input value="${d[1]||""}" oninput="saveName('${d[2]}',this.value)"></td>
<td>${d[2]}</td>
<td>${d[3]}</td>
<td>${online?"🟢":"🔴"}</td>
<td>${formatDateTime(d[5])}</td>
<td>${formatDateTime(d[6])}</td>
<td><button onclick="del('${d[2]}')">❌</button></td>
</tr>`;
    });
}

async function load(){
    startSpinner();

    let r=await fetch("/scan");
    currentData=await r.json();

    stopSpinner();
    render();
}

async function saveName(mac,name){
    await fetch("/name",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({mac,name})
    });
}

async function del(mac){
    await fetch("/delete",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({mac})
    });
    load();
}

async function clearAll(){
    await fetch("/clear",{method:"POST"});
    load();
}

setInterval(load,120000);
load();

</script>

</body>
</html>
"""