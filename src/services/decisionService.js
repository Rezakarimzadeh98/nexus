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

export function buildDecisionScore({ summary, forecast, news }) {
  const technicalScore = Number(summary?.technicalOverview?.marketScore ?? 50);

  const newsRaw = Number(news?.sentiment?.averageScore ?? 0);
  const newsScore = clamp(50 + newsRaw * 10, 0, 100);

  const forecastItems = forecast?.items || [];
  const forecastScores = [];

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
    const score = clamp(50 + changePct * 8, 0, 100);
    forecastScores.push(score);
  }

  const forecastScore = forecastScores.length
    ? forecastScores.reduce((a, b) => a + b, 0) / forecastScores.length
    : 50;

  const compositeScore =
    technicalScore * 0.5 +
    forecastScore * 0.3 +
    newsScore * 0.2;

  return {
    technicalScore,
    forecastScore,
    newsScore,
    compositeScore,
    verdict: verdict(compositeScore)
  };
}
