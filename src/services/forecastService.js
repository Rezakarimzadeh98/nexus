import { MIN_FORECAST_POINTS } from "../config/constants.js";

export function buildForecastBundle(records, horizon) {
  const grouped = groupByTarget(records);
  const forecasts = [];

  for (const [target, points] of grouped.entries()) {
    const sorted = points.sort((a, b) => (a.date > b.date ? 1 : -1));
    const dates = sorted.map((x) => x.date);
    const values = sorted.map((x) => Number(x.rate));

    if (values.length < MIN_FORECAST_POINTS) {
      forecasts.push({
        target,
        ok: false,
        reason: `داده برای پیش بینی کافی نیست. حداقل ${MIN_FORECAST_POINTS} نقطه لازم است.`,
        dataPoints: values.length,
        forecast: [],
        metrics: null,
        model: "holt-linear"
      });
      continue;
    }

    const alpha = 0.35;
    const beta = 0.2;
    const model = fitHolt(values, alpha, beta);
    const future = forecastHolt(model, horizon);
    const sigma = Math.max(stdDev(model.residuals), 1e-8);
    const lastDate = dates[dates.length - 1];
    const forecast = future.map((value, idx) => {
      const step = idx + 1;
      const band = 1.96 * sigma * Math.sqrt(step);
      return {
        date: plusDays(lastDate, step),
        predicted: value,
        lower95: Math.max(value - band, 0),
        upper95: value + band
      };
    });

    const metrics = backtestHolt(values, alpha, beta);

    forecasts.push({
      target,
      ok: true,
      reason: null,
      dataPoints: values.length,
      forecast,
      metrics,
      model: "holt-linear"
    });
  }

  return {
    generatedAt: new Date().toISOString(),
    horizon,
    items: forecasts
  };
}

function fitHolt(values, alpha, beta) {
  const residuals = [];
  let level = values[0];
  let trend = values[1] - values[0];

  for (let i = 1; i < values.length; i++) {
    const actual = values[i];
    const prevLevel = level;
    const prevTrend = trend;
    const prediction = prevLevel + prevTrend;
    residuals.push(actual - prediction);

    level = alpha * actual + (1 - alpha) * (prevLevel + prevTrend);
    trend = beta * (level - prevLevel) + (1 - beta) * prevTrend;
  }

  return { level, trend, residuals };
}

function forecastHolt(model, horizon) {
  const out = [];
  for (let m = 1; m <= horizon; m++) {
    out.push(model.level + m * model.trend);
  }
  return out;
}

function backtestHolt(values, alpha, beta) {
  const minTrain = Math.min(30, Math.max(12, Math.floor(values.length * 0.6)));
  const actuals = [];
  const preds = [];

  for (let i = minTrain; i < values.length; i++) {
    const train = values.slice(0, i);
    const model = fitHolt(train, alpha, beta);
    const pred = forecastHolt(model, 1)[0];
    preds.push(pred);
    actuals.push(values[i]);
  }

  return {
    mae: mae(actuals, preds),
    rmse: rmse(actuals, preds),
    mape: mape(actuals, preds)
  };
}

function groupByTarget(records) {
  const map = new Map();
  for (const row of records) {
    const arr = map.get(row.target) || [];
    arr.push(row);
    map.set(row.target, arr);
  }
  return map;
}

function plusDays(isoDate, days) {
  const d = new Date(isoDate);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function mae(actuals, preds) {
  if (!actuals.length || actuals.length !== preds.length) {
    return null;
  }
  let sum = 0;
  for (let i = 0; i < actuals.length; i++) {
    sum += Math.abs(actuals[i] - preds[i]);
  }
  return sum / actuals.length;
}

function rmse(actuals, preds) {
  if (!actuals.length || actuals.length !== preds.length) {
    return null;
  }
  let sum = 0;
  for (let i = 0; i < actuals.length; i++) {
    const e = actuals[i] - preds[i];
    sum += e * e;
  }
  return Math.sqrt(sum / actuals.length);
}

function mape(actuals, preds) {
  if (!actuals.length || actuals.length !== preds.length) {
    return null;
  }
  let sum = 0;
  let count = 0;
  for (let i = 0; i < actuals.length; i++) {
    if (actuals[i] !== 0) {
      sum += Math.abs((actuals[i] - preds[i]) / actuals[i]);
      count += 1;
    }
  }
  if (!count) {
    return null;
  }
  return (sum / count) * 100;
}

function stdDev(values) {
  if (!values.length) {
    return 0;
  }
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((acc, v) => acc + (v - avg) ** 2, 0) / values.length;
  return Math.sqrt(variance);
}
