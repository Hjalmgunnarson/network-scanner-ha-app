async function postJson(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(`${url} failed: HTTP ${response.status} ${text}`);
    }

    return response.json();
}

async function fetchScan() {
    const response = await fetch("scan");

    if (!response.ok) {
        throw new Error("scan failed: HTTP " + response.status);
    }

    return response.json();
}

async function fetchScanStatus() {
    const response = await fetch("scan/status");

    if (!response.ok) {
        throw new Error("scan/status failed: HTTP " + response.status);
    }

    return response.json();
}