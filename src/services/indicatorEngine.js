export function buildTechnicalPack(rates) {
  const close = rates.map((v) => Number(v)).filter((v) => Number.isFinite(v));
  const latest = close.length ? close[close.length - 1] : null;

  const sma5 = sma(close, 5);
  const sma10 = sma(close, 10);
  const sma20 = sma(close, 20);
  const sma50 = sma(close, 50);

  const ema9 = ema(close, 9);
  const ema21 = ema(close, 21);
  const ema50 = ema(close, 50);
  const wma20 = wma(close, 20);

  const rsi14 = rsi(close, 14);
  const stochRsi14 = stochRsi(close, 14);

  const macdPack = macd(close, 12, 26, 9);
  const bb20 = bollinger(close, 20, 2);

  const roc12 = roc(close, 12);
  const mom10 = momentum(close, 10);
  const std20 = stdDev(close, 20);
  const z20 = zScore(close, 20);

  const support20 = rollingMin(close, 20);
  const resistance20 = rollingMax(close, 20);
  const returns = dailyReturns(close);
  const sharpeLike = returns.length ? mean(returns) / (stdDevRaw(returns) || 1) : null;

  const signalScore = scoreSignal({
    latest,
    sma20,
    sma50,
    ema21,
    ema50,
    rsi14,
    stochRsi14,
    macdLine: macdPack.macdLine,
    macdSignal: macdPack.signal,
    roc12,
    mom10,
    z20
  });

  return {
    latest,
    sma5,
    sma10,
    sma20,
    sma50,
    ema9,
    ema21,
    ema50,
    wma20,
    rsi14,
    stochRsi14,
    macd: macdPack.macdLine,
    macdSignal: macdPack.signal,
    macdHistogram: macdPack.histogram,
    bollingerMiddle: bb20.middle,
    bollingerUpper: bb20.upper,
    bollingerLower: bb20.lower,
    bollingerBandwidth: bb20.bandwidth,
    bollingerPercentB: bb20.percentB,
    roc12,
    momentum10: mom10,
    stdDev20: std20,
    zScore20: z20,
    support20,
    resistance20,
    sharpeLike,
    signalScore,
    signal: scoreToSignal(signalScore)
  };
}

export function buildOhlcTechnicalPack(ohlcRows) {
  const rows = Array.isArray(ohlcRows) ? ohlcRows : [];
  if (!rows.length) {
    return {
      atr14: null,
      adx14: null,
      cci20: null,
      stochasticK14: null,
      stochasticD3: null
    };
  }

  const atr14 = atr(rows, 14);
  const adx14 = adx(rows, 14);
  const cci20 = cci(rows, 20);
  const stoch = stochastic(rows, 14, 3);

  return {
    atr14,
    adx14,
    cci20,
    stochasticK14: stoch.k,
    stochasticD3: stoch.d
  };
}

function scoreSignal(input) {
  let score = 50;

  if (isNum(input.latest) && isNum(input.sma20)) {
    score += input.latest > input.sma20 ? 6 : -6;
  }
  if (isNum(input.sma20) && isNum(input.sma50)) {
    score += input.sma20 > input.sma50 ? 8 : -8;
  }
  if (isNum(input.ema21) && isNum(input.ema50)) {
    score += input.ema21 > input.ema50 ? 7 : -7;
  }

  if (isNum(input.rsi14)) {
    if (input.rsi14 >= 70) {
      score -= 4;
    } else if (input.rsi14 <= 30) {
      score += 4;
    } else if (input.rsi14 >= 55) {
      score += 3;
    } else if (input.rsi14 <= 45) {
      score -= 3;
    }
  }

  if (isNum(input.stochRsi14)) {
    if (input.stochRsi14 > 0.8) {
      score -= 3;
    } else if (input.stochRsi14 < 0.2) {
      score += 3;
    }
  }

  if (isNum(input.macdLine) && isNum(input.macdSignal)) {
    score += input.macdLine > input.macdSignal ? 7 : -7;
  }

  if (isNum(input.roc12)) {
    score += input.roc12 > 0 ? 5 : -5;
  }
  if (isNum(input.mom10)) {
    score += input.mom10 > 0 ? 4 : -4;
  }

  if (isNum(input.z20)) {
    if (input.z20 >= 2) {
      score -= 5;
    } else if (input.z20 <= -2) {
      score += 5;
    }
  }

  return clamp(score, 0, 100);
}

function scoreToSignal(score) {
  if (!isNum(score)) {
    return "neutral";
  }
  if (score >= 75) {
    return "strong_bullish";
  }
  if (score >= 60) {
    return "bullish";
  }
  if (score >= 40) {
    return "neutral";
  }
  if (score >= 25) {
    return "bearish";
  }
  return "strong_bearish";
}

