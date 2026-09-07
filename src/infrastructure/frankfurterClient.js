import { FX_API_BASE } from "../config/constants.js";
import { fetchWithTimeout } from "./httpClient.js";

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

export async function fetchTimeseries({ base, targets, days }) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days + 1);

  const from = formatDate(start);
  const to = formatDate(end);
  const toQuery = targets.join(",");
  const url = `${FX_API_BASE}/${from}..${to}?from=${base}&to=${toQuery}`;

  const response = await fetchWithTimeout(url, {
    headers: { Accept: "application/json" },
    timeoutMs: 7000,
    retries: 1
  });

  if (!response.ok) {
    throw new Error(`FX provider error: ${response.status}`);
  }

  const payload = await response.json();
  const rows = [];
  for (const [date, rates] of Object.entries(payload.rates || {})) {
    for (const [target, rawRate] of Object.entries(rates || {})) {
      const rate = Number(rawRate);
      if (Number.isFinite(rate) && rate > 0) {
        rows.push({ date, base, target, rate, source: "online" });
      }
    }
  }

  return rows;
}
