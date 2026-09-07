function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function verdict(score) {
  if (score >= 75) {
    return "strong_buy_bias";
  }
  if (score >= 60) {
    return "buy_bias";
  }
  if (score >= 40) {
    return "neutral";
  }
  if (score >= 25) {
    return "sell_bias";
  }
  return "strong_sell_bias";
}

function getWeights(mode) {
  const key = String(mode || "hybrid").toLowerCase();
  if (key === "technical") {
    return { technical: 0.7, quant: 0.2, fundamental: 0.1 };
  }
  if (key === "fundamental") {
    return { technical: 0.2, quant: 0.2, fundamental: 0.6 };
  }
  if (key === "quant") {
    return { technical: 0.2, quant: 0.65, fundamental: 0.15 };
  }
  return { technical: 0.45, quant: 0.35, fundamental: 0.2 };
}

export function buildDecisionScore({ summary, forecast, news, mode = "hybrid" }) {
  const technicalScore = Number(summary?.technicalOverview?.marketScore ?? 50);

  const newsRaw = Number(news?.sentiment?.averageScore ?? 0);
  const newsScore = clamp(50 + newsRaw * 10, 0, 100);

  const forecastItems = forecast?.items || [];
  const directionScores = [];
  const qualityScores = [];

  for (const item of forecastItems) {
    if (!item.ok || !item.forecast?.length) {
      continue;
    }
    const targetStat = (summary?.stats || []).find((s) => s.target === item.target);
    if (!targetStat || !targetStat.latestRate) {
      continue;
    }

    const next = item.forecast[0].predicted;
    const latest = targetStat.latestRate;
    const changePct = latest === 0 ? 0 : ((next - latest) / latest) * 100;
    directionScores.push(clamp(50 + changePct * 8, 0, 100));

    const mape = Number(item.metrics?.mape);
    if (Number.isFinite(mape)) {
      qualityScores.push(clamp(100 - mape * 10, 0, 100));
    }
  }

  const forecastDirectionScore = directionScores.length
    ? directionScores.reduce((a, b) => a + b, 0) / directionScores.length
    : 50;

  const forecastQualityScore = qualityScores.length
    ? qualityScores.reduce((a, b) => a + b, 0) / qualityScores.length
    : 50;

  const sharpeValues = (summary?.stats || [])
    .map((s) => Number(s.technical?.sharpeLike))
    .filter((x) => Number.isFinite(x));
  const avgSharpe = sharpeValues.length
    ? sharpeValues.reduce((a, b) => a + b, 0) / sharpeValues.length
    : 0;
  const riskAdjustedScore = clamp(50 + avgSharpe * 20, 0, 100);

  const quantitativeScore = clamp((forecastDirectionScore * 0.5) + (forecastQualityScore * 0.3) + (riskAdjustedScore * 0.2), 0, 100);
  const fundamentalScore = clamp(newsScore, 0, 100);

  const weights = getWeights(mode);

  const compositeScore =
    technicalScore * weights.technical +
    quantitativeScore * weights.quant +
    fundamentalScore * weights.fundamental;

  return {
    technicalScore,
    forecastScore: forecastDirectionScore,
    newsScore: fundamentalScore,
    quantitativeScore,
    forecastQualityScore,
    riskAdjustedScore,
    analysisMode: String(mode || "hybrid").toLowerCase(),
    weights,
    compositeScore,
    verdict: verdict(compositeScore)
  };
}