function sma(values, period) {
  if (values.length < period) {
    return null;
  }
  return mean(values.slice(-period));
}

function ema(values, period) {
  if (values.length < period) {
    return null;
  }
  const k = 2 / (period + 1);
  let acc = mean(values.slice(0, period));
  for (let i = period; i < values.length; i++) {
    acc = values[i] * k + acc * (1 - k);
  }
  return acc;
}

function wma(values, period) {
  if (values.length < period) {
    return null;
  }
  const window = values.slice(-period);
  const weightSum = (period * (period + 1)) / 2;
  let weighted = 0;
  for (let i = 0; i < window.length; i++) {
    weighted += window[i] * (i + 1);
  }
  return weighted / weightSum;
}

function rsi(values, period) {
  if (values.length <= period) {
    return null;
  }
  let gains = 0;
  let losses = 0;
  for (let i = values.length - period; i < values.length; i++) {
    const delta = values[i] - values[i - 1];
    if (delta > 0) {
      gains += delta;
    } else {
      losses += Math.abs(delta);
    }
  }
  if (losses === 0) {
    return 100;
  }
  const rs = gains / losses;
  return 100 - 100 / (1 + rs);
}

function stochRsi(values, period) {
  if (values.length < period + 1) {
    return null;
  }
  const rsiSeries = [];
  for (let i = period; i < values.length; i++) {
    const window = values.slice(0, i + 1);
    const value = rsi(window, period);
    if (isNum(value)) {
      rsiSeries.push(value);
    }
  }
  if (rsiSeries.length < period) {
    return null;
  }
  const window = rsiSeries.slice(-period);
  const min = Math.min(...window);
  const max = Math.max(...window);
  if (max === min) {
    return 0.5;
  }
  return (window[window.length - 1] - min) / (max - min);
}

function macd(values, fast, slow, signalPeriod) {
  if (values.length < slow + signalPeriod) {
    return { macdLine: null, signal: null, histogram: null };
  }

  const fastSeries = emaSeries(values, fast);
  const slowSeries = emaSeries(values, slow);
  const macdSeries = [];

  for (let i = 0; i < values.length; i++) {
    if (isNum(fastSeries[i]) && isNum(slowSeries[i])) {
      macdSeries[i] = fastSeries[i] - slowSeries[i];
    } else {
      macdSeries[i] = null;
    }
  }

  const compact = macdSeries.filter((v) => isNum(v));
  const signal = ema(compact, signalPeriod);
  const macdLine = compact.length ? compact[compact.length - 1] : null;
  const histogram = isNum(macdLine) && isNum(signal) ? macdLine - signal : null;

  return { macdLine, signal, histogram };
}

function bollinger(values, period, mult) {
  if (values.length < period) {
    return {
      middle: null,
      upper: null,
      lower: null,
      bandwidth: null,
      percentB: null
    };
  }
  const window = values.slice(-period);
  const middle = mean(window);
  const sd = stdDevRaw(window);
  const upper = middle + mult * sd;
  const lower = middle - mult * sd;
  const latest = window[window.length - 1];
  const bandwidth = middle === 0 ? null : (upper - lower) / middle;
  const percentB = upper === lower ? 0.5 : (latest - lower) / (upper - lower);

  return { middle, upper, lower, bandwidth, percentB };
}

function roc(values, period) {
  if (values.length <= period) {
    return null;
  }
  const latest = values[values.length - 1];
  const base = values[values.length - 1 - period];
  if (base === 0) {
    return null;
  }
  return ((latest - base) / base) * 100;
}

function momentum(values, period) {
  if (values.length <= period) {
    return null;
  }
  return values[values.length - 1] - values[values.length - 1 - period];
}

function stdDev(values, period) {
  if (values.length < period) {
    return null;
  }
  return stdDevRaw(values.slice(-period));
}

function zScore(values, period) {
  if (values.length < period) {
    return null;
  }
  const window = values.slice(-period);
  const avg = mean(window);
  const sd = stdDevRaw(window);
  if (sd === 0) {
    return 0;
  }
  return (window[window.length - 1] - avg) / sd;
}

function rollingMin(values, period) {
  if (values.length < period) {
    return null;
  }
  return Math.min(...values.slice(-period));
}

function rollingMax(values, period) {
  if (values.length < period) {
    return null;
  }
  return Math.max(...values.slice(-period));
}

function dailyReturns(values) {
  const out = [];
  for (let i = 1; i < values.length; i++) {
    const prev = values[i - 1];
    const curr = values[i];
    if (prev !== 0) {
      out.push((curr - prev) / prev);
    }
  }
  return out;
}

