let currentData = [];
let sortKey = 0;
let sortAsc = true;
let editingName = false;
let searchQuery = "";

function normalize(s) {
    return (s || "").toLowerCase();
}

function getIcon(d) {
    const vendor = normalize(d[3]);

    if (vendor.includes("espressif")) return "cpu";
    if (vendor.includes("tp-link")) return "router";

    if (
        vendor.includes("samsung") ||
        vendor.includes("oneplus") ||
        vendor.includes("google")
    ) return "smartphone";

    if (
        vendor.includes("azurewave") ||
        vendor.includes("wistron") ||
        vendor.includes("intel")
    ) return "laptop";

    if (vendor.includes("roborock")) return "bot";
    if (vendor.includes("nintendo")) return "gamepad";
    if (vendor.includes("raspberry")) return "server";
    if (vendor.includes("pocketbook")) return "book";

    if (
        vendor.includes("onbekend") ||
        vendor.includes("random") ||
        vendor.includes("ieee")
    ) return "help-circle";

    return "monitor";
}

function handleKey(e, el) {
    if (e.key === "Enter") {
        el.blur();
    }
}

function getArrow(k) {
    if (sortKey !== k) return "";
    return sortAsc ? " ↑" : " ↓";
}

function ipToNumber(ip) {
    if (!ip) return 0;

    return ip
        .split(".")
        .reduce((acc, n) => acc * 256 + Number(n), 0);
}

function sortData(data) {
    return [...data].sort((a, b) => {
        if (sortKey === 0) {
            const ipA = ipToNumber(a[0]);
            const ipB = ipToNumber(b[0]);

            if (ipA !== ipB) {
                return sortAsc ? ipA - ipB : ipB - ipA;
            }

            return (b[5] || 0) - (a[5] || 0);
        }

        if (sortKey === 5) {
            return sortAsc ? a[5] - b[5] : b[5] - a[5];
        }

        if (sortKey === 6) {
            return sortAsc ? a[6] - b[6] : b[6] - a[6];
        }

        if (sortKey === 1) {
            return sortAsc
                ? (a[1] || "").localeCompare(b[1] || "")
                : (b[1] || "").localeCompare(a[1] || "");
        }

        return 0;
    });
}

function changeSort(value) {
    sortKey = Number(value);
    render();
}

function toggleSortDirection() {
    sortAsc = !sortAsc;
    render();
}

function render() {
    let t = document.getElementById("table");

    t.innerHTML = `
<tr class="table-header">
<th>IP${getArrow(0)}</th>
<th>Name${getArrow(1)}</th>
<th>MAC</th>
<th>Vendor</th>
<th>Status</th>
<th>Last Seen${getArrow(5)}</th>
<th>First Seen${getArrow(6)}</th>
<th>Actions</th>
</tr>
`;

    let filtered = currentData.filter(d => {

        if (!searchQuery) {
            return true;
        }

        const haystack = [
            d[0], // IP
            d[1], // Name
            d[2], // MAC
            d[3], // Vendor
        ]
            .join(" ")
            .toLowerCase();

        return haystack.includes(searchQuery);
    });

    let data = sortData(filtered);

    data.forEach(d => {
        const userName = d[7];
        const isNew = !userName;
        const online = d[4];

        const rowClass = isNew ? "new-device" : "";
        const rowStyle = online ? "" : "opacity:0.5;";

        t.innerHTML += `
<tr class="${rowClass}" style="${rowStyle}">
<td>${d[0]}</td>
<td class="name-cell">
  <span data-lucide="${getIcon(d)}" class="icon"></span>
    <input value="${d[1] || ""}"
        onfocus="editingName = true"
        onblur="saveName('${d[2]}', this.value)"
        onkeydown="handleKey(event, this)">
</td>
<td>${d[2]}</td>
<td class="vendor">${d[3]}</td>
<td><span class="status-dot ${online ? "online" : "offline"}"></span></td>
<td class="timeago" datetime="${new Date(d[5] * 1000).toISOString()}"></td>
<td class="timeago" datetime="${new Date(d[6] * 1000).toISOString()}"></td>
<td>
  <button onclick="del('${d[2]}')" class="icon-button delete-button" title="Delete">
    <span data-lucide="trash-2" class="button-icon"></span>
  </button>
</td>
</tr>`;
    });

    timeago.render(document.querySelectorAll(".timeago"));
    lucide.createIcons();
}

async function load() {
    try {
        let r = await fetch("scan");

        if (!r.ok) {
            throw new Error("HTTP " + r.status);
        }

        currentData = await r.json();
        render();
        loadScanStatus();

    } catch (e) {
        console.error("Load error:", e);
        document.getElementById("status").innerText =
            "⚠️ Kon resultaten niet laden";
    }
}

async function loadScanStatus() {
    try {
        const r = await fetch("scan/status");

        if (!r.ok) {
            throw new Error("HTTP " + r.status);
        }

        const status = await r.json();

        const total = currentData.length;
        const online = currentData.filter(d => d[4]).length;

        let text = `✅ ${online} online / ${total} total`;

        if (status.scanning) {
            text += " · 🔄 Scanning";
        } else if (status.last_finished) {
            text += ` · Last scan: ${timeago.format(status.last_finished * 1000)}`;
        }

        if (status.error) {
            text += ` · ⚠️ ${status.error}`;
        }

        document.getElementById("status").innerText = text;

    } catch (e) {
        console.error("Scan status error:", e);
    }
}

async function saveName(mac, name) {
    try {
        await fetch("name", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ mac, name })
        });

        currentData = currentData.map(d => {
            if (d[2] !== mac) return d;

            d[1] = name;
            d[7] = name || null;

            return d;
        });

        render();
        loadScanStatus();

    } finally {
        editingName = false;
    }
}

async function del(mac) {
    await fetch("delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ mac })
    });

    currentData = currentData.filter(d => d[2] !== mac);
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
        }

        const result = await r.json();

        console.log("Import result:", result);

        await load();

        alert("✅ Import succesful, please wait for results.");

    } catch (e) {
        console.error("Import error:", e);

        alert(`⚠️ Import failed:\n\n${e.message}`);
    }

    event.target.value = "";
}

function applySearch(value) {
    searchQuery = value.toLowerCase().trim();

    render();
}

setInterval(autoLoad, 30000);
setInterval(loadScanStatus, 5000);

load();
