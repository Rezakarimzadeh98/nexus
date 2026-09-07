const state = {
  charts: { trend: null, avg: null, volatility: null },
  records: [],
  summary: null,
};

const colors = ["#0f4cc9", "#059669", "#b45309", "#be123c", "#374151", "#7c3aed"];

const baseSelect = document.getElementById("baseSelect");
const targetsInput = document.getElementById("targetsInput");
const daysSelect = document.getElementById("daysSelect");
const loadBtn = document.getElementById("loadBtn");
const addBtn = document.getElementById("addBtn");
const statusText = document.getElementById("statusText");

loadBtn.addEventListener("click", loadOverview);
addBtn.addEventListener("click", addManualRecord);

loadOverview();

async function loadOverview() {
  const base = baseSelect.value.trim().toUpperCase();
  const targets = targetsInput.value.trim();
  const days = Number(daysSelect.value);

  setStatus("در حال دریافت داده آنلاین...", false);
  try {
    const response = await fetch(`/api/analytics/overview?base=${encodeURIComponent(base)}&targets=${encodeURIComponent(targets)}&days=${days}`);
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.message || "خطا در دریافت داده");
    }

    state.records = data.records;
    state.summary = data.summary;
    renderAll();
    setStatus(`دریافت موفق: ${data.records.length} رکورد واقعی`, false);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function addManualRecord() {
  const payload = {
    date: document.getElementById("manualDate").value,
    base: document.getElementById("manualBase").value,
    target: document.getElementById("manualTarget").value,
    rate: Number(document.getElementById("manualRate").value),
  };

  setStatus("در حال ذخیره رکورد دستی...", false);
  try {
    const response = await fetch("/api/manual-records", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "خطا در افزودن رکورد دستی");
    }

    await loadOverview();
    setStatus("رکورد دستی ذخیره شد و تحلیل به روز شد.", false);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function renderAll() {
  renderKpis();
  renderTable();
  renderTrendChart();
  renderAverageChart();
  renderVolatilityChart();
  renderInsights();
}

function renderKpis() {
  const box = document.getElementById("kpiBox");
  const s = state.summary?.kpis;
  if (!s || !state.records.length) {
    box.innerHTML = "<p>داده ای برای نمایش KPI وجود ندارد.</p>";
    return;
  }

  box.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-item"><h3>کل رکورد</h3><strong>${s.totalRecords}</strong></div>
      <div class="kpi-item"><h3>رکورد آنلاین</h3><strong>${s.onlineRecords}</strong></div>
      <div class="kpi-item"><h3>رکورد دستی</h3><strong>${s.manualRecords}</strong></div>
      <div class="kpi-item"><h3>آخرین تاریخ</h3><strong>${s.latestDate || "-"}</strong></div>
      <div class="kpi-item"><h3>میانگین نرخ آخرین روز</h3><strong>${formatRate(s.latestAverageRate || 0)}</strong></div>
    </div>
  `;
}

function renderTable() {
  const body = document.getElementById("recordsTable");
  const rows = [...state.records].sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, 180);
  body.innerHTML = rows
    .map(
      (r) =>
        `<tr><td>${r.date}</td><td>${r.base}</td><td>${r.target}</td><td>${formatRate(r.rate)}</td><td>${r.source}</td></tr>`
    )
    .join("");
}

function renderTrendChart() {
  const labels = uniqueDates(state.records);
  const targets = uniqueTargets(state.records);

  const datasets = targets.map((target, i) => ({
    label: target,
    data: labels.map((d) => getRate(state.records, d, target)),
    borderColor: colors[i % colors.length],
    pointRadius: 0,
    borderWidth: 2,
    tension: 0.25,
  }));

  state.charts.trend = replaceChart(state.charts.trend, "trendChart", {
    type: "line",
    data: { labels, datasets },
    options: chartOptions(),
  });
}

function renderAverageChart() {
  const stats = state.summary?.stats || [];
  state.charts.avg = replaceChart(state.charts.avg, "avgChart", {
    type: "bar",
    data: {
      labels: stats.map((x) => x.target),
      datasets: [
        {
          label: "میانگین نرخ",
          data: stats.map((x) => x.averageRate),
          backgroundColor: stats.map((_, i) => colors[i % colors.length]),
          borderRadius: 8,
        },
      ],
    },
    options: chartOptions(),
  });
}

function renderVolatilityChart() {
  const stats = state.summary?.stats || [];
  state.charts.volatility = replaceChart(state.charts.volatility, "volatilityChart", {
    type: "bar",
    data: {
      labels: stats.map((x) => x.target),
      datasets: [
        {
          label: "دامنه نوسان",
          data: stats.map((x) => x.volatility),
          backgroundColor: "#334155",
          borderRadius: 8,
        },
      ],
    },
    options: chartOptions(),
  });
}

function renderInsights() {
  const list = document.getElementById("insightList");
  const stats = state.summary?.stats || [];
  if (!stats.length) {
    list.innerHTML = "<li>داده کافی برای تحلیل وجود ندارد.</li>";
    return;
  }

  const maxVol = stats.reduce((m, c) => (c.volatility > m.volatility ? c : m), stats[0]);
  const strongest = stats.reduce((m, c) => (c.latestRate > m.latestRate ? c : m), stats[0]);
  const weakest = stats.reduce((m, c) => (c.latestRate < m.latestRate ? c : m), stats[0]);

  list.innerHTML = `
    <li>بیشترین نوسان: ${maxVol.target} با دامنه ${formatRate(maxVol.volatility)}</li>
    <li>بالاترین نرخ فعلی: ${strongest.target} با نرخ ${formatRate(strongest.latestRate)}</li>
    <li>پایین ترین نرخ فعلی: ${weakest.target} با نرخ ${formatRate(weakest.latestRate)}</li>
    <li>این تحلیل فقط از داده واقعی آنلاین و رکوردهای دستی معتبر ساخته شده است.</li>
  `;
}

function uniqueDates(records) {
  return Array.from(new Set(records.map((x) => x.date))).sort();
}

function uniqueTargets(records) {
  return Array.from(new Set(records.map((x) => x.target))).sort();
}

function getRate(records, date, target) {
  const row = records.find((x) => x.date === date && x.target === target);
  return row ? Number(row.rate) : null;
}

function replaceChart(ref, canvasId, config) {
  if (ref) {
    ref.destroy();
  }
  return new Chart(document.getElementById(canvasId), config);
}

function chartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "bottom" },
    },
    scales: {
      x: { ticks: { maxTicksLimit: 8 } },
      y: { beginAtZero: false },
    },
  };
}

function setStatus(text, isError) {
  statusText.textContent = text;
  statusText.className = isError ? "status error" : "status";
}

function formatRate(value) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 6 }).format(Number(value));
}
