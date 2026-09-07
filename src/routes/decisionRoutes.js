import { Router } from "express";
import { validateDecisionQuery } from "../domain/validation.js";
import { fetchTimeseries } from "../infrastructure/frankfurterClient.js";
import { fetchOhlcForPairs } from "../infrastructure/ohlcClient.js";
import { getManualRecords } from "../infrastructure/manualRecordStore.js";
import { mergeRecords, summarize } from "../services/analyticsService.js";
import { fetchNewsAndAnalyze } from "../services/newsAnalysisService.js";
import { buildForecastBundle } from "../services/forecastService.js";
import { buildDecisionScore } from "../services/decisionService.js";

const decisionRouter = Router();

decisionRouter.get("/score", async (req, res) => {
  try {
    const query = validateDecisionQuery(req.query);

    const [onlineRowsResult, manualRowsResult, ohlcByTargetResult, newsResult] = await Promise.allSettled([
      fetchTimeseries(query),
      getManualRecords(),
      fetchOhlcForPairs(query),
      fetchNewsAndAnalyze({ query: query.newsQuery, max: query.newsMax })
    ]);

    const onlineRows = onlineRowsResult.status === "fulfilled" ? onlineRowsResult.value : [];
    const manualRows = manualRowsResult.status === "fulfilled" ? manualRowsResult.value : [];
    const ohlcByTarget = ohlcByTargetResult.status === "fulfilled" ? ohlcByTargetResult.value : new Map();
    const news = newsResult.status === "fulfilled"
      ? newsResult.value
      : {
          query: query.newsQuery,
          source: "google-news-rss",
          totalArticles: 0,
          sentiment: { positive: 0, negative: 0, neutral: 0, averageScore: 0 },
          articles: []
        };

    if (!onlineRows.length && onlineRowsResult.status !== "fulfilled") {
      throw new Error("Live FX provider is temporarily unavailable.");
    }

    const scopedManualRows = manualRows.filter(
      (row) => row.base === query.base && query.targets.includes(row.target)
    );

    const records = mergeRecords(onlineRows, scopedManualRows);
    const summary = summarize(records, ohlcByTarget);
    const forecast = buildForecastBundle(records, query.horizon);
    const score = buildDecisionScore({ summary, forecast, news, mode: query.analysisMode });
    const warnings = [];
    if (ohlcByTargetResult.status !== "fulfilled") {
      warnings.push("OHLC provider unavailable; technical OHLC enrichments were skipped.");
    }
    if (newsResult.status !== "fulfilled") {
      warnings.push("News provider unavailable; sentiment score used fallback values.");
    }

    res.json({
      ok: true,
      query,
      source: "online+manual+news+ohlc",
      score,
      summary,
      forecast,
      news,
      warnings
    });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default decisionRouter;