function emaSeries(values, period) {
  const series = new Array(values.length).fill(null);
  if (values.length < period) {
    return series;
  }

  const k = 2 / (period + 1);
  let prev = mean(values.slice(0, period));
  series[period - 1] = prev;

  for (let i = period; i < values.length; i++) {
    prev = values[i] * k + prev * (1 - k);
    series[i] = prev;
  }

  return series;
}

function mean(arr) {
  if (!arr.length) {
    return 0;
  }
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function stdDevRaw(arr) {
  if (!arr.length) {
    return 0;
  }
  const avg = mean(arr);
  const variance = arr.reduce((acc, v) => acc + (v - avg) ** 2, 0) / arr.length;
  return Math.sqrt(variance);
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function isNum(v) {
  return typeof v === "number" && Number.isFinite(v);
}

function trueRange(curr, prevClose) {
  const a = curr.high - curr.low;
  const b = prevClose === null ? a : Math.abs(curr.high - prevClose);
  const c = prevClose === null ? a : Math.abs(curr.low - prevClose);
  return Math.max(a, b, c);
}

function atr(rows, period) {
  if (rows.length < period + 1) {
    return null;
  }
  const trs = [];
  for (let i = 0; i < rows.length; i++) {
    const prevClose = i === 0 ? null : rows[i - 1].close;
    trs.push(trueRange(rows[i], prevClose));
  }

  let value = mean(trs.slice(0, period));
  for (let i = period; i < trs.length; i++) {
    value = ((value * (period - 1)) + trs[i]) / period;
  }
  return value;
}

function adx(rows, period) {
  if (rows.length < period * 2) {
    return null;
  }

  const tr = [];
  const plusDM = [];
  const minusDM = [];

  tr.push(0);
  plusDM.push(0);
  minusDM.push(0);

  for (let i = 1; i < rows.length; i++) {
    const upMove = rows[i].high - rows[i - 1].high;
    const downMove = rows[i - 1].low - rows[i].low;
    plusDM.push(upMove > downMove && upMove > 0 ? upMove : 0);
    minusDM.push(downMove > upMove && downMove > 0 ? downMove : 0);
    tr.push(trueRange(rows[i], rows[i - 1].close));
  }

  let trN = sum(tr.slice(1, period + 1));
  let plusN = sum(plusDM.slice(1, period + 1));
  let minusN = sum(minusDM.slice(1, period + 1));

  const dxSeries = [];
  for (let i = period + 1; i < rows.length; i++) {
    trN = trN - trN / period + tr[i];
    plusN = plusN - plusN / period + plusDM[i];
    minusN = minusN - minusN / period + minusDM[i];

    const plusDI = trN === 0 ? 0 : (100 * plusN) / trN;
    const minusDI = trN === 0 ? 0 : (100 * minusN) / trN;
    const denom = plusDI + minusDI;
    const dx = denom === 0 ? 0 : (100 * Math.abs(plusDI - minusDI)) / denom;
    dxSeries.push(dx);
  }

  if (dxSeries.length < period) {
    return null;
  }

  let adxValue = mean(dxSeries.slice(0, period));
  for (let i = period; i < dxSeries.length; i++) {
    adxValue = ((adxValue * (period - 1)) + dxSeries[i]) / period;
  }
  return adxValue;
}

function cci(rows, period) {
  if (rows.length < period) {
    return null;
  }
  const window = rows.slice(-period);
  const typicalPrices = window.map((r) => (r.high + r.low + r.close) / 3);
  const smaTp = mean(typicalPrices);
  const meanDeviation = mean(typicalPrices.map((tp) => Math.abs(tp - smaTp)));
  if (meanDeviation === 0) {
    return 0;
  }
  const currentTp = typicalPrices[typicalPrices.length - 1];
  return (currentTp - smaTp) / (0.015 * meanDeviation);
}

function stochastic(rows, period, dPeriod) {
  if (rows.length < period) {
    return { k: null, d: null };
  }

  const kSeries = [];
  for (let i = period - 1; i < rows.length; i++) {
    const window = rows.slice(i - period + 1, i + 1);
    const high = Math.max(...window.map((r) => r.high));
    const low = Math.min(...window.map((r) => r.low));
    const close = rows[i].close;
    const k = high === low ? 50 : ((close - low) / (high - low)) * 100;
    kSeries.push(k);
  }

  const k = kSeries.length ? kSeries[kSeries.length - 1] : null;
  const d = kSeries.length >= dPeriod ? mean(kSeries.slice(-dPeriod)) : null;
  return { k, d };
}

function sum(arr) {
  return arr.reduce((acc, v) => acc + v, 0);
}
