import { buildOhlcTechnicalPack, buildTechnicalPack } from "./indicatorEngine.js";

export function mergeRecords(onlineRows, manualRows) {
  const map = new Map();
  for (const row of [...onlineRows, ...manualRows]) {
    const key = `${row.date}|${row.base}|${row.target}|${row.source}`;
    map.set(key, row);
  }
  return Array.from(map.values()).sort((a, b) => (a.date > b.date ? 1 : -1));
}

export function summarize(records, ohlcByTarget = new Map()) {
  if (!records.length) {
    return {
      kpis: {
        totalRecords: 0,
        onlineRecords: 0,
        manualRecords: 0,
        latestDate: null,
        latestAverageRate: null
      },
      stats: [],
      technicalOverview: {
        strongBullishTargets: 0,
        bullishTargets: 0,
        bearishTargets: 0,
        strongBearishTargets: 0,
        neutralTargets: 0,
        marketScore: 50
      }
    };
  }

  const latestDate = records.reduce((max, row) => (row.date > max ? row.date : max), records[0].date);
  const latestRows = records.filter((x) => x.date === latestDate);
  const latestAverageRate = mean(latestRows.map((x) => Number(x.rate)));

  const byTarget = new Map();
  for (const row of records) {
    const arr = byTarget.get(row.target) || [];
    arr.push(Number(row.rate));
    byTarget.set(row.target, arr);
  }

  const stats = Array.from(byTarget.entries()).map(([target, rates]) => {
    const technical = buildTechnicalPack(rates);
    const ohlcRows = ohlcByTarget.get(target) || [];
    const ohlcTechnical = buildOhlcTechnicalPack(ohlcRows);

    return {
      target,
      averageRate: mean(rates),
      minRate: Math.min(...rates),
      maxRate: Math.max(...rates),
      volatility: Math.max(...rates) - Math.min(...rates),
      latestRate: rates[rates.length - 1],
      technical: {
        ...technical,
        ...ohlcTechnical,
        ohlcPoints: ohlcRows.length
      }
    };
  });

  const marketScore = mean(
    stats.map((s) => (typeof s.technical.signalScore === "number" ? s.technical.signalScore : 50))
  );

  const technicalOverview = {
    strongBullishTargets: stats.filter((s) => s.technical.signal === "strong_bullish").length,
    bullishTargets: stats.filter((s) => s.technical.signal === "bullish").length,
    bearishTargets: stats.filter((s) => s.technical.signal === "bearish").length,
    strongBearishTargets: stats.filter((s) => s.technical.signal === "strong_bearish").length,
    neutralTargets: stats.filter((s) => s.technical.signal === "neutral").length,
    marketScore
  };

  return {
    kpis: {
      totalRecords: records.length,
      onlineRecords: records.filter((x) => x.source === "online").length,
      manualRecords: records.filter((x) => x.source === "manual").length,
      latestDate,
      latestAverageRate
    },
    stats,
    technicalOverview
  };
}

function mean(arr) {
  if (!arr.length) {
    return 0;
  }
  return arr.reduce((acc, v) => acc + v, 0) / arr.length;
}
