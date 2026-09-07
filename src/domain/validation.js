import { ISO_CURRENCY, MAX_DAYS, MAX_TARGETS, MAX_FORECAST_HORIZON } from "../config/constants.js";

function ensureCurrency(code, label) {
  const normalized = String(code || "").trim().toUpperCase();
  if (!ISO_CURRENCY.test(normalized)) {
    throw new Error(`${label} نامعتبر است. باید کد سه حرفی باشد.`);
  }
  return normalized;
}

export function validateTimeseriesQuery(query) {
  const base = ensureCurrency(query.base, "ارز مبدا");
  const days = Number(query.days || 30);
  if (!Number.isInteger(days) || days < 1 || days > MAX_DAYS) {
    throw new Error(`days باید بین 1 تا ${MAX_DAYS} باشد.`);
  }

  const targets = String(query.targets || "")
    .split(",")
    .map((x) => x.trim().toUpperCase())
    .filter(Boolean);

  if (!targets.length) {
    throw new Error("حداقل یک ارز مقصد لازم است.");
  }

  if (targets.length > MAX_TARGETS) {
    throw new Error(`حداکثر ${MAX_TARGETS} ارز مقصد مجاز است.`);
  }

  const uniqueTargets = Array.from(new Set(targets.map((t) => ensureCurrency(t, "ارز مقصد")))).filter((t) => t !== base);
  if (!uniqueTargets.length) {
    throw new Error("ارز مقصد نباید فقط برابر ارز مبدا باشد.");
  }

  return { base, targets: uniqueTargets, days };
}

export function validateManualRecord(payload) {
  const date = String(payload.date || "").trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    throw new Error("date نامعتبر است. فرمت باید YYYY-MM-DD باشد.");
  }

  const base = ensureCurrency(payload.base, "base");
  const target = ensureCurrency(payload.target, "target");
  if (base === target) {
    throw new Error("base و target نباید یکسان باشند.");
  }

  const rate = Number(payload.rate);
  if (!Number.isFinite(rate) || rate <= 0) {
    throw new Error("rate باید عدد مثبت باشد.");
  }

  return {
    date,
    base,
    target,
    rate,
    source: "manual"
  };
}

export function validateForecastQuery(query) {
  const baseData = validateTimeseriesQuery(query);
  const horizon = Number(query.horizon || 7);
  if (!Number.isInteger(horizon) || horizon < 1 || horizon > MAX_FORECAST_HORIZON) {
    throw new Error(`horizon باید بین 1 تا ${MAX_FORECAST_HORIZON} باشد.`);
  }

  return {
    ...baseData,
    horizon
  };
}

export function validateDecisionQuery(query) {
  const base = validateForecastQuery(query);
  const newsQuery = String(query.newsQuery || "forex market").trim();
  const newsMax = Number(query.newsMax || 20);

  if (!newsQuery) {
    throw new Error("newsQuery الزامی است.");
  }
  if (!Number.isInteger(newsMax) || newsMax < 1 || newsMax > 50) {
    throw new Error("newsMax باید بین 1 تا 50 باشد.");
  }

  return {
    ...base,
    newsQuery,
    newsMax
  };
}

export function validateMarketQuery(query) {
  const market = String(query.market || "forex").trim().toLowerCase();
  const allowed = new Set(["forex", "stocks", "crypto", "commodities", "all"]);
  if (!allowed.has(market)) {
    throw new Error("market نامعتبر است. مقادیر مجاز: forex, stocks, crypto, commodities, all");
  }

  const days = Number(query.days || 30);
  if (!Number.isInteger(days) || days < 1 || days > MAX_DAYS) {
    throw new Error(`days باید بین 1 تا ${MAX_DAYS} باشد.`);
  }

  const symbols = String(query.symbols || "")
    .split(",")
    .map((x) => x.trim().toUpperCase())
    .filter(Boolean);

  if (symbols.length > 20) {
    throw new Error("حداکثر 20 نماد مجاز است.");
  }

  return { market, symbols, days };
}
