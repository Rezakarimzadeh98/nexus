const state = {
  charts: { trend: null, avg: null, volatility: null, forecast: null },
  records: [],
  summary: null,
  news: null,
  forecast: null,
  decision: null,
  apiKey: localStorage.getItem("nexus_api_key") || "",
};

const colors = ["#0f4cc9", "#059669", "#b45309", "#be123c", "#374151", "#7c3aed"];

const baseSelect = document.getElementById("baseSelect");
const targetsInput = document.getElementById("targetsInput");
const daysSelect = document.getElementById("daysSelect");
const loadBtn = document.getElementById("loadBtn");
const addBtn = document.getElementById("addBtn");
const loadNewsBtn = document.getElementById("loadNewsBtn");
const loadForecastBtn = document.getElementById("loadForecastBtn");
const statusText = document.getElementById("statusText");
const apiKeyInput = document.getElementById("apiKeyInput");
const saveApiKeyBtn = document.getElementById("saveApiKeyBtn");
const checkMeBtn = document.getElementById("checkMeBtn");
const loadAuditBtn = document.getElementById("loadAuditBtn");
const openDashboardBtn = document.getElementById("openDashboardBtn");
const openSecurityBtn = document.getElementById("openSecurityBtn");

loadBtn.addEventListener("click", loadOverview);
addBtn.addEventListener("click", addManualRecord);
loadNewsBtn.addEventListener("click", loadNewsAnalysis);
loadForecastBtn.addEventListener("click", loadForecast);
saveApiKeyBtn.addEventListener("click", saveApiKey);
checkMeBtn.addEventListener("click", checkMe);
loadAuditBtn.addEventListener("click", loadAudit);
openDashboardBtn?.addEventListener("click", () => {
  document.querySelector("main.layout")?.scrollIntoView({ behavior: "smooth", block: "start" });
});
openSecurityBtn?.addEventListener("click", () => {
  document.querySelector(".access-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

apiKeyInput.value = state.apiKey;

loadOverview();
loadNewsAnalysis();
loadForecast();
loadDecisionScore();

async function loadOverview() {
  const base = baseSelect.value.trim().toUpperCase();
  const targets = targetsInput.value.trim();
  const days = Number(daysSelect.value);

  setStatus("Fetching live market data...", false);
  try {
    const response = await apiFetch(`/api/analytics/overview?base=${encodeURIComponent(base)}&targets=${encodeURIComponent(targets)}&days=${days}`);
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Failed to load analytics data");
    }

    state.records = data.records;
    state.summary = data.summary;
    renderAll();
    await loadForecast();
    setStatus(`Loaded successfully: ${data.records.length} real records`, false);
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

  setStatus("Saving manual record...", false);
  try {
    const response = await apiFetch("/api/manual-records", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Failed to add manual record");
    }

    await Promise.all([loadOverview(), loadForecast(), loadDecisionScore()]);
    setStatus("Manual record saved and analytics refreshed.", false);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function loadForecast() {
  const base = baseSelect.value.trim().toUpperCase();
  const targets = targetsInput.value.trim();
  const days = Number(daysSelect.value);
  const horizon = Number(document.getElementById("forecastHorizonSelect").value);

  setStatus("Running forecast model...", false);
  try {
    const response = await apiFetch(
      `/api/forecast/overview?base=${encodeURIComponent(base)}&targets=${encodeURIComponent(targets)}&days=${days}&horizon=${horizon}`
    );
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Failed to compute forecast");
    }

    state.forecast = data.forecast;
    renderForecastChart();
    renderForecastTable();
    setStatus(`Forecast ready: ${horizon}-day horizon`, false);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function loadDecisionScore() {
  const base = baseSelect.value.trim().toUpperCase();
  const targets = targetsInput.value.trim();
  const days = Number(daysSelect.value);
  const horizon = Number(document.getElementById("forecastHorizonSelect").value);
  const newsQuery = document.getElementById("newsQueryInput")?.value?.trim() || "forex market";
  const newsMax = Number(document.getElementById("newsMaxSelect")?.value || 20);

  try {
    const response = await apiFetch(
      `/api/decision/score?base=${encodeURIComponent(base)}&targets=${encodeURIComponent(
        targets
      )}&days=${days}&horizon=${horizon}&newsQuery=${encodeURIComponent(newsQuery)}&newsMax=${newsMax}`
    );
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Failed to compute decision score");
    }
    state.decision = data.score;
    renderDecisionBox();
  } catch (error) {
    const content = document.getElementById("decisionContent");
    content.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
  }
}

function renderAll() {
  renderKpis();
  renderTable();
  renderTrendChart();
  renderAverageChart();
  renderVolatilityChart();
  renderInsights();
  renderIndicatorTable();
  renderNewsKpis();
  renderNewsTable();
  renderDecisionBox();
}

function renderForecastChart() {
  const forecast = state.forecast;
  if (!forecast || !forecast.items?.length) {
    state.charts.forecast = replaceChart(state.charts.forecast, "forecastChart", {
      type: "line",
      data: { labels: [], datasets: [] },
      options: chartOptions(),
    });
    return;
  }

  const labels = [];
  for (const item of forecast.items) {
    if (item.ok && item.forecast.length) {
      for (const point of item.forecast) {
        labels.push(point.date);
      }
      break;
    }
  }

  const uniqueLabels = Array.from(new Set(labels)).sort();
  const datasets = [];
  let colorIndex = 0;

  for (const item of forecast.items) {
    if (!item.ok || !item.forecast.length) {
      continue;
    }

    const color = colors[colorIndex % colors.length];
    colorIndex += 1;

    const map = new Map(item.forecast.map((p) => [p.date, p.predicted]));
    datasets.push({
      label: `${item.target} forecast`,
      data: uniqueLabels.map((d) => map.get(d) ?? null),
      borderColor: color,
      backgroundColor: "transparent",
      borderWidth: 2,
      borderDash: [6, 4],
      pointRadius: 0,
      tension: 0.2,
    });
  }

  state.charts.forecast = replaceChart(state.charts.forecast, "forecastChart", {
    type: "line",
    data: { labels: uniqueLabels, datasets },
    options: chartOptions(),
  });
}

function renderForecastTable() {
  const body = document.getElementById("forecastTable");
  const items = state.forecast?.items || [];
  if (!items.length) {
    body.innerHTML = "<tr><td colspan=\"9\">No forecast data available.</td></tr>";
    return;
  }

  body.innerHTML = items
    .map((item) => {
      if (!item.ok) {
        return `<tr><td>${escapeHtml(item.target)}</td><td>${escapeHtml(item.model)}</td><td>${item.dataPoints}</td><td>-</td><td>-</td><td>-</td><td colspan=\"3\">${escapeHtml(item.reason || "")}</td></tr>`;
      }

      const first = item.forecast[0];
      return `<tr>
        <td>${escapeHtml(item.target)}</td>
        <td>${escapeHtml(item.model)}</td>
        <td>${item.dataPoints}</td>
        <td>${formatNum(item.metrics?.mae)}</td>
        <td>${formatNum(item.metrics?.rmse)}</td>
        <td>${formatNum(item.metrics?.mape)}</td>
        <td>${formatRate(first?.predicted)}</td>
        <td>${formatRate(first?.lower95)}</td>
        <td>${formatRate(first?.upper95)}</td>
      </tr>`;
    })
    .join("");
}

function renderKpis() {
  const box = document.getElementById("kpiBox");
  const s = state.summary?.kpis;
  if (!s || !state.records.length) {
    box.innerHTML = "<p>No KPI data available for display.</p>";
    return;
  }

  box.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-item"><h3>Total Records</h3><strong>${s.totalRecords}</strong></div>
      <div class="kpi-item"><h3>Online Records</h3><strong>${s.onlineRecords}</strong></div>
      <div class="kpi-item"><h3>Manual Records</h3><strong>${s.manualRecords}</strong></div>
      <div class="kpi-item"><h3>Latest Date</h3><strong>${s.latestDate || "-"}</strong></div>
      <div class="kpi-item"><h3>Latest Avg Rate</h3><strong>${formatRate(s.latestAverageRate || 0)}</strong></div>
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
          label: "Average Rate",
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
          label: "Volatility Range",
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
    list.innerHTML = "<li>Not enough data to generate insights.</li>";
    return;
  }

  const maxVol = stats.reduce((m, c) => (c.volatility > m.volatility ? c : m), stats[0]);
  const strongest = stats.reduce((m, c) => (c.latestRate > m.latestRate ? c : m), stats[0]);
  const weakest = stats.reduce((m, c) => (c.latestRate < m.latestRate ? c : m), stats[0]);

  const technicalOverview = state.summary?.technicalOverview;
  list.innerHTML = `
    <li>Highest volatility: ${maxVol.target} with range ${formatRate(maxVol.volatility)}</li>
    <li>Strongest current rate: ${strongest.target} at ${formatRate(strongest.latestRate)}</li>
    <li>Weakest current rate: ${weakest.target} at ${formatRate(weakest.latestRate)}</li>
    <li>Technical signal mix: strong bullish ${technicalOverview?.strongBullishTargets || 0} | bullish ${technicalOverview?.bullishTargets || 0} | neutral ${technicalOverview?.neutralTargets || 0} | bearish ${technicalOverview?.bearishTargets || 0} | strong bearish ${technicalOverview?.strongBearishTargets || 0}</li>
    <li>Market score (0-100): ${formatNum(technicalOverview?.marketScore || 50)}</li>
    <li>This view is generated from live market data and validated manual records only.</li>
  `;
}

function renderIndicatorTable() {
  const body = document.getElementById("indicatorTable");
  const stats = state.summary?.stats || [];
  if (!stats.length) {
    body.innerHTML = "<tr><td colspan=\"19\">Not enough data for indicator calculations.</td></tr>";
    return;
  }

  body.innerHTML = stats
    .map((row) => {
      const t = row.technical || {};
      return `<tr>
        <td>${escapeHtml(row.target)}</td>
        <td>${signalTag(t.signal)}</td>
        <td>${formatNum(t.signalScore)}</td>
        <td>${formatNum(t.rsi14)}</td>
        <td>${formatRate(t.atr14)}</td>
        <td>${formatNum(t.adx14)}</td>
        <td>${formatNum(t.cci20)}</td>
        <td>${formatNum(t.stochasticK14)}</td>
        <td>${formatNum(t.macd)}</td>
        <td>${formatNum(t.macdSignal)}</td>
        <td>${formatRate(t.sma20)}</td>
        <td>${formatRate(t.sma50)}</td>
        <td>${formatRate(t.ema21)}</td>
        <td>${formatRate(t.ema50)}</td>
        <td>${formatRate(t.bollingerUpper)}</td>
        <td>${formatRate(t.bollingerLower)}</td>
        <td>${formatNum(t.roc12)}</td>
        <td>${formatNum(t.momentum10)}</td>
        <td>${formatNum(t.zScore20)}</td>
      </tr>`;
    })
    .join("");
}

function renderDecisionBox() {
  const content = document.getElementById("decisionContent");
  const d = state.decision;
  if (!d) {
    content.innerHTML = "<p>Decision score has not been computed yet.</p>";
    return;
  }

  content.innerHTML = `
    <div class="decision-grid">
      <div class="kpi-item"><h3>Technical Score</h3><strong>${formatNum(d.technicalScore)}</strong></div>
      <div class="kpi-item"><h3>Forecast Score</h3><strong>${formatNum(d.forecastScore)}</strong></div>
      <div class="kpi-item"><h3>News Score</h3><strong>${formatNum(d.newsScore)}</strong></div>
      <div class="kpi-item"><h3>Composite Score</h3><strong>${formatNum(d.compositeScore)}</strong></div>
      <div class="kpi-item"><h3>Verdict</h3><span class="decision-verdict ${verdictClass(d.verdict)}">${escapeHtml(d.verdict)}</span></div>
    </div>
  `;
}

async function loadNewsAnalysis() {
  const query = document.getElementById("newsQueryInput").value.trim();
  const max = Number(document.getElementById("newsMaxSelect").value);
  if (!query) {
    setStatus("Please enter a news theme.", true);
    return;
  }

  setStatus("Analyzing market news...", false);
  try {
    const response = await apiFetch(`/api/news/analyze?query=${encodeURIComponent(query)}&max=${max}`);
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Failed to analyze market news");
    }
    state.news = data;
    renderNewsKpis();
    renderNewsTable();
    setStatus(`News analysis ready: ${data.totalArticles} articles`, false);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function renderNewsKpis() {
  const box = document.getElementById("newsKpiBox");
  const news = state.news;
  if (!news) {
    box.innerHTML = "<p>News analysis has not been executed yet.</p>";
    return;
  }

  box.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-item"><h3>Theme</h3><strong>${escapeHtml(news.query)}</strong></div>
      <div class="kpi-item"><h3>Articles</h3><strong>${news.totalArticles}</strong></div>
      <div class="kpi-item"><h3>Positive</h3><strong>${news.sentiment.positive}</strong></div>
      <div class="kpi-item"><h3>Negative</h3><strong>${news.sentiment.negative}</strong></div>
      <div class="kpi-item"><h3>Average Score</h3><strong>${news.sentiment.averageScore}</strong></div>
    </div>
  `;
}

function renderNewsTable() {
  const body = document.getElementById("newsTable");
  const news = state.news;
  if (!news || !news.articles?.length) {
    body.innerHTML = "<tr><td colspan=\"5\">No news data available.</td></tr>";
    return;
  }

  body.innerHTML = news.articles
    .map((n) => {
      const cls =
        n.sentiment === "positive"
          ? "sentiment-positive"
          : n.sentiment === "negative"
          ? "sentiment-negative"
          : "sentiment-neutral";
      return `<tr><td>${escapeHtml(n.pubDate || "-")}</td><td>${escapeHtml(n.source || "-")}</td><td>${escapeHtml(
        n.title || "-"
      )}</td><td class="${cls}">${escapeHtml(n.sentiment || "neutral")}</td><td><a href="${escapeHtml(
        n.link || "#"
      )}" target="_blank" rel="noopener noreferrer">Open</a></td></tr>`;
    })
    .join("");
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

function saveApiKey() {
  const value = apiKeyInput.value.trim();
  state.apiKey = value;
  localStorage.setItem("nexus_api_key", value);
  setStatus("API key saved.", false);
}

async function checkMe() {
  try {
    const response = await apiFetch("/api/admin/me");
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Failed to fetch current user");
    }
    setStatus(`Role: ${data.user.role || "none"} | Auth: ${data.user.authenticated}`, false);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function loadAudit() {
  const body = document.getElementById("auditTable");
  try {
    const response = await apiFetch("/api/admin/audit?limit=50");
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Failed to load audit events");
    }
    body.innerHTML = data.events
      .map(
        (e) => `<tr><td>${escapeHtml(e.ts || "-")}</td><td>${escapeHtml(e.method || "-")}</td><td>${escapeHtml(
          e.path || "-"
        )}</td><td>${escapeHtml(String(e.status || "-"))}</td><td>${escapeHtml(e.role || "-")}</td></tr>`
      )
      .join("");
    setStatus(`Audit loaded: ${data.events.length}`, false);
  } catch (error) {
    body.innerHTML = `<tr><td colspan="5">${escapeHtml(error.message)}</td></tr>`;
    setStatus(error.message, true);
  }
}

function apiFetch(url, options = {}) {
  const merged = {
    ...options,
    headers: {
      ...(options.headers || {}),
      "x-api-key": state.apiKey
    }
  };
  return fetch(url, merged);
}

function formatNum(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 }).format(Number(value));
}

function signalTag(signal) {
  const val = String(signal || "neutral");
  const cls =
    val === "strong_bullish"
      ? "signal-tag signal-strong-bullish"
      : val === "bullish"
      ? "signal-tag signal-bullish"
      : val === "bearish"
      ? "signal-tag signal-bearish"
      : val === "strong_bearish"
      ? "signal-tag signal-strong-bearish"
      : "signal-tag signal-neutral";
  return `<span class="${cls}">${escapeHtml(val)}</span>`;
}

function verdictClass(v) {
  const key = String(v || "neutral").replace(/_/g, "-");
  return `verdict-${key}`;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
