function normalize(s) {
    return (s || "").toLowerCase();
}

function getIcon(v) {
    const vendor = normalize(v);

    if (vendor.includes("espressif")) return "mdi-chip";
    if (vendor.includes("tp-link")) return "mdi-router-network-wireless";

    if (
        vendor.includes("samsung") ||
        vendor.includes("oneplus") ||
        vendor.includes("google")
    ) return "mdi-cellphone";

    if (
        vendor.includes("azurewave") ||
        vendor.includes("wistron") ||
        vendor.includes("intel")
    ) return "mdi-laptop";

    if (vendor.includes("roborock")) return "mdi-robot-vacuum";
    if (vendor.includes("nintendo")) return "mdi-controller-variant-outline";
    if (vendor.includes("raspberry")) return "mdi-server-network-outline";
    if (vendor.includes("pocketbook")) return "mdi-book-outline";

    if (
        vendor.includes("onbekend") ||
        vendor.includes("random") ||
        vendor.includes("ieee")
    ) return "mdi-help-circle-outline";

    return "mdi-network-outline";
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

function matchesBooleanFilter(value, filterValue) {
    if (filterValue === "all") {
        return true;
    }

    return value === (filterValue === "true");
}

function filterData(data) {
    return data.filter(device => {
        if (!matchesBooleanFilter(device.saved === true, savedFilter)) {
            return false;
        }

        if (!matchesBooleanFilter(device.tracked === true, trackedFilter)) {
            return false;
        }

        if (!matchesBooleanFilter(device.online === true, onlineFilter)) {
            return false;
        }

        if (!searchQuery) {
            return true;
        }

        const haystack = [
            device.ip,
            device.name,
            device.mac,
            device.vendor,
        ]
            .join(" ")
            .toLowerCase();

        return haystack.includes(searchQuery);
    });
}

function sortData(data) {
    return [...data].sort((a, b) => {
        if (sortKey === 0) {
            const ipA = ipToNumber(a.ip);
            const ipB = ipToNumber(b.ip);

            if (ipA !== ipB) {
                return sortAsc ? ipA - ipB : ipB - ipA;
            }

            return (b.last_seen || 0) - (a.last_seen || 0);
        }

        if (sortKey === 5) {
            return sortAsc
                ? a.last_seen - b.last_seen
                : b.last_seen - a.last_seen;
        }

        if (sortKey === 6) {
            return sortAsc
                ? a.first_seen - b.first_seen
                : b.first_seen - a.first_seen;
        }

        if (sortKey === 1) {
            return sortAsc
                ? (a.name || "").localeCompare(b.name || "")
                : (b.name || "").localeCompare(a.name || "");
        }

        return 0;
    });
}