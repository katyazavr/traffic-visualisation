const globeContainer = document.getElementById("globeContainer");
const totalPacketsNode = document.getElementById("totalPackets");
const suspiciousPacketsNode = document.getElementById("suspiciousPackets");
const topRegionsNode = document.getElementById("topRegions");
const suspiciousOnlyNode = document.getElementById("suspiciousOnly");
const pauseBtn = document.getElementById("pauseBtn");

function apiBase() {
    const fromQuery = new URLSearchParams(window.location.search).get("api");
    if (fromQuery) {
        return fromQuery.replace(/\/$/, "");
    }
    return "/api";
}

const BACKEND_BASE = apiBase();
const POINT_LIFETIME_MS = 10_000;

let streamPaused = false;
let suspiciousOnly = false;
let points = [];

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function formatTimestamp(ts) {
    const sec = Number(ts);
    if (Number.isNaN(sec)) {
        return escapeHtml(String(ts));
    }
    const ms = sec > 1e12 ? sec : sec * 1000;
    try {
        return escapeHtml(new Date(ms).toLocaleString());
    } catch {
        return escapeHtml(String(ts));
    }
}

function pointTooltipHtml(d) {
    const ip = escapeHtml(d.ip ?? "");
    const region = escapeHtml(d.region ?? "");
    const lat = escapeHtml(Number(d.lat).toFixed(4));
    const lng = escapeHtml(Number(d.lng).toFixed(4));
    const ts = formatTimestamp(d.timestamp);
    const suspicious = d.s_mark === 1 ? "Да" : "Нет";
    return `
<div class="globe-tooltip">
  <div><strong>IP:</strong> ${ip}</div>
  <div><strong>Region:</strong> ${region}</div>
  <div><strong>Coordinates:</strong> ${lat}, ${lng}</div>
  <div><strong>Time:</strong> ${ts}</div>
  <div><strong>Suspicious:</strong> ${suspicious}</div>
</div>`;
}

const globe = Globe()(globeContainer)
    .globeImageUrl("//unpkg.com/three-globe/example/img/earth-night.jpg")
    .backgroundImageUrl("//unpkg.com/three-globe/example/img/night-sky.png")
    .pointColor((d) => (d.s_mark === 1 ? "#ff4d4f" : "#4da6ff"))
    .pointAltitude((d) => (d.s_mark === 1 ? 0.06 : 0.04))
    .pointRadius(0.52)
    .pointLabel(pointTooltipHtml)
    .pointsData([]);

globe.controls().autoRotate = true;
globe.controls().autoRotateSpeed = 0.35;

function renderPoints() {
    const now = Date.now();
    points = points.filter((point) => now - point.receivedAt <= POINT_LIFETIME_MS);
    const visible = suspiciousOnly ? points.filter((p) => p.s_mark === 1) : points;
    globe.pointsData(visible);
}

function addPoint(packet) {
    points.push({
        lat: packet.latitude,
        lng: packet.longitude,
        s_mark: packet.s_mark,
        ip: packet.ip,
        timestamp: packet.timestamp,
        region: packet.region || "",
        receivedAt: Date.now(),
    });
    renderPoints();
}

async function loadStats() {
    try {
        const response = await fetch(`${BACKEND_BASE}/stats`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const stats = await response.json();
        totalPacketsNode.textContent = stats.total_packets;
        suspiciousPacketsNode.textContent = stats.suspicious_packets;
        topRegionsNode.innerHTML = "";
        const list = stats.top_regions || [];
        if (list.length === 0) {
            const item = document.createElement("li");
            item.className = "stats-placeholder";
            item.textContent =
                Number(stats.total_packets) === 0
                    ? "Wile no packets check the backend"
                    : "No data for regions";
            topRegionsNode.appendChild(item);
            return;
        }
        list.forEach((entry, index) => {
            const item = document.createElement("li");
            const name = document.createElement("span");
            name.className = "top-region-name";
            name.textContent = entry.region;
            const count = document.createElement("span");
            count.className = "top-region-count";
            count.textContent = ` — ${entry.count}`;
            item.appendChild(name);
            item.appendChild(count);
            topRegionsNode.appendChild(item);
        });
    } catch (error) {
        console.error("Failed to fetch stats", error);
        topRegionsNode.innerHTML = "";
        const item = document.createElement("li");
        item.className = "stats-error";
        item.textContent =
            "No stats";
        topRegionsNode.appendChild(item);
    }
}

function connectStream() {
    const source = new EventSource(`${BACKEND_BASE}/stream`);
    source.onmessage = (event) => {
        if (streamPaused) {
            return;
        }
        const packet = JSON.parse(event.data);
        addPoint(packet);
    };
    source.onerror = () => {
        source.close();
        setTimeout(connectStream, 3000);
    };
}

suspiciousOnlyNode.addEventListener("change", (event) => {
    suspiciousOnly = event.target.checked;
    renderPoints();
});

pauseBtn.addEventListener("click", () => {
    streamPaused = !streamPaused;
    pauseBtn.textContent = streamPaused ? "Resume stream" : "Pause stream";
});

setInterval(renderPoints, 1000);
setInterval(loadStats, 2000);
loadStats();
connectStream();
