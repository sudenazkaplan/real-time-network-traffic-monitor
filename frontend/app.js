const socket = io("http://localhost:5000");

// --- Canlı grafik ---
const inData = Array(60).fill(0);
const chartLabels = Array.from({length: 60}, (_, i) => i === 59 ? "now" : (i % 20 === 0 ? `−${60-i}s` : ""));

const liveChart = new Chart(document.getElementById("chart-live"), {
  type: "line",
  data: {
    labels: chartLabels,
    datasets: [{
      label: "Mbps",
      data: inData,
      borderColor: "#0a84ff",
      backgroundColor: "rgba(10,132,255,0.08)",
      borderWidth: 1.5,
      pointRadius: 0,
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 150 },
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#86868b", font: { size: 10 } }, grid: { color: "rgba(0,0,0,0.04)" }, border: { display: false } },
      y: { min: 0, ticks: { color: "#86868b", font: { size: 10 }, callback: v => v + "M" }, grid: { color: "rgba(0,0,0,0.04)" }, border: { display: false } }
    }
  }
});

// --- Protokol pasta grafiği ---
const protoChart = new Chart(document.getElementById("chart-proto"), {
  type: "doughnut",
  data: {
    labels: ["TCP", "UDP", "ICMP", "Other"],
    datasets: [{ data: [0,0,0,0], backgroundColor: ["#0a84ff","#30d158","#ff9500","#aeaeb2"], borderWidth: 2, borderColor: "#ffffff" }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "70%",
    plugins: { legend: { display: false } }
  }
});

// --- Alert sistemi ---
const alerts = [];
let alertCount = 0;
let prevMbps = 0;

function addAlert(type, msg) {
  alertCount++;
  const cls = type === "danger" ? "alert-d" : type === "warning" ? "alert-w" : "alert-i";
  const dotCls = type === "danger" ? "adot-d" : type === "warning" ? "adot-w" : "adot-i";
  const now = new Date().toLocaleTimeString("tr-TR", {hour:"2-digit",minute:"2-digit",second:"2-digit"});
  alerts.unshift({ cls, dotCls, msg, now });
  if (alerts.length > 6) alerts.pop();

  document.getElementById("alert-list").innerHTML = alerts.map(a =>
    `<div class="alert ${a.cls}">
      <div class="adot ${a.dotCls}"></div>
      <div class="alert-txt">${a.msg}</div>
      <span class="alert-ts">${a.now}</span>
    </div>`
  ).join("");
  document.getElementById("alert-count").textContent = alertCount + " active";
}

// --- Renk yardımcısı ---
const protoColors = { TCP: "#0a84ff", UDP: "#30d158", ICMP: "#ff9500", OTHER: "#aeaeb2" };

// --- Socket verisi ---
let knownHosts = new Set();

socket.on("traffic_update", (data) => {
  const mbps = data.mbps;

  // ML alert'leri işle
if (data.ml_alerts && data.ml_alerts.length > 0) {
    data.ml_alerts.forEach(a => addAlert(a.type, a.msg));
}

  // Metrik kartlar
  document.getElementById("mbps").textContent = mbps;
  document.getElementById("pps").textContent = data.pps.toLocaleString();
  document.getElementById("hosts").textContent = data.active_hosts;
  document.getElementById("bps-badge").textContent = mbps + " Mbps";

  // Mbps trend
  const trendEl = document.getElementById("mbps-trend");
  if (mbps > prevMbps) { trendEl.textContent = "↑ artıyor"; trendEl.className = "trend trend-up"; }
  else if (mbps < prevMbps) { trendEl.textContent = "↓ azalıyor"; trendEl.className = "trend trend-dn"; }
  else { trendEl.textContent = "— stabil"; trendEl.className = "trend"; }
  prevMbps = mbps;

  // Canlı grafik
  inData.shift();
  inData.push(mbps);
  liveChart.data.datasets[0].data = [...inData];
  liveChart.update("none");

  // Protokol dağılımı
  const pd = data.protocol_dist;
  const total = Object.values(pd).reduce((a, b) => a + b, 0) || 1;
  const keys = ["TCP","UDP","ICMP","OTHER"];
  protoChart.data.datasets[0].data = keys.map(k => pd[k] || 0);
  protoChart.update("none");

  keys.forEach(k => {
    const pct = Math.round((pd[k] || 0) / total * 100);
    const barId = "bar-" + k.toLowerCase();
    const pctId = "pct-" + k.toLowerCase();
    const barEl = document.getElementById(barId);
    const pctEl = document.getElementById(pctId);
    if (barEl) barEl.style.width = pct + "%";
    if (pctEl) pctEl.textContent = pct + "%";
  });

  // En baskın protokol
  const topProto = keys.reduce((a, b) => (pd[a]||0) > (pd[b]||0) ? a : b);
  const topPct = Math.round((pd[topProto]||0) / total * 100);
  document.getElementById("top-proto").textContent = topProto;
  document.getElementById("top-proto-pct").textContent = "paketlerin %" + topPct + "'i";

  document.getElementById("proto-total").textContent = total.toLocaleString() + " pkts";

  // Top talkers tablosu
  const maxBytes = data.top_talkers[0]?.bytes || 1;
  document.getElementById("talker-count").textContent = data.active_hosts + " hosts";
  document.getElementById("talker-body").innerHTML = data.top_talkers.map(t => {
    const kb = (t.bytes / 1024).toFixed(1);
    const share = Math.round(t.bytes / maxBytes * 100);
    const color = protoColors[t.protocol] || "#aeaeb2";
    return `<tr>
      <td style="font-weight:500">${t.ip}</td>
      <td><span class="pill pill-${t.protocol}">${t.protocol}</span></td>
      <td>${kb} KB</td>
      <td><div class="bbar"><div class="bfill" style="width:${share}%;background:${color}"></div></div></td>
    </tr>`;
  }).join("");

  // Alert kuralları
  if (mbps > 5) addAlert("warning", `<strong>BW spike</strong> — ${mbps} Mbps tespit edildi`);

  data.top_talkers.forEach(t => {
    if (!knownHosts.has(t.ip)) {
      knownHosts.add(t.ip);
      addAlert("info", `<strong>Yeni host</strong> — ${t.ip} ağa katıldı`);
    }
  });

  if (pd["ICMP"] > 50) addAlert("danger", `<strong>ICMP flood</strong> — ${pd["ICMP"]} paket/sn`);
});

socket.on("connect", () => addAlert("info", "Sunucuya bağlandı, izleme başladı"));
socket.on("disconnect", () => addAlert("danger", "<strong>Bağlantı kesildi</strong> — yeniden bağlanılıyor…"));