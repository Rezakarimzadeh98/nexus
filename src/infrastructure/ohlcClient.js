import { fetchWithTimeout, mapWithConcurrency } from "./httpClient.js";

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function unixSeconds(date) {
  return Math.floor(date.getTime() / 1000);
}

function parseCsv(csv) {
  const lines = String(csv || "")
    .trim()
    .split(/\r?\n/)
    .filter(Boolean);
  if (lines.length < 2) {
    return [];
  }

  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const [date, open, high, low, close] = lines[i].split(",");
    const item = {
      date: String(date || "").trim(),
      open: Number(open),
      high: Number(high),
      low: Number(low),
      close: Number(close)
    };
    if (
      /^\d{4}-\d{2}-\d{2}$/.test(item.date) &&
      Number.isFinite(item.open) &&
      Number.isFinite(item.high) &&
      Number.isFinite(item.low) &&
      Number.isFinite(item.close)
    ) {
      rows.push(item);
    }
  }

  return rows;
}

async function fetchStooqSymbol(symbol) {
  const url = `https://stooq.com/q/d/l/?s=${symbol.toLowerCase()}&i=d`;
  const response = await fetchWithTimeout(url, { timeoutMs: 7000, retries: 1 });
  if (!response.ok) {
    return [];
  }
  const csv = await response.text();
  return parseCsv(csv);
}

async function fetchYahooSymbol(symbol, fromDate, toDate) {
  const period1 = unixSeconds(new Date(`${fromDate}T00:00:00Z`));
  const period2 = unixSeconds(new Date(`${toDate}T23:59:59Z`));
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(
    symbol
  )}?period1=${period1}&period2=${period2}&interval=1d&events=history`;

  const response = await fetchWithTimeout(url, {
    headers: { Accept: "application/json" },
    timeoutMs: 7000,
    retries: 1
  });
  if (!response.ok) {
    return [];
  }

  const payload = await response.json();
  const result = payload?.chart?.result?.[0];
  const ts = result?.timestamp || [];
  const quote = result?.indicators?.quote?.[0] || {};
  const opens = quote.open || [];
  const highs = quote.high || [];
  const lows = quote.low || [];
  const closes = quote.close || [];

  const rows = [];
  for (let i = 0; i < ts.length; i++) {
    const open = Number(opens[i]);
    const high = Number(highs[i]);
    const low = Number(lows[i]);
    const close = Number(closes[i]);
    if ([open, high, low, close].every((v) => Number.isFinite(v))) {
      const date = new Date(ts[i] * 1000).toISOString().slice(0, 10);
      rows.push({ date, open, high, low, close });
    }
  }

  return rows.sort((a, b) => (a.date > b.date ? 1 : -1));
}

function invertRows(rows) {
  return rows.map((r) => ({
    date: r.date,
    open: r.open !== 0 ? 1 / r.open : null,
    high: r.low !== 0 ? 1 / r.low : null,
    low: r.high !== 0 ? 1 / r.high : null,
    close: r.close !== 0 ? 1 / r.close : null
  })).filter((r) => Number.isFinite(r.open) && Number.isFinite(r.high) && Number.isFinite(r.low) && Number.isFinite(r.close));
}

export async function fetchOhlcForPairs({ base, targets, days }) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days + 1);
  const from = formatDate(start);
  const to = formatDate(end);

  const entries = await mapWithConcurrency(targets, 3, async (target) => {
    try {
      const direct = `${base}${target}`;
      const inverse = `${target}${base}`;

      const yahooDirect = await fetchYahooSymbol(`${direct}=X`, from, to);
      if (yahooDirect.length) {
        return [target, yahooDirect];
      }

      const yahooInverse = await fetchYahooSymbol(`${inverse}=X`, from, to);
      if (yahooInverse.length) {
        return [target, invertRows(yahooInverse)];
      }

      const directRows = await fetchStooqSymbol(direct);
      if (directRows.length) {
        const scoped = directRows.filter((r) => r.date >= from).sort((a, b) => (a.date > b.date ? 1 : -1));
        return [target, scoped];
      }

      const inverseRows = await fetchStooqSymbol(inverse);
      if (inverseRows.length) {
        const scoped = invertRows(inverseRows).filter((r) => r.date >= from).sort((a, b) => (a.date > b.date ? 1 : -1));
        return [target, scoped];
      }

      return [target, []];
    } catch {
      return [target, []];
    }
  });

  return new Map(entries);
}
