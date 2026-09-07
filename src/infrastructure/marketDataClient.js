import { fetchWithTimeout, mapWithConcurrency } from "./httpClient.js";

const MARKET_DEFAULTS = {
  forex: ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"],
  stocks: ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"],
  crypto: ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"],
  commodities: ["GC=F", "CL=F", "SI=F", "NG=F", "HG=F"],
  all: [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AAPL",
    "MSFT",
    "NVDA",
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "GC=F",
    "CL=F"
  ]
};

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function unixSeconds(date) {
  return Math.floor(date.getTime() / 1000);
}

function normalizeSymbol(input) {
  return String(input || "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "");
}

function isAllowedSymbol(symbol) {
  return /^[A-Z0-9.=\-^]+$/.test(symbol);
}

function toTargetLabel(symbol) {
  return symbol.replace(/=X$/i, "");
}

async function fetchYahooHistory(symbol, fromDate, toDate) {
  const period1 = unixSeconds(new Date(`${fromDate}T00:00:00Z`));
  const period2 = unixSeconds(new Date(`${toDate}T23:59:59Z`));
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(
    symbol
  )}?period1=${period1}&period2=${period2}&interval=1d&events=history`;

  const response = await fetchWithTimeout(url, {
    headers: { Accept: "application/json" },
    timeoutMs: 8000,
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
  for (let i = 0; i < ts.length; i += 1) {
    const open = Number(opens[i]);
    const high = Number(highs[i]);
    const low = Number(lows[i]);
    const close = Number(closes[i]);
    if ([open, high, low, close].every((v) => Number.isFinite(v) && v > 0)) {
      const date = new Date(ts[i] * 1000).toISOString().slice(0, 10);
      rows.push({ date, open, high, low, close });
    }
  }

  return rows.sort((a, b) => (a.date > b.date ? 1 : -1));
}

export function resolveSymbols({ market, symbols }) {
  const parsed = String(symbols || "")
    .split(",")
    .map(normalizeSymbol)
    .filter(Boolean)
    .filter(isAllowedSymbol);

  if (parsed.length) {
    return Array.from(new Set(parsed)).slice(0, 20);
  }

  const defaults = MARKET_DEFAULTS[market] || MARKET_DEFAULTS.forex;
  return [...defaults];
}

export async function fetchMarketSeries({ market, symbols, days }) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days + 1);
  const from = formatDate(start);
  const to = formatDate(end);

  const entries = await mapWithConcurrency(symbols, 4, async (symbol) => {
    try {
      const rows = await fetchYahooHistory(symbol, from, to);
      return [symbol, rows];
    } catch {
      return [symbol, []];
    }
  });

  const records = [];
  const ohlcByTarget = new Map();

  for (const [symbol, rows] of entries) {
    const target = toTargetLabel(symbol);
    ohlcByTarget.set(target, rows);
    for (const row of rows) {
      records.push({
        date: row.date,
        base: market === "forex" ? "USD" : market.toUpperCase(),
        target,
        rate: row.close,
        source: "online"
      });
    }
  }

  records.sort((a, b) => (a.date > b.date ? 1 : -1));
  return { records, ohlcByTarget };
}
