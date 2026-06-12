function render() {
    const table = document.getElementById("table");
    const filtered = filterData(currentData);
    const data = sortData(filtered);

    table.innerHTML = renderHeader() + data.map(renderRow).join("");

    timeago.render(Array.from(document.querySelectorAll(".timeago")));
}

function formatExactTime(timestamp) {
    if (!timestamp) return "";

    return new Date(timestamp * 1000).toLocaleString();
}

function renderHeader() {
    return `
<tr class="table-header">
<th>IP${getArrow(0)}</th>
<th>Name${getArrow(1)}</th>
<th>MAC</th>
<th>Vendor</th>
<th>Status</th>
<th>Last Seen${getArrow(5)}</th>
<th>First Seen${getArrow(6)}</th>
<th>Actions</th>
</tr>`;
}

function renderRow(device) {

    const rowStyle = device.online ? "" : "opacity:0.5;";

    const rowClass = !device.saved ? "new-device" : "";

    const saveIcon = device.saved ? "mdi-content-save-minus" : "mdi-content-save-check";
    const saveTitle = device.saved ? "Forget" : "Save"
    const saveStateClass = device.saved ? "state-on" : "state-off";

    const trackIcon = device.tracked ? "mdi-map-marker-minus-outline" : "mdi-map-marker-plus-outline";
    const trackTitle = device.tracked ? "Ignore" : "Track"
    const trackStateClass = device.tracked ? "state-on" : "state-off";

    return `
<tr class="${rowClass}" style="${rowStyle}">
<td>${device.ip}</td>
<td class="name-cell">
  <span class="mdi ${getIcon(device.vendor)} icon"></span>
    <input value="${device.name || ""}"
        onfocus="editingName = true"
        onblur="saveName('${device.mac}', this.value)"
        onkeydown="handleKey(event, this)">
</td>
<td>${device.mac}</td>
<td class="vendor">${device.vendor}</td>
<td><span class="status-dot ${device.online ? "online" : "offline"}"></span></td>
<td
  class="timeago"
  datetime="${new Date(device.last_seen * 1000).toISOString()}"
  title="${formatExactTime(device.last_seen)}"
></td>
<td
  class="timeago"
  datetime="${new Date(device.first_seen * 1000).toISOString()}"
  title="${formatExactTime(device.first_seen)}"
></td>
<td class="row-actions">
  <div class="row-action-buttons">
    <button onclick="toggleSave('${device.mac}')" class="icon-button save-button ${saveStateClass}" title="${saveTitle}">
    <span class="mdi ${saveIcon} button-icon"></span>
    </button>

    <button onclick="toggleTrack('${device.mac}')" class="icon-button track-button ${trackStateClass}" title="${trackTitle}">
    <span class="mdi ${trackIcon} button-icon"></span>
    </button>

    <button onclick="del('${device.mac}')" class="icon-button delete-button state-danger" title="Delete">
    <span class="mdi mdi-delete-outline button-icon"></span>
    </button>
  </div>
</td>
</tr>`;
}

function updateFilterButton(buttonId, filterValue, icons, labels) {
    const button = document.getElementById(buttonId);

    if (!button) {
        return;
    }

    const icon = button.querySelector(".mdi");

    button.classList.remove("state-on", "state-off", "state-neutral");

    if (filterValue === "true") {
        button.classList.add("state-on");
        button.title = labels.true;
        icon.className = `mdi ${icons.true} button-icon`;
        return;
    }

    if (filterValue === "false") {
        button.classList.add("state-off");
        button.title = labels.false;
        icon.className = `mdi ${icons.false} button-icon`;
        return;
    }

    button.classList.add("state-neutral");
    button.title = labels.all;
    icon.className = `mdi ${icons.all} button-icon`;
}

function updateFilterButtons() {
    updateFilterButton(
        "savedFilterButton",
        savedFilter,
        {
            all: "mdi-content-save-outline",
            true: "mdi-content-save-check",
            false: "mdi-content-save-minus",
        },
        {
            all: "Saved filter: All",
            true: "Saved filter: Saved only",
            false: "Saved filter: Not saved only",
        }
    );

    updateFilterButton(
        "trackedFilterButton",
        trackedFilter,
        {
            all: "mdi-map-marker-outline",
            true: "mdi-map-marker-check-outline",
            false: "mdi-map-marker-minus-outline",
        },
        {
            all: "Tracked filter: All",
            true: "Tracked filter: Tracked only",
            false: "Tracked filter: Not tracked only",
        }
    );

    updateFilterButton(
        "onlineFilterButton",
        onlineFilter,
        {
            all: "mdi-lan-pending",
            true: "mdi-lan-connect",
            false: "mdi-lan-disconnect",
        },
        {
            all: "Online filter: All",
            true: "Online filter: Online only",
            false: "Online filter: Offline only",
        }
    );
}
