function changeSort(value) {
    sortKey = Number(value);
    render();
}

function toggleSortDirection() {
    sortAsc = !sortAsc;
    render();
}

async function load() {
    try {
        currentData = await fetchScan();

        render();
        loadScanStatus();

    } catch (e) {
        console.error("Load error:", e);
        document.getElementById("status").innerText =
            "Could not load results.";
    }
}

async function loadScanStatus() {
    try {
        const status = await fetchScanStatus();

        const total = currentData.length;
        const online = currentData.filter(device => device.online).length;

        let text = `${online} online / ${total} total`;

        if (status.scanning) {
            text += " · Scanning";
        } else if (status.last_finished) {
            text += ` · Last scan: ${timeago.format(status.last_finished * 1000)}`;
        }

        if (status.error) {
            text += ` · ${status.error}`;
        }

        document.getElementById("status").innerText = text;

    } catch (e) {
        console.error("Scan status error:", e);
    }
}

async function saveName(mac, name) {
    try {
        await postJson("name", { mac, name });

        currentData = currentData.map(device => {
            if (device.mac !== mac) return device;

            device.name = name;
            return device;
        });

        render();
        loadScanStatus();

    } finally {
        editingName = false;
    }
}

async function toggleSave(mac) {
    const device = currentData.find(device => device.mac === mac);
    if (!device) return;

    const nextSaved = !device.saved;

    await postJson("save", {
        mac,
        saved: nextSaved
    });

    device.saved = nextSaved;
    render();
}

async function toggleTrack(mac) {
    const device = currentData.find(device => device.mac === mac);
    if (!device) return;

    const nextTracked = !device.tracked;

    await postJson("track", {
        mac,
        tracked: nextTracked
    });

    device.tracked = nextTracked;
    render();
}

async function del(mac) {
    await postJson("delete", { mac });

    currentData = currentData.filter(device => device.mac !== mac);
    render();
}

async function clearAll() {
    await fetch("clear", {
        method: "POST"
    });

    load();
}

function autoLoad() {
    if (editingName) {
        return;
    }

    load();
}

async function exportBackup() {
    window.location.href = "export";
}

async function importBackup(event) {
    const file = event.target.files[0];

    if (!file) {
        return;
    }

    const confirmed = confirm(
        "Are you sure you want to import this backup?"
    );

    if (!confirmed) {
        event.target.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const r = await fetch("import", {
            method: "POST",
            body: formData
        });

        if (!r.ok) {

            let message = `HTTP ${r.status}`;

            try {
                const error = await r.json();

                if (error.error) {
                    message = error.error;
                }

            } catch (_) {
                // ignore JSON parse failure
            }

            throw new Error(message);
        
        }

        const result = await r.json();

        console.log("Import result:", result);

        await load();

        alert("Import successful. Please wait for results!");

    } catch (e) {
        console.error("Import error:", e);

        alert(`Import failed:\n\n${e.message}`);
    }

    event.target.value = "";
}

function nextFilterState(value) {
    if (value === "all") return "true";
    if (value === "true") return "false";
    return "all";
}

function cycleSavedFilter() {
    savedFilter = nextFilterState(savedFilter);
    updateFilterButtons();
    render();
}

function cycleTrackedFilter() {
    trackedFilter = nextFilterState(trackedFilter);
    updateFilterButtons();
    render();
}

function cycleOnlineFilter() {
    onlineFilter = nextFilterState(onlineFilter);
    updateFilterButtons();
    render();
}

function applySearch(value) {
    searchQuery = value.toLowerCase().trim();
    render();
}

setInterval(autoLoad, 30000);
setInterval(loadScanStatus, 5000);

updateFilterButtons();
load();
